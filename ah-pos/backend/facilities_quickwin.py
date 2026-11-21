"""
AH-POS Government Quick-Win Scanner (IT + Facilities)
=====================================================

Implements the "facilities support contractor" play:
  - Target small, fast, simplified-acquisition awards (roughly $15K-$350K under
    FAR thresholds effective 2025-10-01: MPT $15,000, SAT $350,000).
  - Stack several ~$25K wins (4 x $25K = $100K) instead of chasing one big contract.
  - Win on response time and price: surface quick-turn RFQs in the target state,
    small-business set-asides first, and learn which offices repeatedly buy.

Data source: SAM.gov Get Opportunities Public API v2
  https://api.sam.gov/opportunities/v2/search
  Required: api_key, postedFrom, postedTo (MM/dd/yyyy, <= 1 year apart).

Public API keys have a tight daily request quota, so this scanner pulls broad
pages (no per-NAICS fan-out) and filters client-side. Every run is bounded by
--max-calls.

Env:
  SAM_GOV_API_KEY      required (SAM.gov -> Account Details -> Public API Key)
  AH_POS_STATES        place-of-performance states, default "AZ"
  AH_POS_CERTS         socio-economic certs actually held, comma list of SAM
                       set-aside codes (e.g. "SDVOSBC,WOSB"). Default empty:
                       only open small-business (SBA/SBP) and unrestricted
                       notices are treated as biddable.
  TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID   optional digest delivery
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

import requests

logger = logging.getLogger("facilities_quickwin")

SAM_SEARCH_URL = "https://api.sam.gov/opportunities/v2/search"

# FAR 2.101 thresholds effective 2025-10-01
MICRO_PURCHASE_THRESHOLD = 15_000
SIMPLIFIED_ACQUISITION_THRESHOLD = 350_000

CAPABILITIES_PATH = Path(__file__).resolve().parents[1] / "config" / "capabilities.json"


def load_capabilities(path: Path = CAPABILITIES_PATH) -> dict:
    """NAICS -> {lane, delivery, desc} plus per-lane keywords. Mirrors alreadyherellc.com."""
    cfg = json.loads(Path(path).read_text())
    naics = {n["code"]: {"lane": n["lane"], "delivery": n["delivery"], "desc": n["desc"]}
             for n in cfg["naics"]}
    keywords = {lane: tuple(v["keywords"]) for lane, v in cfg["lanes"].items()}
    labels = {lane: v["label"] for lane, v in cfg["lanes"].items()}
    return {"naics": naics, "keywords": keywords, "labels": labels}


CAPABILITIES = load_capabilities()
NAICS_MAP = CAPABILITIES["naics"]

# SAM ptype codes
PTYPE_LABELS = {
    "k": "Combined Synopsis/Solicitation",
    "o": "Solicitation",
    "p": "Presolicitation",
    "r": "Sources Sought",
    "a": "Award Notice",
}

OPEN_SMALL_BUSINESS = {"SBA", "SBP"}
RESTRICTED_SET_ASIDES = {
    "8A", "8AN", "HZC", "HZS", "SDVOSBC", "SDVOSBS", "WOSB", "WOSBSS",
    "EDWOSB", "EDWOSBSS", "VSA", "VSS", "ISBEE", "IEE", "BICiv",
}


# --------------------------------------------------------------------------- #
# SAM.gov client
# --------------------------------------------------------------------------- #
class QuotaExhausted(RuntimeError):
    pass


class SamClient:
    def __init__(self, api_key: str, max_calls: int = 6, timeout: int = 60,
                 session: Optional[requests.Session] = None):
        if not api_key:
            raise ValueError("SAM_GOV_API_KEY is not configured")
        self.api_key = api_key
        self.max_calls = max_calls
        self.calls = 0
        self.timeout = timeout
        self.http = session or requests.Session()

    @staticmethod
    def fmt(d: date) -> str:
        return d.strftime("%m/%d/%Y")

    def search(self, posted_from: date, posted_to: date, ptypes: Iterable[str],
               ncode: Optional[str] = None, state: Optional[str] = None,
               page_size: int = 1000) -> list[dict]:
        """Page through results until exhausted or the call budget is spent."""
        if (posted_to - posted_from).days > 364:
            raise ValueError("postedFrom/postedTo must be within one year")
        rows: list[dict] = []
        offset = 0
        while True:
            if self.calls >= self.max_calls:
                logger.warning("Call budget (%s) reached; stopping pagination", self.max_calls)
                break
            params = {
                "api_key": self.api_key,
                "postedFrom": self.fmt(posted_from),
                "postedTo": self.fmt(posted_to),
                "ptype": ",".join(ptypes),
                "limit": page_size,
                "offset": offset,
            }
            if ncode:
                params["ncode"] = ncode
            if state:
                params["state"] = state
            self.calls += 1
            resp = self.http.get(SAM_SEARCH_URL, params=params, timeout=self.timeout)
            if resp.status_code == 429:
                raise QuotaExhausted("SAM.gov daily API quota exhausted (HTTP 429)")
            if resp.status_code in (401, 403):
                raise PermissionError(f"SAM.gov rejected the API key (HTTP {resp.status_code})")
            resp.raise_for_status()
            payload = resp.json()
            batch = payload.get("opportunitiesData") or []
            rows.extend(batch)
            total = int(payload.get("totalRecords") or 0)
            offset += page_size
            if not batch or offset >= total:
                break
        return rows


# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #
def _parse_date(value) -> Optional[date]:
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _money(value) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except ValueError:
        return None


def _ptype_code(raw_type: str) -> str:
    t = (raw_type or "").lower()
    if "combined" in t:
        return "k"
    if "sources sought" in t:
        return "r"
    if "presolicitation" in t:
        return "p"
    if "award" in t:
        return "a"
    if "solicitation" in t:
        return "o"
    return "?"


def normalize(opp: dict) -> dict:
    pop = opp.get("placeOfPerformance") or {}
    state = ((pop.get("state") or {}).get("code") or "").upper()
    city = (pop.get("city") or {}).get("name") or ""
    award = opp.get("award") or {}
    awardee = award.get("awardee") or {}
    contacts = opp.get("pointOfContact") or []
    primary = next((c for c in contacts if (c.get("type") or "").lower() == "primary"),
                   contacts[0] if contacts else {})
    path = opp.get("fullParentPathName") or ""
    parts = [p.strip() for p in path.split(".") if p.strip()]
    notice_id = opp.get("noticeId") or ""
    return {
        "notice_id": notice_id,
        "solicitation_number": opp.get("solicitationNumber") or "",
        "title": (opp.get("title") or "").strip(),
        "ptype": _ptype_code(opp.get("type") or opp.get("baseType") or ""),
        "notice_type": opp.get("type") or "",
        "naics": (opp.get("naicsCode") or "").strip(),
        "psc": opp.get("classificationCode") or "",
        "set_aside_code": (opp.get("typeOfSetAside") or "").strip(),
        "set_aside": opp.get("typeOfSetAsideDescription") or "",
        "agency": parts[0] if parts else "",
        "office": parts[-1] if parts else "",
        "office_path": path,
        "posted": _parse_date(opp.get("postedDate")),
        "deadline": _parse_date(opp.get("responseDeadLine")),
        "pop_state": state,
        "pop_city": city,
        "award_amount": _money(award.get("amount")),
        "award_date": _parse_date(award.get("date")),
        "awardee": awardee.get("name") or "",
        "contact_name": primary.get("fullName") or "",
        "contact_email": primary.get("email") or "",
        "contact_phone": primary.get("phone") or "",
        "url": opp.get("uiLink") or (f"https://sam.gov/opp/{notice_id}/view" if notice_id else ""),
        "active": str(opp.get("active", "Yes")).lower() in ("yes", "true", "1"),
    }


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
@dataclass
class ScoredOpportunity:
    opp: dict
    score: int
    biddable: bool
    reasons: list[str] = field(default_factory=list)
    days_left: Optional[int] = None


def eligibility(set_aside_code: str, certs: set[str]) -> tuple[bool, str]:
    code = (set_aside_code or "").upper()
    if not code or code == "NONE":
        return True, "unrestricted"
    if code in OPEN_SMALL_BUSINESS:
        return True, "small-business set-aside"
    if code in certs:
        return True, f"{code} set-aside (cert held)"
    if code in RESTRICTED_SET_ASIDES:
        return False, f"{code} set-aside requires a certification not held"
    return True, f"set-aside {code}"


def score(opp: dict, states: set[str], certs: set[str], today: Optional[date] = None) -> ScoredOpportunity:
    today = today or date.today()
    reasons: list[str] = []
    pts = 0

    naics = opp["naics"]
    cap = NAICS_MAP.get(naics)
    if not cap:
        return ScoredOpportunity(opp, 0, False, ["NAICS out of scope"])
    opp["lane"] = cap["lane"]
    opp["delivery"] = cap["delivery"]
    if cap["delivery"] == "self":
        pts += 30
        reasons.append(f"{cap['lane'].upper()} NAICS {naics} (self-perform)")
    else:
        pts += 20
        reasons.append(f"{cap['lane'].upper()} NAICS {naics} (needs teaming partner)")

    ok, why = eligibility(opp["set_aside_code"], certs)
    if not ok:
        return ScoredOpportunity(opp, 0, False, [why])
    pts += 20 if opp["set_aside_code"].upper() in OPEN_SMALL_BUSINESS else 10
    reasons.append(why)

    if opp["pop_state"] and opp["pop_state"] in states:
        pts += 20
        reasons.append(f"on-site in {opp['pop_state']}")
    elif opp["pop_state"]:
        return ScoredOpportunity(opp, 0, False, [f"place of performance {opp['pop_state']} outside dispatch area"])

    pts += {"k": 15, "o": 12, "r": 10, "p": 8}.get(opp["ptype"], 0)
    reasons.append(PTYPE_LABELS.get(opp["ptype"], opp["notice_type"] or "notice"))

    days_left = None
    if opp["deadline"]:
        days_left = (opp["deadline"] - today).days
        if days_left < 2:
            return ScoredOpportunity(opp, 0, False, ["closes in under 2 days"], days_left)
        if days_left <= 4:
            pts += 5
            reasons.append(f"fast-turn: {days_left}d left")
        elif days_left <= 21:
            pts += 15
            reasons.append(f"{days_left}d to respond")
        else:
            pts += 10
            reasons.append(f"{days_left}d to respond")

    title = opp["title"].lower()
    hits = [k.strip() for k in CAPABILITIES["keywords"].get(cap["lane"], ()) if k in title]
    if hits:
        pts += min(10, 4 * len(hits))
        reasons.append("fits: " + ", ".join(hits[:3]))

    return ScoredOpportunity(opp, min(100, pts), True, reasons, days_left)


# --------------------------------------------------------------------------- #
# Award intelligence: who repeatedly buys small facilities work?
# --------------------------------------------------------------------------- #
def repeat_buyers(awards: list[dict], states: set[str],
                  low: float = 10_000, high: float = SIMPLIFIED_ACQUISITION_THRESHOLD) -> list[dict]:
    buckets: dict[str, dict] = {}
    for a in awards:
        amt = a.get("award_amount")
        if amt is None or not (low <= amt <= high):
            continue
        if a["naics"] not in NAICS_MAP:
            continue
        if states and a["pop_state"] and a["pop_state"] not in states:
            continue
        key = a["office_path"] or a["office"]
        b = buckets.setdefault(key, {"office": a["office"], "agency": a["agency"], "awards": 0,
                                     "total": 0.0, "naics": set(), "awardees": set()})
        b["awards"] += 1
        b["total"] += amt
        b["naics"].add(a["naics"])
        if a["awardee"]:
            b["awardees"].add(a["awardee"])
    out = []
    for b in buckets.values():
        out.append({
            "office": b["office"],
            "agency": b["agency"],
            "awards": b["awards"],
            "avg_award": round(b["total"] / b["awards"], 2),
            "total": round(b["total"], 2),
            "naics": sorted(b["naics"]),
            "incumbents": sorted(b["awardees"])[:5],
        })
    return sorted(out, key=lambda r: (r["awards"], r["total"]), reverse=True)


# --------------------------------------------------------------------------- #
# Goal math: 4 x $25K = $100K
# --------------------------------------------------------------------------- #
def pipeline_plan(revenue_goal: float, avg_award: float, win_rate: float) -> dict:
    wins = math.ceil(revenue_goal / avg_award)
    bids = math.ceil(wins / win_rate) if win_rate > 0 else None
    return {"revenue_goal": revenue_goal, "avg_award": avg_award, "win_rate": win_rate,
            "wins_needed": wins, "bids_needed": bids}


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def _json_default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(type(o))


def _digest_item(i: int, s: ScoredOpportunity) -> list[str]:
    o = s.opp
    dl = o["deadline"].isoformat() if o["deadline"] else "n/a"
    return [f"{i}. [{s.score}] {o['title'][:90]}",
            f"   {o['office'] or o['agency']} | {o['pop_city']} {o['pop_state']} | "
            f"NAICS {o['naics']} | due {dl}",
            f"   {'; '.join(s.reasons)}",
            f"   {o['url']}"]


def render_digest(ranked: list[ScoredOpportunity], buyers: list[dict], plan: dict,
                  states: set[str], top: int = 6) -> str:
    lines = [f"AH-POS Government Quick-Win Scan — {date.today().isoformat()}",
             f"Dispatch area: {', '.join(sorted(states))} | biddable: {len(ranked)}",
             f"Goal ${plan['revenue_goal']:,.0f} = {plan['wins_needed']} wins x "
             f"${plan['avg_award']:,.0f} -> ~{plan['bids_needed']} bids at "
             f"{plan['win_rate']:.0%} win rate"]
    if not ranked:
        lines += ["", "No biddable opportunities in this window."]
    for lane, label in CAPABILITIES["labels"].items():
        items = [s for s in ranked if s.opp.get("lane") == lane]
        if not items:
            continue
        lines += ["", f"{label} ({len(items)}):"]
        for i, s in enumerate(items[:top], 1):
            lines += _digest_item(i, s)
    if buyers:
        lines += ["", "Repeat small-award buyers (target for capability statements):"]
        for b in buyers[:5]:
            lines.append(f"- {b['office']} ({b['agency']}): {b['awards']} awards, "
                         f"avg ${b['avg_award']:,.0f}, NAICS {', '.join(b['naics'])}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# alreadyherellc.com revenue-command intake (Procurement lane, owner-approval gated)
# --------------------------------------------------------------------------- #
SITE_INTAKE_URL = "https://www.alreadyherellc.com/api/revenue-command-spine/intake"
SITE_INTAKE_MAX = 8  # endpoint allows 10 requests/minute per client


def intake_payload(s: ScoredOpportunity) -> dict:
    o = s.opp
    dl = o["deadline"].isoformat() if o["deadline"] else "not stated"
    body = "\n".join([
        f"SAM.gov {o['notice_type'] or 'notice'} | solicitation {o['solicitation_number'] or 'n/a'}",
        f"Lane: {o.get('lane', '')} | delivery: {o.get('delivery', '')} | score {s.score}",
        f"NAICS {o['naics']} | set-aside: {o['set_aside'] or 'none'} | response due {dl}",
        f"Place of performance: {o['pop_city']} {o['pop_state']}",
        f"Contracting contact: {o['contact_name'] or 'see notice'}",
        f"Why: {'; '.join(s.reasons)}",
        o["url"],
        "Bid/no-bid decision and any submission require owner approval.",
    ])
    return {
        "source": "sam_gov",
        "sourceId": o["notice_id"],
        "channel": "web",
        "fullName": o["contact_name"] or "Contracting Officer",
        "company": o["office"] or o["agency"] or "Federal agency",
        "domain": (o["contact_email"].split("@", 1)[1] if "@" in o["contact_email"] else ""),
        "email": o["contact_email"],
        "phone": o["contact_phone"],
        "title": f"Government RFQ: {o['title']}"[:240],
        "body": body[:4000],
        "location": ", ".join(x for x in (o["pop_city"], o["pop_state"]) if x),
        "serviceType": f"Federal {o.get('lane', '')} solicitation".strip(),
        "ticketNumber": o["solicitation_number"],
        "requestedWindow": f"respond by {dl}",
        "estimatedValueCents": 0,
        # Stable timestamp keeps the site's canonical intake id identical across daily runs.
        "submittedAt": (o["posted"].isoformat() + "T00:00:00.000Z") if o["posted"] else None,
    }


def push_to_site(ranked: list[ScoredOpportunity], url: str = SITE_INTAKE_URL,
                 limit: int = SITE_INTAKE_MAX, min_score: int = 70,
                 http: Optional[requests.Session] = None) -> dict:
    http = http or requests.Session()
    sent, failed = 0, []
    for s in [r for r in ranked if r.score >= min_score][:limit]:
        payload = {k: v for k, v in intake_payload(s).items() if v not in (None, "")}
        try:
            r = http.post(url, json=payload, timeout=20,
                          headers={"User-Agent": "Mozilla/5.0 (AH-POS scanner)"})
            if r.status_code == 200:
                sent += 1
            else:
                failed.append({"notice_id": s.opp["notice_id"], "status": r.status_code})
        except requests.RequestException as exc:
            failed.append({"notice_id": s.opp["notice_id"], "error": str(exc)[:200]})
    return {"sent": sent, "failed": failed}


def send_telegram(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        return False
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)]
    for chunk in chunks:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": chunk, "disable_web_page_preview": True},
                          timeout=30)
        r.raise_for_status()
    return True


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run(client: SamClient, states: set[str], certs: set[str], days_back: int,
        award_days: int, goal: float, avg_award: float, win_rate: float,
        out_dir: Path, today: Optional[date] = None) -> dict:
    today = today or date.today()
    raw_open = client.search(today - timedelta(days=days_back), today, ptypes=["k", "o", "r", "p"])
    opps = [normalize(o) for o in raw_open]
    opps = [o for o in opps if o["active"]]
    scored = [score(o, states, certs, today) for o in opps]
    ranked = sorted((s for s in scored if s.biddable and s.score > 0),
                    key=lambda s: s.score, reverse=True)

    buyers: list[dict] = []
    if award_days > 0:
        try:
            # Award notices: one call per core NAICS would burn quota; pull state-scoped pages instead.
            raw_awards: list[dict] = []
            for st in sorted(states):
                raw_awards += client.search(today - timedelta(days=award_days), today,
                                            ptypes=["a"], state=st)
            buyers = repeat_buyers([normalize(a) for a in raw_awards], states)
        except QuotaExhausted as exc:
            logger.warning("Skipping award intel: %s", exc)

    plan = pipeline_plan(goal, avg_award, win_rate)
    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "states": sorted(states),
        "api_calls": client.calls,
        "scanned": len(opps),
        "plan": plan,
        "opportunities": [{**s.opp, "score": s.score, "reasons": s.reasons, "days_left": s.days_left}
                          for s in ranked],
        "repeat_buyers": buyers,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "facilities_scan.json").write_text(json.dumps(result, indent=2, default=_json_default))
    digest = render_digest(ranked, buyers, plan, states)
    (out_dir / "facilities_digest.txt").write_text(digest)
    result["digest"] = digest
    return result


def _csv_set(value: str) -> set[str]:
    return {v.strip().upper() for v in (value or "").split(",") if v.strip()}


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--days-back", type=int, default=3)
    p.add_argument("--award-days", type=int, default=90, help="0 disables award intel")
    p.add_argument("--goal", type=float, default=100_000)
    p.add_argument("--avg-award", type=float, default=25_000)
    p.add_argument("--win-rate", type=float, default=0.20)
    p.add_argument("--max-calls", type=int, default=int(os.getenv("SAM_MAX_CALLS", "6")))
    p.add_argument("--out", default=os.getenv("AH_POS_OUT_DIR", "facilities_out"))
    p.add_argument("--notify", action="store_true", help="send digest to Telegram")
    p.add_argument("--push-intake", action="store_true",
                   help="post score>=70 items to alreadyherellc.com Procurement intake")
    args = p.parse_args(argv)

    key = os.getenv("SAM_GOV_API_KEY", "").strip()
    if not key:
        print("BLOCKED — SAM_GOV_API_KEY missing. Get it at SAM.gov > Account Details > Public API Key.",
              file=sys.stderr)
        return 2
    states = _csv_set(os.getenv("AH_POS_STATES", "AZ")) or {"AZ"}
    certs = _csv_set(os.getenv("AH_POS_CERTS", ""))

    client = SamClient(key, max_calls=args.max_calls)
    try:
        result = run(client, states, certs, args.days_back, args.award_days,
                     args.goal, args.avg_award, args.win_rate, Path(args.out))
    except QuotaExhausted as exc:
        print(f"BLOCKED — {exc}", file=sys.stderr)
        return 3
    except PermissionError as exc:
        print(f"BLOCKED — {exc}", file=sys.stderr)
        return 2
    print(result["digest"])
    if args.push_intake:
        ranked = [ScoredOpportunity(o, o["score"], True, o["reasons"], o["days_left"])
                  for o in result["opportunities"]]
        pushed = push_to_site(ranked, os.getenv("AH_SITE_INTAKE_URL", SITE_INTAKE_URL))
        print(f"Site intake: {pushed['sent']} sent, {len(pushed['failed'])} failed")
        if pushed["failed"]:
            logger.warning("Site intake failures: %s", pushed["failed"])
    if args.notify and send_telegram(result["digest"]):
        logger.info("Digest sent to Telegram")
    return 0


if __name__ == "__main__":
    sys.exit(main())

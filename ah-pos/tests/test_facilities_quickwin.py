"""Offline tests for the facilities quick-win scanner (no network)."""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import facilities_quickwin as fq  # noqa: E402

TODAY = date(2026, 10, 29)


def sam_row(**over):
    row = {
        "noticeId": "a1b2c3d4e5f6",
        "title": "HVAC Preventive Maintenance - Phoenix VA Medical Center",
        "solicitationNumber": "36C26227Q0001",
        "fullParentPathName": "VETERANS AFFAIRS, DEPARTMENT OF.VETERANS AFFAIRS, DEPARTMENT OF.262-NETWORK CONTRACT OFFICE 22",
        "postedDate": "2026-10-27",
        "type": "Combined Synopsis/Solicitation",
        "typeOfSetAside": "SBA",
        "typeOfSetAsideDescription": "Total Small Business Set-Aside (FAR 19.5)",
        "responseDeadLine": "2026-11-12T14:00:00-07:00",
        "naicsCode": "238220",
        "classificationCode": "J041",
        "active": "Yes",
        "placeOfPerformance": {"city": {"name": "Phoenix"}, "state": {"code": "AZ"}},
        "pointOfContact": [{"type": "primary", "fullName": "Contracting Officer"}],
        "uiLink": "https://sam.gov/opp/a1b2c3d4e5f6/view",
    }
    row.update(over)
    return row


def test_normalize_maps_v2_fields():
    o = fq.normalize(sam_row())
    assert o["ptype"] == "k"
    assert o["naics"] == "238220"
    assert o["pop_state"] == "AZ"
    assert o["deadline"] == date(2026, 11, 12)
    assert o["office"] == "262-NETWORK CONTRACT OFFICE 22"
    assert o["url"].endswith("/view")


def test_core_small_business_in_state_scores_high():
    s = fq.score(fq.normalize(sam_row()), {"AZ"}, set(), TODAY)
    assert s.biddable
    assert s.score >= 90


def test_restricted_set_aside_excluded_without_cert():
    o = fq.normalize(sam_row(typeOfSetAside="SDVOSBC"))
    assert not fq.score(o, {"AZ"}, set(), TODAY).biddable
    assert fq.score(o, {"AZ"}, {"SDVOSBC"}, TODAY).biddable


def test_out_of_area_and_out_of_scope_excluded():
    far = fq.normalize(sam_row(placeOfPerformance={"state": {"code": "ME"}}))
    assert not fq.score(far, {"AZ"}, set(), TODAY).biddable
    offscope = fq.normalize(sam_row(naicsCode="325412"))
    assert not fq.score(offscope, {"AZ"}, set(), TODAY).biddable


def test_closing_too_soon_excluded():
    o = fq.normalize(sam_row(responseDeadLine="2026-10-30T10:00:00-07:00"))
    assert not fq.score(o, {"AZ"}, set(), TODAY).biddable


def test_repeat_buyers_keeps_small_awards_only():
    base = dict(type="Award Notice", naicsCode="561720")
    awards = [
        fq.normalize(sam_row(**base, award={"amount": "24,500.00", "awardee": {"name": "Desert Clean LLC"}})),
        fq.normalize(sam_row(**base, award={"amount": "31000", "awardee": {"name": "Sonoran FM Inc"}})),
        fq.normalize(sam_row(**base, award={"amount": "4200000"})),
    ]
    buyers = fq.repeat_buyers(awards, {"AZ"})
    assert len(buyers) == 1
    assert buyers[0]["awards"] == 2
    assert buyers[0]["avg_award"] == pytest.approx(27750.0)


def test_pipeline_plan_four_by_25k():
    plan = fq.pipeline_plan(100_000, 25_000, 0.20)
    assert plan["wins_needed"] == 4
    assert plan["bids_needed"] == 20


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        return self._p

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class _Http:
    def __init__(self, pages):
        self.pages, self.params = list(pages), []

    def get(self, url, params, timeout):
        assert url == fq.SAM_SEARCH_URL
        self.params.append(params)
        return self.pages.pop(0)


def test_client_uses_v2_params_and_respects_budget():
    http = _Http([_Resp({"totalRecords": 3, "opportunitiesData": [sam_row(), sam_row()]}),
                  _Resp({"totalRecords": 3, "opportunitiesData": [sam_row()]})])
    c = fq.SamClient("k", max_calls=1, session=http)
    rows = c.search(date(2026, 10, 26), TODAY, ["k", "o"], page_size=2)
    assert len(rows) == 2 and c.calls == 1
    p = http.params[0]
    assert p["postedFrom"] == "10/26/2026" and p["postedTo"] == "10/29/2026"
    assert p["ptype"] == "k,o" and p["api_key"] == "k"


def test_client_raises_on_quota():
    c = fq.SamClient("k", session=_Http([_Resp({}, 429)]))
    with pytest.raises(fq.QuotaExhausted):
        c.search(date(2026, 10, 26), TODAY, ["k"])


def test_run_writes_outputs(tmp_path):
    http = _Http([_Resp({"totalRecords": 1, "opportunitiesData": [sam_row()]})])
    c = fq.SamClient("k", session=http)
    r = fq.run(c, {"AZ"}, set(), 3, 0, 100_000, 25_000, 0.2, tmp_path, TODAY)
    assert len(r["opportunities"]) == 1
    assert (tmp_path / "facilities_scan.json").exists()
    assert "4 wins" in r["digest"]

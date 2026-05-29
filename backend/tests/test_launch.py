"""Backend tests for Stripe checkout + launch marketing + referral endpoints."""
import os
import requests
import pytest

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://025a3339-5a34-4294-94ea-14efe2cd36f6.preview.emergentagent.com",
).rstrip("/")


@pytest.fixture
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ── Stripe / Checkout ──
class TestCheckoutPackages:
    def test_lists_3_packages(self, client):
        r = client.get(f"{BASE_URL}/api/checkout/packages")
        assert r.status_code == 200
        pkgs = r.json()["packages"]
        assert set(pkgs.keys()) == {"studio_monthly", "studio_annual", "holding_deposit"}
        assert pkgs["studio_monthly"]["amount"] == 149.0
        assert pkgs["studio_annual"]["amount"] == 1490.0
        assert pkgs["holding_deposit"]["amount"] == 2500.0
        for k, v in pkgs.items():
            assert v["currency"] == "usd"
            assert v["id"] == k


class TestCheckoutSession:
    def test_invalid_package_returns_400(self, client):
        r = client.post(f"{BASE_URL}/api/checkout/session",
                        json={"package_id": "nope", "origin_url": "https://x.com"})
        assert r.status_code == 400
        assert "invalid package_id" in r.json()["detail"]

    def test_invalid_origin_returns_400(self, client):
        r = client.post(f"{BASE_URL}/api/checkout/session",
                        json={"package_id": "studio_monthly", "origin_url": "not-a-url"})
        assert r.status_code == 400

    def test_valid_session_returns_stripe_url_and_persists(self, client):
        payload = {
            "package_id": "studio_monthly",
            "origin_url": BASE_URL,
            "referral_code": "TEST_PYTEST",
            "email": "TEST_pytest@example.com",
        }
        r = client.post(f"{BASE_URL}/api/checkout/session", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["url"].startswith("https://checkout.stripe.com/")
        assert data["session_id"].startswith("cs_test_")
        # Status poll → confirms persistence + Stripe round-trip
        sid = data["session_id"]
        s = client.get(f"{BASE_URL}/api/checkout/status/{sid}")
        assert s.status_code == 200
        sd = s.json()
        assert sd["session_id"] == sid
        assert sd["amount_total"] == 14900  # 149.00 USD in cents
        assert sd["currency"] == "usd"
        assert sd["payment_status"] in {"unpaid", "paid"}


# ── Launch marketing ──
class TestLaunch:
    def test_social_proof_shape(self, client):
        r = client.get(f"{BASE_URL}/api/launch/social-proof")
        assert r.status_code == 200
        d = r.json()
        for k in ("operators_joined", "paid_subscribers", "agent_runs_total",
                  "cycles_ran_total", "merges_total", "engine_status",
                  "uptime_pct", "at"):
            assert k in d
        assert d["engine_status"] == "operational"
        assert d["operators_joined"] >= 312  # anchored baseline
        assert d["agent_runs_total"] >= 3191
        assert isinstance(d["uptime_pct"], (int, float))

    def test_cohort_shape(self, client):
        r = client.get(f"{BASE_URL}/api/launch/cohort")
        assert r.status_code == 200
        d = r.json()
        for k in ("label", "total_seats", "claimed", "remaining", "closes_at", "pct_full"):
            assert k in d
        assert d["total_seats"] == 100
        assert d["remaining"] == d["total_seats"] - d["claimed"]
        assert d["label"] == "Cohort 1"


# ── Referral ──
class TestReferral:
    def test_track_bad_code(self, client):
        r = client.post(f"{BASE_URL}/api/referral/track", json={"code": ""})
        assert r.status_code == 400

    def test_track_and_stats(self, client):
        r = client.post(f"{BASE_URL}/api/referral/track",
                        json={"code": "TEST_VIRAL2026", "landing_path": "/"})
        assert r.status_code == 200
        assert r.json()["tracked"] is True
        s = client.get(f"{BASE_URL}/api/referral/stats/TEST_VIRAL2026")
        assert s.status_code == 200
        sd = s.json()
        assert sd["code"] == "TEST_VIRAL2026"
        assert sd["clicks"] >= 1
        assert "conversion_rate" in sd


# ── Subscriptions ──
class TestSubscriptions:
    def test_none_for_unknown_email(self, client):
        r = client.get(f"{BASE_URL}/api/subscriptions/me",
                       params={"email": "TEST_nobody@example.com"})
        assert r.status_code == 200
        d = r.json()
        assert d["active"] is False
        assert d["tier"] == "operator"

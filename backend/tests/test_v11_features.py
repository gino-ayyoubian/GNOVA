"""
GNOVA v1.1 Feature Tests
Covers: live rates, ZarinPal (mock fallback), KYC submit/status/auto-approve,
OTP request/verify, analytics summary, alerts DELETE.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://objective-jackson-13.preview.emergentagent.com",
).rstrip("/")

TEST_TELEGRAM_ID = 999888777


@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def auth_headers(api):
    r = api.post(f"{BASE_URL}/api/auth/login", json={"telegram_id": TEST_TELEGRAM_ID})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============ Live Rates ============
class TestLiveRates:
    def test_get_all_rates(self, api):
        r = api.get(f"{BASE_URL}/api/rates")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "rates" in d
        assert "updated_at" in d
        assert isinstance(d["rates"], dict)
        # At least one rate should be present (fallback or live)
        assert len(d["rates"]) >= 1

    def test_specific_rate_usdt_irr(self, api):
        r = api.get(f"{BASE_URL}/api/rates/USDT/IRR")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["from"] == "USDT"
        assert d["to"] == "IRR"
        assert isinstance(d["rate"], (int, float))
        assert d["rate"] > 0

    def test_specific_rate_lowercase_input(self, api):
        r = api.get(f"{BASE_URL}/api/rates/usdt/irr")
        assert r.status_code == 200
        d = r.json()
        assert d["from"] == "USDT"
        assert d["to"] == "IRR"


# ============ ZarinPal ============
class TestZarinPal:
    def test_status(self, api):
        r = api.get(f"{BASE_URL}/api/payment/zarinpal/status")
        assert r.status_code == 200
        d = r.json()
        assert "configured" in d
        assert "sandbox" in d
        # In this environment MERCHANT_ID is empty -> not configured
        assert d["configured"] is False

    def test_request_falls_back_to_mock(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/payment/zarinpal/request",
            headers=auth_headers,
            json={"amount_irr": 50000},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True
        # When merchant id empty should fall back to mock mode
        assert d.get("mode") == "mock"
        assert "payment_url" in d
        assert "deposit_id" in d

    def test_request_requires_auth(self, api):
        r = api.post(
            f"{BASE_URL}/api/payment/zarinpal/request",
            json={"amount_irr": 50000},
        )
        assert r.status_code == 401


# ============ KYC ============
class TestKYC:
    def test_submit_kyc(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/kyc/submit",
            headers=auth_headers,
            json={
                "full_name": "TEST User",
                "national_id": "0012345678",
                "birth_date": "1990-01-01",
                "address": "Tehran, Test St.",
                "phone": "+989121234567",
            },
        )
        # Should succeed; if user was previously approved some implementations
        # might reject re-submission - accept both 200 and 400 but log
        assert r.status_code in (200, 400), r.text
        if r.status_code == 200:
            d = r.json()
            assert d.get("ok") is True or d.get("success") is True

    def test_status(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/kyc/status", headers=auth_headers)
        assert r.status_code == 200
        d = r.json()
        assert "kyc_status" in d
        assert d["kyc_status"] in ("pending", "submitted", "approved", "rejected")

    def test_auto_approve(self, api, auth_headers):
        r = api.post(f"{BASE_URL}/api/kyc/auto-approve", headers=auth_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True or d.get("success") is True

        # Verify status is now approved
        rs = api.get(f"{BASE_URL}/api/kyc/status", headers=auth_headers)
        assert rs.status_code == 200
        assert rs.json()["kyc_status"] == "approved"


# ============ OTP / 2FA ============
class TestOTP:
    def test_request_otp(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/otp/request",
            headers=auth_headers,
            json={"purpose": "withdrawal"},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True
        assert "sent_via_telegram" in d
        assert "expires_at" in d
        assert isinstance(d.get("expires_in_seconds"), int)

    def test_verify_wrong_code(self, api, auth_headers):
        # Request OTP first
        api.post(
            f"{BASE_URL}/api/otp/request",
            headers=auth_headers,
            json={"purpose": "withdrawal"},
        )
        # Verify with wrong code
        r = api.post(
            f"{BASE_URL}/api/otp/verify",
            headers=auth_headers,
            json={"code": "000000", "purpose": "withdrawal"},
        )
        assert r.status_code == 400


# ============ Withdrawals after KYC ============
class TestWithdrawalsAfterKYC:
    def test_withdrawal_succeeds_after_kyc(self, api, auth_headers):
        # Ensure KYC approved
        api.post(f"{BASE_URL}/api/kyc/auto-approve", headers=auth_headers)
        r = api.post(
            f"{BASE_URL}/api/withdrawals",
            headers=auth_headers,
            json={
                "asset": "CREDIT",
                "amount_minor": 50000,
                "destination": "6037-XXXX-XXXX-1234",
                "destination_type": "card",
            },
        )
        # Should never be 403 (KYC) now
        assert r.status_code != 403, r.text
        # 200 if balance is enough, otherwise 400 insufficient funds
        assert r.status_code in (200, 400)
        if r.status_code == 200:
            d = r.json()
            assert d["success"] is True
            assert d["status"] == "pending"


# ============ Analytics ============
class TestAnalytics:
    def test_analytics_summary(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/analytics/summary", headers=auth_headers)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "this_month" in d
        assert "by_type" in d
        assert "daily_last_30_days" in d
        tm = d["this_month"]
        for k in ("total_deposits", "total_withdrawals", "net_flow", "total_transactions"):
            assert k in tm
        assert isinstance(d["by_type"], list)
        assert isinstance(d["daily_last_30_days"], list)

    def test_analytics_requires_auth(self, api):
        r = api.get(f"{BASE_URL}/api/analytics/summary")
        assert r.status_code == 401


# ============ Alerts CRUD with DELETE ============
class TestAlertsCRUD:
    def test_create_list_delete_alert(self, api, auth_headers):
        # Create
        r = api.post(
            f"{BASE_URL}/api/alerts/rate",
            headers=auth_headers,
            json={
                "from_asset": "USDT",
                "to_asset": "IRR",
                "target_rate": 64000.0,
                "condition": "below",
            },
        )
        assert r.status_code == 200, r.text
        alert_id = r.json()["alert_id"]

        # List - should include
        rl = api.get(f"{BASE_URL}/api/alerts", headers=auth_headers)
        assert rl.status_code == 200
        alerts = rl.json()["alerts"]
        assert any(a["id"] == alert_id for a in alerts)

        # Delete
        rd = api.delete(f"{BASE_URL}/api/alerts/{alert_id}", headers=auth_headers)
        assert rd.status_code == 200
        assert rd.json()["success"] is True

        # List - should no longer include
        rl2 = api.get(f"{BASE_URL}/api/alerts", headers=auth_headers)
        assert rl2.status_code == 200
        assert not any(a["id"] == alert_id for a in rl2.json()["alerts"])

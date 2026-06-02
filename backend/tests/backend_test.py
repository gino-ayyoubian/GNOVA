"""
GNOVA Fintech Platform - Backend API Tests
Covers: health, auth, wallets, deposits, webhooks (idempotency), conversions, withdrawals,
transactions, rate alerts.
"""
import os
import uuid
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://objective-jackson-13.preview.emergentagent.com").rstrip("/")

TEST_TELEGRAM_ID = 999888777
TEST_USER_ID = "d3cfeb71-7000-4ac3-b1f7-7763552d76d5"


@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def token(api):
    r = api.post(f"{BASE_URL}/api/auth/login", json={"telegram_id": TEST_TELEGRAM_ID})
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("success") is True
    assert isinstance(data.get("token"), str) and len(data["token"]) > 10
    return data["token"]


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ============ Health ============
class TestHealth:
    def test_health(self, api):
        r = api.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "healthy"
        assert "services" in d

    def test_root(self, api):
        r = api.get(f"{BASE_URL}/api/")
        assert r.status_code == 200
        assert r.json().get("status") == "operational"


# ============ Auth ============
class TestAuth:
    def test_login_existing_user(self, api):
        r = api.post(f"{BASE_URL}/api/auth/login", json={"telegram_id": TEST_TELEGRAM_ID})
        assert r.status_code == 200
        d = r.json()
        assert d["user_id"] == TEST_USER_ID
        assert "token" in d

    def test_login_unknown_user(self, api):
        # Random tg id that should not exist
        r = api.post(f"{BASE_URL}/api/auth/login", json={"telegram_id": 1})
        assert r.status_code in (401, 404)

    def test_register_new_user(self, api):
        new_tg = 700000000 + int(time.time()) % 100000000
        r = api.post(
            f"{BASE_URL}/api/auth/register",
            json={"telegram_id": new_tg, "username": f"TEST_user_{new_tg}"},
        )
        assert r.status_code in (200, 201), f"Register failed: {r.status_code} {r.text}"
        d = r.json()
        assert d.get("success") is True
        assert "user_id" in d and "token" in d

    def test_register_duplicate(self, api):
        r = api.post(
            f"{BASE_URL}/api/auth/register",
            json={"telegram_id": TEST_TELEGRAM_ID, "username": "test_user"},
        )
        # Should not allow duplicate
        assert r.status_code in (400, 409)

    def test_me_requires_auth(self, api):
        r = api.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_me_with_token(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        d = r.json()
        assert d["user_id"] == TEST_USER_ID
        assert d["telegram_id"] == TEST_TELEGRAM_ID
        assert "kyc_status" in d


# ============ Wallets ============
class TestWallets:
    def test_get_wallets(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/wallets", headers=auth_headers)
        assert r.status_code == 200
        d = r.json()
        assert d["user_id"] == TEST_USER_ID
        assert isinstance(d["balances"], list)
        assert len(d["balances"]) >= 1
        codes = {b["asset_code"] for b in d["balances"]}
        # Should include CREDIT
        assert "CREDIT" in codes
        for b in d["balances"]:
            assert "balance_minor" in b
            assert "balance_display" in b
            assert "decimal_precision" in b

    def test_wallets_requires_auth(self, api):
        r = api.get(f"{BASE_URL}/api/wallets")
        assert r.status_code == 401


# ============ Deposits ============
class TestDeposits:
    def test_initiate_deposit(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/deposits/initiate",
            headers=auth_headers,
            json={"amount_irr": 50000},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["amount_irr"] == 50000
        assert "deposit_id" in d
        assert "payment_url" in d

    def test_deposit_below_min(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/deposits/initiate",
            headers=auth_headers,
            json={"amount_irr": 5000},
        )
        assert r.status_code == 400

    def test_deposit_above_max(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/deposits/initiate",
            headers=auth_headers,
            json={"amount_irr": 200000000},
        )
        assert r.status_code == 400


# ============ Webhook idempotency ============
class TestWebhookIdempotency:
    def test_webhook_processes_and_idempotent(self, api, auth_headers):
        # Get balance before
        r0 = api.get(f"{BASE_URL}/api/wallets", headers=auth_headers)
        balances_before = {b["asset_code"]: b["balance_minor"] for b in r0.json()["balances"]}
        credit_before = balances_before.get("CREDIT", 0)

        txn_id = f"TEST_webhook_{uuid.uuid4().hex[:12]}"
        payload = {
            "transaction_id": txn_id,
            "paid_amount": 1000,
            "status": "success",
            "user_id": TEST_USER_ID,
            "metadata": {"source": "pytest"},
        }
        # First call - should credit
        r1 = api.post(f"{BASE_URL}/api/webhooks/payment", json=payload)
        assert r1.status_code == 200, r1.text
        assert r1.json().get("success") is True

        # Check balance after first call
        r1b = api.get(f"{BASE_URL}/api/wallets", headers=auth_headers)
        credit_after_first = next(
            (b["balance_minor"] for b in r1b.json()["balances"] if b["asset_code"] == "CREDIT"),
            0,
        )
        assert credit_after_first == credit_before + 1000, (
            f"Balance not credited: before={credit_before} after={credit_after_first}"
        )

        # Replay - should NOT double-credit
        r2 = api.post(f"{BASE_URL}/api/webhooks/payment", json=payload)
        assert r2.status_code == 200
        msg = r2.json().get("message", "").lower()
        assert "already" in msg or "processed" in msg

        r2b = api.get(f"{BASE_URL}/api/wallets", headers=auth_headers)
        credit_after_second = next(
            (b["balance_minor"] for b in r2b.json()["balances"] if b["asset_code"] == "CREDIT"),
            0,
        )
        assert credit_after_second == credit_after_first, (
            f"Double credit detected! after_first={credit_after_first} after_second={credit_after_second}"
        )


# ============ Conversions ============
class TestConversions:
    def test_conversion_quote_and_confirm(self, api, auth_headers):
        # Quote CREDIT -> USDT for 65000 CREDIT (~1 USDT in minor units)
        amount = 65000
        rq = api.post(
            f"{BASE_URL}/api/convert/quote",
            headers=auth_headers,
            json={"from_asset": "CREDIT", "to_asset": "USDT", "amount_minor": amount},
        )
        assert rq.status_code == 200, rq.text
        q = rq.json()
        assert "quote_id" in q
        assert q["from_asset"] == "CREDIT"
        assert q["to_asset"] == "USDT"
        assert q["amount_from"] == amount

        # Confirm conversion
        rc = api.post(
            f"{BASE_URL}/api/conversions/confirm",
            headers=auth_headers,
            json={"quote_id": q["quote_id"]},
        )
        assert rc.status_code == 200, rc.text
        d = rc.json()
        assert d["success"] is True
        assert "transaction_id" in d

    def test_conversion_invalid_pair(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/convert/quote",
            headers=auth_headers,
            json={"from_asset": "XXX", "to_asset": "YYY", "amount_minor": 1000},
        )
        assert r.status_code == 400

    def test_confirm_invalid_quote(self, api, auth_headers):
        r = api.post(
            f"{BASE_URL}/api/conversions/confirm",
            headers=auth_headers,
            json={"quote_id": "nonexistent-quote-id"},
        )
        assert r.status_code == 404


# ============ Withdrawals ============
class TestWithdrawals:
    def test_withdrawal_requires_kyc(self, api, auth_headers):
        # Test user has kyc_status='pending' - should be blocked
        r = api.post(
            f"{BASE_URL}/api/withdrawals",
            headers=auth_headers,
            json={
                "asset": "CREDIT",
                "amount_minor": 100000,
                "destination": "6037-XXXX-XXXX-1234",
                "destination_type": "card",
            },
        )
        assert r.status_code == 403
        assert "KYC" in r.json().get("detail", "")


# ============ Transactions ============
class TestTransactions:
    def test_get_transactions(self, api, auth_headers):
        r = api.get(f"{BASE_URL}/api/transactions?limit=10&offset=0", headers=auth_headers)
        assert r.status_code == 200
        d = r.json()
        assert "transactions" in d
        assert isinstance(d["transactions"], list)
        assert d["limit"] == 10
        assert d["offset"] == 0


# ============ Rate Alerts ============
class TestRateAlerts:
    def test_create_and_list_alerts(self, api, auth_headers):
        # Create alert
        r = api.post(
            f"{BASE_URL}/api/alerts/rate",
            headers=auth_headers,
            json={
                "from_asset": "USDT",
                "to_asset": "IRR",
                "target_rate": 70000.0,
                "condition": "above",
            },
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True
        assert "alert_id" in d
        alert_id = d["alert_id"]

        # List alerts
        rl = api.get(f"{BASE_URL}/api/alerts", headers=auth_headers)
        assert rl.status_code == 200
        alerts = rl.json().get("alerts", [])
        assert any(a["id"] == alert_id for a in alerts)

"""Deposit, PSP webhook and ZarinPal routes"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta
import os
import json
import uuid
import hmac
import hashlib

from models import DepositInitiateRequest, WebhookPayload, ZarinPalCallbackRequest
from deps import get_current_user
from database import get_db
from ledger_service import LedgerService
from zarinpal_service import ZarinPalService

router = APIRouter(tags=["deposits"])
zarinpal = ZarinPalService()


@router.post("/deposits/initiate")
async def initiate_deposit(
    request: DepositInitiateRequest,
    user: dict = Depends(get_current_user)
):
    """Initiate IRR deposit via payment gateway"""
    if request.amount_irr < 10000:
        raise HTTPException(status_code=400, detail="Minimum deposit is 10,000 IRR")
    if request.amount_irr > 100000000:
        raise HTTPException(status_code=400, detail="Maximum deposit is 100,000,000 IRR")

    deposit_id = str(uuid.uuid4())
    payment_url = f"{os.getenv('APP_URL')}/payment/{deposit_id}"

    return {
        "success": True,
        "deposit_id": deposit_id,
        "amount_irr": request.amount_irr,
        "payment_url": payment_url,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        "instructions": "برای تکمیل واریز، روی لینک پرداخت کلیک کنید و مراحل را دنبال کنید."
    }


async def _credit_deposit(db, payload: WebhookPayload) -> bool:
    """Credit user CREDIT account for a successful webhook. Returns True if credited."""
    credit_asset_id = os.getenv("CREDIT_ASSET_ID", "asset-credit-irr")
    cursor = await db.execute(
        "SELECT id FROM accounts WHERE user_id = ? AND asset_id = ?",
        (payload.user_id, credit_asset_id)
    )
    account = await cursor.fetchone()
    if not account:
        return False

    result = await LedgerService.credit_account(
        user_id=payload.user_id,
        account_id=account["id"],
        asset_id=credit_asset_id,
        amount_minor=payload.paid_amount,
        source_event="deposit_confirmed",
        source_ref=payload.transaction_id,
        metadata=payload.metadata
    )
    return result["ok"]


@router.post("/webhooks/payment")
async def payment_webhook(
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None)
):
    """Handle payment gateway webhook callbacks (HMAC enforced when secret configured)"""
    secret = os.getenv("PAYMENT_GATEWAY_SECRET", "")
    payload_str = json.dumps(payload.model_dump(), sort_keys=True)

    if secret:
        if not x_signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")
        expected_signature = hmac.new(
            secret.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(x_signature, expected_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, processed FROM webhook_events WHERE external_id = ?",
            (payload.transaction_id,)
        )
        existing = await cursor.fetchone()

        # Idempotency: only skip if fully processed
        if existing and existing["processed"]:
            return {"success": True, "message": "Already processed"}

        now = datetime.now(timezone.utc).isoformat()
        if not existing:
            await db.execute("""
                INSERT INTO webhook_events
                (id, provider, external_id, payload, signature_valid, processed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), "psp", payload.transaction_id,
                  json.dumps(payload.model_dump()), 1 if x_signature else 0, 0, now))
            await db.commit()

        if payload.status == "success":
            credited = await _credit_deposit(db, payload)
            if credited:
                await db.execute(
                    "UPDATE webhook_events SET processed = 1 WHERE external_id = ?",
                    (payload.transaction_id,)
                )
                await db.commit()
                return {"success": True, "message": "Payment processed"}

        return {"success": True, "message": "Webhook received"}
    finally:
        await db.close()


# ==================== ZarinPal ====================

@router.get("/payment/zarinpal/status")
async def zarinpal_status():
    return {
        "configured": zarinpal.is_configured(),
        "sandbox": zarinpal.sandbox,
        "message": "ZarinPal sandbox mode" if zarinpal.sandbox else "ZarinPal production mode"
    }


@router.post("/payment/zarinpal/request")
async def zarinpal_request(
    request: DepositInitiateRequest,
    user: dict = Depends(get_current_user)
):
    """Initiate ZarinPal payment request"""
    deposit_id = str(uuid.uuid4())

    result = await zarinpal.request_payment(
        amount_rial=request.amount_irr,
        deposit_id=deposit_id,
        user_email=user.get("email"),
        description=f"GNOVA Deposit for {user.get('username', 'user')}"
    )

    if not result["success"]:
        if result.get("fallback"):
            return {
                "success": True,
                "deposit_id": deposit_id,
                "amount_irr": request.amount_irr,
                "payment_url": None,
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
                "instructions": "زرین‌پال پیکربندی نشده است. این تراکنش آزمایشی است.",
                "mode": "mock"
            }
        raise HTTPException(status_code=400, detail=result.get("error"))

    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO webhook_events (id, provider, external_id, payload, signature_valid, processed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), "zarinpal", result["authority"],
            json.dumps({
                "user_id": user["id"],
                "amount_irr": request.amount_irr,
                "deposit_id": deposit_id,
                "status": "pending"
            }),
            1, 0, datetime.now(timezone.utc).isoformat()
        ))
        await db.commit()
    finally:
        await db.close()

    return {
        "success": True,
        "deposit_id": deposit_id,
        "authority": result["authority"],
        "amount_irr": request.amount_irr,
        "payment_url": result["payment_url"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        "mode": "sandbox" if zarinpal.sandbox else "production"
    }


@router.post("/payment/zarinpal/verify")
async def zarinpal_verify(request: ZarinPalCallbackRequest):
    """Verify ZarinPal payment after user returns from gateway"""
    if request.status != "OK":
        return {"success": False, "error": "Payment was cancelled"}

    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT * FROM webhook_events
            WHERE external_id = ? AND provider = 'zarinpal'
        """, (request.authority,))
        event = await cursor.fetchone()

        if not event:
            raise HTTPException(status_code=404, detail="Payment not found")
        if event["processed"]:
            return {"success": True, "message": "Already processed"}

        payload = json.loads(event["payload"])
        user_id = payload["user_id"]
        amount = payload["amount_irr"]

        verify_result = await zarinpal.verify_payment(request.authority, amount)
        if not verify_result["success"]:
            raise HTTPException(status_code=400, detail=verify_result.get("error", "Verification failed"))

        credit_asset_id = os.getenv("CREDIT_ASSET_ID", "asset-credit-irr")
        cursor = await db.execute(
            "SELECT id FROM accounts WHERE user_id=? AND asset_id=?",
            (user_id, credit_asset_id)
        )
        account = await cursor.fetchone()
        if not account:
            raise HTTPException(status_code=404, detail="User account not found")

        ref_id = str(verify_result.get("ref_id", request.authority))
        credit_result = await LedgerService.credit_account(
            user_id=user_id,
            account_id=account["id"],
            asset_id=credit_asset_id,
            amount_minor=amount,
            source_event="deposit_zarinpal",
            source_ref=f"zarinpal-{ref_id}",
            metadata={"authority": request.authority, "ref_id": ref_id, "card_pan": verify_result.get("card_pan")}
        )

        if credit_result["ok"]:
            await db.execute("UPDATE webhook_events SET processed=1 WHERE external_id=?", (request.authority,))
            await db.commit()
            return {"success": True, "ref_id": ref_id, "amount": amount, "message": "پرداخت با موفقیت تایید شد"}
        raise HTTPException(status_code=500, detail="Credit failed")
    finally:
        await db.close()

"""Conversion quote and confirm routes"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid

from models import ConvertQuoteRequest, ConversionConfirmRequest
from deps import get_current_user
from database import get_db
from ledger_service import LedgerService
from rate_service import RateService

router = APIRouter(tags=["conversions"])


@router.post("/convert/quote")
async def get_conversion_quote(
    request: ConvertQuoteRequest,
    user: dict = Depends(get_current_user)
):
    """Get conversion quote with 5-minute rate lock - uses live rates"""
    try:
        rate = await RateService.get_rate(request.from_asset, request.to_asset)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rate service unavailable: {str(e)}")

    if not rate or (rate == 1.0 and request.from_asset != request.to_asset):
        raise HTTPException(status_code=400, detail="Conversion pair not supported")

    quoted_amount = int(request.amount_minor * rate)
    fee = int(quoted_amount * 0.003)  # 0.3% fee
    final_amount = quoted_amount - fee

    quote_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.from_asset,))
        from_asset = await cursor.fetchone()
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.to_asset,))
        to_asset = await cursor.fetchone()

        if not from_asset or not to_asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO conversion_quotes
            (id, user_id, from_asset_id, to_asset_id, amount_minor, rate,
             quoted_amount_minor, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (quote_id, user["id"], from_asset["id"], to_asset["id"],
              request.amount_minor, rate, final_amount, expires_at.isoformat(), now))
        await db.commit()

        return {
            "quote_id": quote_id,
            "from_asset": request.from_asset,
            "to_asset": request.to_asset,
            "amount_from": request.amount_minor,
            "rate": rate,
            "amount_to": final_amount,
            "fee": fee,
            "expires_at": expires_at.isoformat(),
            "source": "live"
        }
    finally:
        await db.close()


@router.post("/conversions/confirm")
async def confirm_conversion(
    request: ConversionConfirmRequest,
    user: dict = Depends(get_current_user)
):
    """Confirm and execute conversion atomically (debit + credit in single DB transaction)"""
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT * FROM conversion_quotes
            WHERE id = ? AND user_id = ? AND status = 'active'
        """, (request.quote_id, user["id"]))
        quote = await cursor.fetchone()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found or expired")

        expires_at = datetime.fromisoformat(quote["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Quote has expired")

        cursor = await db.execute(
            "SELECT id FROM accounts WHERE user_id = ? AND asset_id = ?",
            (user["id"], quote["from_asset_id"])
        )
        from_account = await cursor.fetchone()
        cursor = await db.execute(
            "SELECT id FROM accounts WHERE user_id = ? AND asset_id = ?",
            (user["id"], quote["to_asset_id"])
        )
        to_account = await cursor.fetchone()

        if not from_account or not to_account:
            raise HTTPException(status_code=404, detail="Account not found")
    finally:
        await db.close()

    result = await LedgerService.convert_atomic(
        user_id=user["id"],
        from_account_id=from_account["id"],
        from_asset_id=quote["from_asset_id"],
        to_account_id=to_account["id"],
        to_asset_id=quote["to_asset_id"],
        amount_from_minor=quote["amount_minor"],
        amount_to_minor=quote["quoted_amount_minor"],
        rate=quote["rate"],
        source_ref=f"conversion-{request.quote_id}",
        quote_id=request.quote_id
    )

    if not result["ok"]:
        if result.get("error") == "insufficient_funds":
            raise HTTPException(status_code=400, detail="Insufficient funds")
        raise HTTPException(status_code=500, detail=result.get("error", "Conversion failed"))

    return {
        "success": True,
        "transaction_id": result["transaction_id"],
        "idempotent": result.get("idempotent", False),
        "message": "تبدیل با موفقیت انجام شد"
    }

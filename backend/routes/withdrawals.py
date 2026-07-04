"""Withdrawal routes with Telegram OTP 2FA"""

from fastapi import APIRouter, HTTPException, Depends
import uuid

from models import WithdrawalRequest
from deps import get_current_user
from database import get_db
from ledger_service import LedgerService
from otp_service import OTPService

router = APIRouter(tags=["withdrawals"])

OTP_ERROR_MESSAGES = {
    "no_otp_found": "کد تایید یافت نشد. ابتدا کد تایید درخواست کنید.",
    "otp_expired": "کد تایید منقضی شده است. کد جدید درخواست کنید.",
    "too_many_attempts": "تعداد تلاش‌ها بیش از حد مجاز است. کد جدید درخواست کنید.",
    "invalid_code": "کد تایید اشتباه است."
}


@router.post("/withdrawals")
async def request_withdrawal(
    request: WithdrawalRequest,
    user: dict = Depends(get_current_user)
):
    """Request withdrawal (requires KYC approval + Telegram OTP)"""
    if user["kyc_status"] != "approved":
        raise HTTPException(status_code=403, detail="KYC verification required for withdrawals")

    if request.amount_minor < 50000:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is 50,000 IRR")

    # 2FA: verify Telegram OTP
    if not request.otp_code:
        raise HTTPException(status_code=400, detail="otp_required: کد تایید تلگرام الزامی است")

    otp_result = await OTPService.verify_otp(user["id"], request.otp_code, "withdrawal")
    if not otp_result["ok"]:
        raise HTTPException(
            status_code=400,
            detail=OTP_ERROR_MESSAGES.get(otp_result.get("error"), "خطا در تایید کد")
        )

    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT a.id, ast.id as asset_id
            FROM accounts a
            INNER JOIN assets ast ON a.asset_id = ast.id
            WHERE a.user_id = ? AND ast.code = ?
        """, (user["id"], request.asset))
        account = await cursor.fetchone()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
    finally:
        await db.close()

    source_ref = f"withdrawal-{uuid.uuid4()}"
    reserve_result = await LedgerService.reserve_amount(
        user_id=user["id"],
        account_id=account["id"],
        asset_id=account["asset_id"],
        amount_minor=request.amount_minor,
        source_ref=source_ref,
        reason="withdrawal_pending"
    )

    if not reserve_result["ok"]:
        raise HTTPException(status_code=400, detail=reserve_result.get("error", "Insufficient funds"))

    return {
        "success": True,
        "withdrawal_id": reserve_result["transaction_id"],
        "status": "pending",
        "amount": request.amount_minor,
        "destination": request.destination,
        "estimated_completion": "24-48 hours",
        "message": "درخواست برداشت شما ثبت شد و در حال بررسی است"
    }

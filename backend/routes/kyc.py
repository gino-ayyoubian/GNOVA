"""KYC and OTP routes"""

from fastapi import APIRouter, HTTPException, Depends
import os

from models import KYCSubmitRequest, OTPRequestModel, OTPVerifyModel
from deps import get_current_user
from kyc_service import KYCService
from otp_service import OTPService

router = APIRouter(tags=["kyc", "otp"])


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


@router.post("/kyc/submit")
async def submit_kyc(
    request: KYCSubmitRequest,
    user: dict = Depends(get_current_user)
):
    result = await KYCService.submit_kyc(
        user_id=user["id"],
        full_name=request.full_name,
        national_id=request.national_id,
        birth_date=request.birth_date,
        address=request.address,
        phone=request.phone
    )
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/kyc/status")
async def get_kyc_status(user: dict = Depends(get_current_user)):
    status = await KYCService.get_kyc_status(user["id"])
    return {"kyc_status": user.get("kyc_status", "pending"), "submission": status}


@router.post("/kyc/auto-approve")
async def auto_approve_kyc(user: dict = Depends(get_current_user)):
    """DEMO ONLY: auto-approve KYC. Gated by DEMO_MODE env flag."""
    if not _demo_mode():
        raise HTTPException(status_code=403, detail="Auto-approve is disabled in production")
    result = await KYCService.approve_kyc(user["id"])
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/otp/request")
async def request_otp(
    request: OTPRequestModel,
    user: dict = Depends(get_current_user)
):
    """Request an OTP code via Telegram"""
    result = await OTPService.create_otp(user["id"], request.purpose)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    sent = await OTPService.send_otp_telegram(
        telegram_id=user["telegram_id"],
        code=result["code"],
        purpose=request.purpose
    )

    response = {
        "success": True,
        "sent_via_telegram": sent,
        "expires_at": result["expires_at"],
        "expires_in_seconds": result["expires_in_seconds"]
    }
    # DEMO fallback: expose code when Telegram delivery fails (no chat with bot)
    if not sent and _demo_mode():
        response["debug_code"] = result["code"]
    return response


@router.post("/otp/verify")
async def verify_otp(
    request: OTPVerifyModel,
    user: dict = Depends(get_current_user)
):
    result = await OTPService.verify_otp(user["id"], request.code, request.purpose)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return {"success": True, "message": result["message"]}

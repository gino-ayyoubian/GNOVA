"""GNOVA API Pydantic models"""

from pydantic import BaseModel, Field
from typing import Optional


class RegisterRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    telegram_id: int


class DepositInitiateRequest(BaseModel):
    amount_irr: int = Field(..., gt=0, description="Amount in IRR")


class WebhookPayload(BaseModel):
    transaction_id: str
    paid_amount: int
    status: str
    user_id: str
    metadata: Optional[dict] = None


class ConvertQuoteRequest(BaseModel):
    from_asset: str
    to_asset: str
    amount_minor: int


class ConversionConfirmRequest(BaseModel):
    quote_id: str


class WithdrawalRequest(BaseModel):
    asset: str
    amount_minor: int
    destination: str
    destination_type: str = "card"  # card, iban, crypto_address
    otp_code: Optional[str] = None


class RateAlertRequest(BaseModel):
    from_asset: str
    to_asset: str
    target_rate: float
    condition: str = "below"  # below, above


class KYCSubmitRequest(BaseModel):
    full_name: str
    national_id: str
    birth_date: str
    address: str
    phone: str


class OTPRequestModel(BaseModel):
    purpose: str = "withdrawal"


class OTPVerifyModel(BaseModel):
    code: str
    purpose: str = "withdrawal"


class ZarinPalCallbackRequest(BaseModel):
    deposit_id: str
    authority: str
    status: str
    amount: int

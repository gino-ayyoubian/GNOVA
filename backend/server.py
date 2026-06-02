"""
GNOVA Fintech Platform - Main FastAPI Server
Complete API endpoints for financial operations
"""

from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import os
import uuid
import json
import hmac
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Import services
from database import get_db, init_database
from auth_service import AuthService
from ledger_service import LedgerService
from rate_service import RateService
from zarinpal_service import ZarinPalService
from kyc_service import KYCService
from otp_service import OTPService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="GNOVA Fintech API", version="1.1.0")

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Initialize ZarinPal service
zarinpal = ZarinPalService()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

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


# ==================== Auth Dependency ====================

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    payload = AuthService.decode_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = await AuthService.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is not active")
    
    return user


# ==================== Routes ====================

@api_router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "GNOVA Fintech API",
        "version": "1.0.0",
        "status": "operational"
    }

@api_router.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "services": {
            "auth": "operational",
            "ledger": "operational",
            "telegram_bot": "operational"
        }
    }


# ==================== Authentication ====================

@api_router.post("/auth/register")
async def register_user(request: RegisterRequest):
    """Register new user"""
    result = await AuthService.register_user(
        telegram_id=request.telegram_id,
        username=request.username,
        email=request.email
    )
    
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Registration failed"))
    
    return {
        "success": True,
        "user_id": result["user_id"],
        "token": result["token"]
    }

@api_router.post("/auth/login")
async def login_user(request: LoginRequest):
    """Login user via Telegram"""
    result = await AuthService.login_telegram(request.telegram_id)
    
    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Login failed"))
    
    return {
        "success": True,
        "user_id": result["user_id"],
        "token": result["token"]
    }

@api_router.get("/auth/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": user["id"],
        "telegram_id": user["telegram_id"],
        "username": user["username"],
        "kyc_status": user["kyc_status"],
        "risk_level": user["risk_level"],
        "status": user["status"],
        "created_at": user["created_at"]
    }


# ==================== Wallet Operations ====================

@api_router.get("/wallets")
async def get_wallets(user: dict = Depends(get_current_user)):
    """Get user wallet balances"""
    balances = await LedgerService.compute_all_balances(user["id"])
    
    result = {
        "user_id": user["id"],
        "balances": [],
        "total_value_irr": 0,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    for bal in balances:
        amount = bal["balance_minor"]
        precision = bal["decimal_precision"]
        
        # Convert to major units for display
        if precision > 0:
            amount_display = amount / (10 ** precision)
        else:
            amount_display = amount
        
        result["balances"].append({
            "asset_code": bal["asset_code"],
            "asset_name": bal["asset_name"],
            "balance_minor": amount,
            "balance_display": amount_display,
            "decimal_precision": precision
        })
        
        # Calculate total value in IRR (mock rates)
        if bal["asset_code"] == "IRR" or bal["asset_code"] == "CREDIT":
            result["total_value_irr"] += amount
        elif bal["asset_code"] == "USDT":
            result["total_value_irr"] += amount * 65000  # Mock rate
        elif bal["asset_code"] == "BTC":
            result["total_value_irr"] += amount * 2850000000 // (10 ** 8)  # Mock rate
    
    return result


# ==================== Deposits ====================

@api_router.post("/deposits/initiate")
async def initiate_deposit(
    request: DepositInitiateRequest,
    user: dict = Depends(get_current_user)
):
    """Initiate IRR deposit via payment gateway"""
    
    # Validate amount
    if request.amount_irr < 10000:
        raise HTTPException(status_code=400, detail="Minimum deposit is 10,000 IRR")
    
    if request.amount_irr > 100000000:
        raise HTTPException(status_code=400, detail="Maximum deposit is 100,000,000 IRR")
    
    # Create deposit record
    deposit_id = str(uuid.uuid4())
    
    # In production, this would call actual PSP API
    # For now, return mock payment URL
    payment_url = f"{os.getenv('APP_URL')}/payment/{deposit_id}"
    
    return {
        "success": True,
        "deposit_id": deposit_id,
        "amount_irr": request.amount_irr,
        "payment_url": payment_url,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        "instructions": "برای تکمیل واریز، روی لینک پرداخت کلیک کنید و مراحل را دنبال کنید."
    }


@api_router.post("/webhooks/payment")
async def payment_webhook(
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None)
):
    """Handle payment gateway webhook callbacks"""
    
    # Verify signature (HMAC)
    secret = os.getenv("PAYMENT_GATEWAY_SECRET", "")
    payload_str = json.dumps(payload.model_dump(), sort_keys=True)
    
    if x_signature:
        expected_signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if x_signature != expected_signature:
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Check if already processed (idempotency)
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM webhook_events WHERE external_id = ?",
            (payload.transaction_id,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            return {"success": True, "message": "Already processed"}
        
        # Store webhook event
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO webhook_events 
            (id, provider, external_id, payload, signature_valid, processed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "psp", payload.transaction_id, 
              json.dumps(payload.model_dump()), 1 if x_signature else 0, 0, now))
        
        await db.commit()
        
        # Process payment if successful
        if payload.status == "success":
            # Get user account for CREDIT asset
            credit_asset_id = os.getenv("CREDIT_ASSET_ID", "asset-credit-irr")
            
            cursor = await db.execute("""
                SELECT id FROM accounts 
                WHERE user_id = ? AND asset_id = ?
            """, (payload.user_id, credit_asset_id))
            
            account = await cursor.fetchone()
            
            if account:
                # Credit the account
                result = await LedgerService.credit_account(
                    user_id=payload.user_id,
                    account_id=account["id"],
                    asset_id=credit_asset_id,
                    amount_minor=payload.paid_amount,
                    source_event="deposit_confirmed",
                    source_ref=payload.transaction_id,
                    metadata=payload.metadata
                )
                
                if result["ok"]:
                    # Mark webhook as processed
                    await db.execute("""
                        UPDATE webhook_events 
                        SET processed = 1 
                        WHERE external_id = ?
                    """, (payload.transaction_id,))
                    await db.commit()
                    
                    return {"success": True, "message": "Payment processed"}
        
        return {"success": True, "message": "Webhook received"}
        
    finally:
        await db.close()


# ==================== Conversions ====================

@api_router.post("/convert/quote")
async def get_conversion_quote(
    request: ConvertQuoteRequest,
    user: dict = Depends(get_current_user)
):
    """Get conversion quote with rate lock - uses live rates"""
    
    # Get live rate from RateService
    try:
        rate = await RateService.get_rate(request.from_asset, request.to_asset)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rate service unavailable: {str(e)}")
    
    if not rate or rate == 1.0 and request.from_asset != request.to_asset:
        raise HTTPException(status_code=400, detail="Conversion pair not supported")
    
    quoted_amount = int(request.amount_minor * rate)
    fee = int(quoted_amount * 0.003)  # 0.3% fee
    final_amount = quoted_amount - fee
    
    # Create quote
    quote_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    db = await get_db()
    try:
        # Get asset IDs
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.from_asset,))
        from_asset = await cursor.fetchone()
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.to_asset,))
        to_asset = await cursor.fetchone()
        
        if not from_asset or not to_asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Store quote
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


@api_router.post("/conversions/confirm")
async def confirm_conversion(
    request: ConversionConfirmRequest,
    user: dict = Depends(get_current_user)
):
    """Confirm and execute conversion"""
    
    db = await get_db()
    try:
        # Get quote
        cursor = await db.execute("""
            SELECT * FROM conversion_quotes 
            WHERE id = ? AND user_id = ? AND status = 'active'
        """, (request.quote_id, user["id"]))
        
        quote = await cursor.fetchone()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found or expired")
        
        # Check expiration
        expires_at = datetime.fromisoformat(quote["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Quote has expired")
        
        # Get user accounts
        cursor = await db.execute("""
            SELECT id FROM accounts 
            WHERE user_id = ? AND asset_id = ?
        """, (user["id"], quote["from_asset_id"]))
        from_account = await cursor.fetchone()
        
        cursor = await db.execute("""
            SELECT id FROM accounts 
            WHERE user_id = ? AND asset_id = ?
        """, (user["id"], quote["to_asset_id"]))
        to_account = await cursor.fetchone()
        
        if not from_account or not to_account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Debit from account
        source_ref = f"conversion-{request.quote_id}"
        debit_result = await LedgerService.debit_account(
            user_id=user["id"],
            account_id=from_account["id"],
            asset_id=quote["from_asset_id"],
            amount_minor=quote["amount_minor"],
            source_event="conversion_debit",
            source_ref=f"{source_ref}-debit",
            metadata={"quote_id": request.quote_id}
        )
        
        if not debit_result["ok"]:
            raise HTTPException(status_code=400, detail=debit_result.get("error", "Insufficient funds"))
        
        # Credit to account
        credit_result = await LedgerService.credit_account(
            user_id=user["id"],
            account_id=to_account["id"],
            asset_id=quote["to_asset_id"],
            amount_minor=quote["quoted_amount_minor"],
            source_event="conversion_credit",
            source_ref=f"{source_ref}-credit",
            metadata={"quote_id": request.quote_id}
        )
        
        if not credit_result["ok"]:
            raise HTTPException(status_code=500, detail="Conversion failed")
        
        # Mark quote as used
        await db.execute("""
            UPDATE conversion_quotes 
            SET status = 'completed' 
            WHERE id = ?
        """, (request.quote_id,))
        
        await db.commit()
        
        return {
            "success": True,
            "transaction_id": credit_result["transaction_id"],
            "message": "تبدیل با موفقیت انجام شد"
        }
        
    finally:
        await db.close()


# ==================== Withdrawals ====================

@api_router.post("/withdrawals")
async def request_withdrawal(
    request: WithdrawalRequest,
    user: dict = Depends(get_current_user)
):
    """Request withdrawal"""
    
    # Check KYC status
    if user["kyc_status"] != "approved":
        raise HTTPException(
            status_code=403,
            detail="KYC verification required for withdrawals"
        )
    
    # Validate amount
    if request.amount_minor < 50000:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is 50,000 IRR")
    
    # Get user account
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
        
        # Reserve amount (creates PENDING debit)
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
            raise HTTPException(
                status_code=400,
                detail=reserve_result.get("error", "Insufficient funds")
            )
        
        return {
            "success": True,
            "withdrawal_id": reserve_result["transaction_id"],
            "status": "pending",
            "amount": request.amount_minor,
            "destination": request.destination,
            "estimated_completion": "24-48 hours",
            "message": "درخواست برداشت شما ثبت شد و در حال بررسی است"
        }
        
    finally:
        await db.close()


# ==================== Transaction History ====================

@api_router.get("/transactions")
async def get_transactions(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get transaction history"""
    
    history = await LedgerService.get_transaction_history(
        user_id=user["id"],
        limit=limit,
        offset=offset
    )
    
    return {
        "transactions": history,
        "total": len(history),
        "limit": limit,
        "offset": offset
    }


# ==================== Rate Alerts ====================

@api_router.post("/alerts/rate")
async def create_rate_alert(
    request: RateAlertRequest,
    user: dict = Depends(get_current_user)
):
    """Create rate alert"""
    
    db = await get_db()
    try:
        # Get asset IDs
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.from_asset,))
        from_asset = await cursor.fetchone()
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.to_asset,))
        to_asset = await cursor.fetchone()
        
        if not from_asset or not to_asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Create alert
        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        await db.execute("""
            INSERT INTO rate_alerts
            (id, user_id, from_asset_id, to_asset_id, target_rate, condition, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (alert_id, user["id"], from_asset["id"], to_asset["id"],
              request.target_rate, request.condition, now))
        
        await db.commit()
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": "هشدار نرخ ایجاد شد"
        }
        
    finally:
        await db.close()


@api_router.get("/alerts")
async def get_rate_alerts(user: dict = Depends(get_current_user)):
    """Get user's rate alerts"""
    
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT 
                ra.id,
                fa.code as from_asset,
                ta.code as to_asset,
                ra.target_rate,
                ra.condition,
                ra.status,
                ra.created_at
            FROM rate_alerts ra
            INNER JOIN assets fa ON ra.from_asset_id = fa.id
            INNER JOIN assets ta ON ra.to_asset_id = ta.id
            WHERE ra.user_id = ? AND ra.status = 'active'
            ORDER BY ra.created_at DESC
        """, (user["id"],))
        
        alerts = await cursor.fetchall()
        return {"alerts": [dict(alert) for alert in alerts]}
        
    finally:
        await db.close()


@api_router.delete("/alerts/{alert_id}")
async def delete_rate_alert(alert_id: str, user: dict = Depends(get_current_user)):
    """Delete a rate alert"""
    db = await get_db()
    try:
        await db.execute("""
            UPDATE rate_alerts SET status='deleted' 
            WHERE id=? AND user_id=?
        """, (alert_id, user["id"]))
        await db.commit()
        return {"success": True}
    finally:
        await db.close()


# ==================== Live Rates ====================

@api_router.get("/rates")
async def get_current_rates():
    """Get live exchange rates from Nobitex/CoinGecko"""
    rates = await RateService.get_all_rates()
    return {"rates": rates, "updated_at": datetime.now(timezone.utc).isoformat()}


@api_router.get("/rates/{from_asset}/{to_asset}")
async def get_specific_rate(from_asset: str, to_asset: str):
    """Get a specific exchange rate"""
    rate = await RateService.get_rate(from_asset.upper(), to_asset.upper())
    return {
        "from": from_asset.upper(),
        "to": to_asset.upper(),
        "rate": rate,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


# ==================== KYC ====================

@api_router.post("/kyc/submit")
async def submit_kyc(
    request: KYCSubmitRequest,
    user: dict = Depends(get_current_user)
):
    """Submit KYC application"""
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


@api_router.get("/kyc/status")
async def get_kyc_status(user: dict = Depends(get_current_user)):
    """Get current user's KYC status"""
    status = await KYCService.get_kyc_status(user["id"])
    return {
        "kyc_status": user.get("kyc_status", "pending"),
        "submission": status
    }


@api_router.post("/kyc/auto-approve")
async def auto_approve_kyc(user: dict = Depends(get_current_user)):
    """
    Auto-approve KYC for demo purposes.
    In production, this would be admin-only and require manual review.
    """
    result = await KYCService.approve_kyc(user["id"])
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ==================== OTP / 2FA ====================

@api_router.post("/otp/request")
async def request_otp(
    request: OTPRequestModel,
    user: dict = Depends(get_current_user)
):
    """Request an OTP code via Telegram"""
    result = await OTPService.create_otp(user["id"], request.purpose)
    
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    # Send via Telegram
    sent = await OTPService.send_otp_telegram(
        telegram_id=user["telegram_id"],
        code=result["code"],
        purpose=request.purpose
    )
    
    return {
        "success": True,
        "sent_via_telegram": sent,
        "expires_at": result["expires_at"],
        "expires_in_seconds": result["expires_in_seconds"]
    }


@api_router.post("/otp/verify")
async def verify_otp(
    request: OTPVerifyModel,
    user: dict = Depends(get_current_user)
):
    """Verify an OTP code"""
    result = await OTPService.verify_otp(user["id"], request.code, request.purpose)
    
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return {"success": True, "message": result["message"]}


# ==================== ZarinPal Integration ====================

@api_router.get("/payment/zarinpal/status")
async def zarinpal_status():
    """Check if ZarinPal is configured"""
    return {
        "configured": zarinpal.is_configured(),
        "sandbox": zarinpal.sandbox,
        "message": "ZarinPal sandbox mode" if zarinpal.sandbox else "ZarinPal production mode"
    }


@api_router.post("/payment/zarinpal/request")
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
            # Fallback to mock PSP if not configured
            return {
                "success": True,
                "deposit_id": deposit_id,
                "amount_irr": request.amount_irr,
                "payment_url": f"{os.getenv('APP_URL')}/payment/{deposit_id}",
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
                "instructions": "Mock payment (ZarinPal not configured)",
                "mode": "mock"
            }
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    # Store pending deposit
    db = await get_db()
    try:
        await db.execute("""
            INSERT INTO webhook_events (id, provider, external_id, payload, signature_valid, processed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "zarinpal",
            result["authority"],
            json.dumps({
                "user_id": user["id"],
                "amount_irr": request.amount_irr,
                "deposit_id": deposit_id,
                "status": "pending"
            }),
            1, 0,
            datetime.now(timezone.utc).isoformat()
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


@api_router.post("/payment/zarinpal/verify")
async def zarinpal_verify(request: ZarinPalCallbackRequest):
    """Verify ZarinPal payment after user returns from gateway"""
    
    if request.status != "OK":
        return {"success": False, "error": "Payment was cancelled"}
    
    # Find the webhook event
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT * FROM webhook_events 
            WHERE external_id = ? AND provider = 'zarinpal'
        """, (request.authority,))
        event = await cursor.fetchone()
        
        if not event:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check if already processed (idempotency)
        if event["processed"]:
            return {"success": True, "message": "Already processed"}
        
        payload = json.loads(event["payload"])
        user_id = payload["user_id"]
        amount = payload["amount_irr"]
        
        # Verify with ZarinPal
        verify_result = await zarinpal.verify_payment(request.authority, amount)
        
        if not verify_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=verify_result.get("error", "Verification failed")
            )
        
        # Get user's CREDIT account
        credit_asset_id = os.getenv("CREDIT_ASSET_ID", "asset-credit-irr")
        cursor = await db.execute("""
            SELECT id FROM accounts WHERE user_id=? AND asset_id=?
        """, (user_id, credit_asset_id))
        account = await cursor.fetchone()
        
        if not account:
            raise HTTPException(status_code=404, detail="User account not found")
        
        # Credit the account (idempotent via ref_id)
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
            await db.execute("""
                UPDATE webhook_events SET processed=1 WHERE external_id=?
            """, (request.authority,))
            await db.commit()
            
            return {
                "success": True,
                "ref_id": ref_id,
                "amount": amount,
                "message": "پرداخت با موفقیت تایید شد"
            }
        else:
            raise HTTPException(status_code=500, detail="Credit failed")
        
    finally:
        await db.close()


# ==================== Analytics ====================

@api_router.get("/analytics/summary")
async def get_analytics_summary(user: dict = Depends(get_current_user)):
    """Get spending analytics summary"""
    db = await get_db()
    try:
        # Total deposits this month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        cursor = await db.execute("""
            SELECT 
                SUM(CASE WHEN type IN ('deposit', 'deposit_confirmed', 'deposit_zarinpal') 
                    THEN amount_from_minor ELSE 0 END) as total_deposits,
                SUM(CASE WHEN type IN ('withdraw', 'reserve') 
                    THEN amount_from_minor ELSE 0 END) as total_withdrawals,
                COUNT(*) as total_transactions
            FROM transactions
            WHERE user_id = ? AND created_at >= ?
        """, (user["id"], month_start))
        
        row = await cursor.fetchone()
        
        # Transaction count by type
        cursor = await db.execute("""
            SELECT type, COUNT(*) as count, SUM(amount_from_minor) as total
            FROM transactions
            WHERE user_id = ?
            GROUP BY type
        """, (user["id"],))
        by_type = await cursor.fetchall()
        
        # Daily transactions last 30 days
        cursor = await db.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count,
                SUM(amount_from_minor) as total
            FROM transactions
            WHERE user_id = ? 
            AND created_at >= datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (user["id"],))
        daily = await cursor.fetchall()
        
        return {
            "this_month": {
                "total_deposits": row["total_deposits"] or 0,
                "total_withdrawals": row["total_withdrawals"] or 0,
                "net_flow": (row["total_deposits"] or 0) - (row["total_withdrawals"] or 0),
                "total_transactions": row["total_transactions"] or 0
            },
            "by_type": [dict(r) for r in by_type],
            "daily_last_30_days": [dict(r) for r in daily]
        }
    finally:
        await db.close()


# Include router in main app
app.include_router(api_router)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await init_database()
        await KYCService.init_kyc_table()
        await OTPService.init_otp_table()
        print("✅ GNOVA API Server started successfully")
        print(f"   ZarinPal: {'configured' if zarinpal.is_configured() else 'not configured (using mock)'}")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

"""
GNOVA ZarinPal Payment Gateway Service
Iranian PSP integration using ZarinPal v4 API
Docs: https://www.zarinpal.com/docs/
"""

import aiohttp
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# ZarinPal API endpoints
ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_PAYMENT_URL = "https://www.zarinpal.com/pg/StartPay/{authority}"

# Sandbox endpoints (use ZARINPAL_SANDBOX=true to enable)
ZARINPAL_SANDBOX_REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_SANDBOX_VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_SANDBOX_PAYMENT_URL = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"


class ZarinPalService:
    """ZarinPal Payment Gateway Integration"""
    
    def __init__(self):
        self.merchant_id = os.getenv("ZARINPAL_MERCHANT_ID", "")
        self.sandbox = os.getenv("ZARINPAL_SANDBOX", "true").lower() == "true"
        self.callback_base = os.getenv("APP_URL", "https://gnova.app")
        
        if self.sandbox:
            self.request_url = ZARINPAL_SANDBOX_REQUEST_URL
            self.verify_url = ZARINPAL_SANDBOX_VERIFY_URL
            self.payment_url_template = ZARINPAL_SANDBOX_PAYMENT_URL
        else:
            self.request_url = ZARINPAL_REQUEST_URL
            self.verify_url = ZARINPAL_VERIFY_URL
            self.payment_url_template = ZARINPAL_PAYMENT_URL
    
    def is_configured(self) -> bool:
        """Check if merchant_id is configured"""
        return bool(self.merchant_id and len(self.merchant_id) > 5)
    
    async def request_payment(
        self,
        amount_rial: int,
        deposit_id: str,
        user_email: Optional[str] = None,
        user_mobile: Optional[str] = None,
        description: str = "GNOVA Deposit"
    ) -> Dict:
        """
        Request a payment from ZarinPal
        amount_rial: Amount in IRR (rial)
        Returns: {success, authority, payment_url} or {success: false, error}
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "ZarinPal not configured. Set ZARINPAL_MERCHANT_ID env var.",
                "fallback": True
            }
        
        callback_url = f"{self.callback_base}/payment/zarinpal/callback?deposit_id={deposit_id}"
        
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_rial,
            "callback_url": callback_url,
            "description": description,
            "metadata": {}
        }
        
        if user_email:
            payload["metadata"]["email"] = user_email
        if user_mobile:
            payload["metadata"]["mobile"] = user_mobile
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.request_url, json=payload) as response:
                    data = await response.json()
                    
                    if data.get("data", {}).get("code") == 100:
                        authority = data["data"]["authority"]
                        return {
                            "success": True,
                            "authority": authority,
                            "payment_url": self.payment_url_template.format(authority=authority),
                            "code": 100
                        }
                    else:
                        errors = data.get("errors", {})
                        return {
                            "success": False,
                            "error": errors.get("message", "Unknown error"),
                            "code": errors.get("code"),
                            "validations": errors.get("validations", [])
                        }
        except Exception as e:
            logger.error(f"ZarinPal request error: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_payment(
        self,
        authority: str,
        amount_rial: int
    ) -> Dict:
        """
        Verify a completed payment from ZarinPal
        Should be called after user returns from ZarinPal with Status=OK
        Returns: {success, ref_id, card_pan} or {success: false, error}
        """
        if not self.is_configured():
            return {"success": False, "error": "ZarinPal not configured"}
        
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_rial,
            "authority": authority
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.verify_url, json=payload) as response:
                    data = await response.json()
                    
                    code = data.get("data", {}).get("code")
                    # 100 = success, 101 = already verified (still success)
                    if code in (100, 101):
                        return {
                            "success": True,
                            "ref_id": data["data"].get("ref_id"),
                            "card_pan": data["data"].get("card_pan"),
                            "card_hash": data["data"].get("card_hash"),
                            "fee": data["data"].get("fee"),
                            "code": code,
                            "already_verified": code == 101
                        }
                    else:
                        errors = data.get("errors", {})
                        return {
                            "success": False,
                            "error": errors.get("message", "Verification failed"),
                            "code": errors.get("code")
                        }
        except Exception as e:
            logger.error(f"ZarinPal verify error: {e}")
            return {"success": False, "error": str(e)}

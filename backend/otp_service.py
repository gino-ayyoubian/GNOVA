"""
GNOVA OTP Service - Two-Factor Authentication via Telegram
Generates time-limited OTPs and sends them via the Telegram bot
"""

import uuid
import secrets
import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from database import get_db

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 5
OTP_LENGTH = 6


class OTPService:
    """Handle OTP generation and verification"""
    
    @staticmethod
    async def init_otp_table():
        """Create OTP table if not exists"""
        db = await get_db()
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS otp_codes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used INTEGER DEFAULT 0,
                    attempts INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_otp_user_purpose 
                ON otp_codes(user_id, purpose, used)
            """)
            await db.commit()
        finally:
            await db.close()
    
    @staticmethod
    def generate_code() -> str:
        """Generate a random OTP code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])
    
    @staticmethod
    async def create_otp(user_id: str, purpose: str = "withdrawal") -> Dict:
        """
        Create a new OTP for the user.
        purpose: 'withdrawal', 'login', 'sensitive_operation'
        Returns: {code, expires_at}
        """
        db = await get_db()
        try:
            # Invalidate any existing unused OTPs for same purpose
            await db.execute("""
                UPDATE otp_codes SET used=1 
                WHERE user_id=? AND purpose=? AND used=0
            """, (user_id, purpose))
            
            code = OTPService.generate_code()
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
            otp_id = str(uuid.uuid4())
            
            await db.execute("""
                INSERT INTO otp_codes (id, user_id, code, purpose, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (otp_id, user_id, code, purpose, expires_at.isoformat(), now.isoformat()))
            
            await db.commit()
            
            return {
                "ok": True,
                "code": code,
                "expires_at": expires_at.isoformat(),
                "expires_in_seconds": OTP_EXPIRY_MINUTES * 60
            }
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()
    
    @staticmethod
    async def verify_otp(user_id: str, code: str, purpose: str = "withdrawal") -> Dict:
        """Verify an OTP code"""
        db = await get_db()
        try:
            await db.execute("BEGIN")
            
            cursor = await db.execute("""
                SELECT id, code, expires_at, used, attempts
                FROM otp_codes 
                WHERE user_id=? AND purpose=? AND used=0
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, purpose))
            otp = await cursor.fetchone()
            
            if not otp:
                await db.rollback()
                return {"ok": False, "error": "no_otp_found"}
            
            # Check expiration
            expires_at = datetime.fromisoformat(otp["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                await db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (otp["id"],))
                await db.commit()
                return {"ok": False, "error": "otp_expired"}
            
            # Check attempts (max 3)
            if otp["attempts"] >= 3:
                await db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (otp["id"],))
                await db.commit()
                return {"ok": False, "error": "too_many_attempts"}
            
            # Check code
            if otp["code"] != code:
                await db.execute(
                    "UPDATE otp_codes SET attempts=attempts+1 WHERE id=?",
                    (otp["id"],)
                )
                await db.commit()
                return {"ok": False, "error": "invalid_code", "attempts_left": 2 - otp["attempts"]}
            
            # Mark as used
            await db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (otp["id"],))
            await db.commit()
            
            return {"ok": True, "message": "OTP verified"}
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()
    
    @staticmethod
    async def send_otp_telegram(telegram_id: int, code: str, purpose: str = "withdrawal"):
        """Send OTP code to user via Telegram bot"""
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                logger.warning("Bot token not set, cannot send OTP")
                return False
            
            purpose_text = {
                "withdrawal": "تایید برداشت",
                "login": "ورود به حساب",
                "sensitive_operation": "عملیات حساس"
            }.get(purpose, "تایید")
            
            message = (
                f"🔐 *کد امنیتی GNOVA*\n\n"
                f"کد تایید شما برای {purpose_text}:\n\n"
                f"```\n{code}\n```\n\n"
                f"⏱ این کد فقط 5 دقیقه معتبر است.\n"
                f"⚠️ هرگز این کد را با کسی به اشتراک نگذارید."
            )
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={
                    "chat_id": telegram_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send OTP: {e}")
            return False

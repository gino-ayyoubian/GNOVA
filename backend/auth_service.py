"""
GNOVA Authentication Service
JWT-based auth with Telegram integration
"""

import jwt
import uuid
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from database import get_db
import os

JWT_SECRET = os.getenv("JWT_SECRET", "gnova-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30


class AuthService:
    """Handle authentication and user management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except:
            return False
    
    @staticmethod
    def create_jwt_token(user_id: str, telegram_id: Optional[int] = None) -> str:
        """Create JWT token for user"""
        payload = {
            "user_id": user_id,
            "telegram_id": telegram_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def decode_jwt_token(token: str) -> Optional[Dict]:
        """Decode and verify JWT token"""
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    async def register_user(
        telegram_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict:
        """Register new user (via Telegram or email)"""
        db = await get_db()
        try:
            await db.execute("BEGIN")
            
            # Check if user already exists
            cursor = await db.execute("""
                SELECT id FROM users WHERE telegram_id = ? OR email = ?
            """, (telegram_id, email))
            existing = await cursor.fetchone()
            
            if existing:
                await db.rollback()
                return {"ok": False, "error": "user_already_exists"}
            
            # Create user
            user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            password_hash = AuthService.hash_password(password) if password else None
            
            await db.execute("""
                INSERT INTO users 
                (id, telegram_id, username, email, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, telegram_id, username, email, password_hash, now, now))
            
            # Create default accounts for each asset
            cursor = await db.execute("SELECT id FROM assets WHERE is_active = 1")
            assets = await cursor.fetchall()
            
            for asset in assets:
                account_id = str(uuid.uuid4())
                await db.execute("""
                    INSERT INTO accounts (id, user_id, asset_id, account_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (account_id, user_id, asset["id"], "wallet", now))
            
            # Create user settings
            await db.execute("""
                INSERT INTO user_settings (user_id, language, currency)
                VALUES (?, ?, ?)
            """, (user_id, "fa", "IRR"))
            
            await db.commit()
            
            # Create JWT token
            token = AuthService.create_jwt_token(user_id, telegram_id)
            
            return {
                "ok": True,
                "user_id": user_id,
                "token": token
            }
            
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()
    
    @staticmethod
    async def login_telegram(telegram_id: int) -> Dict:
        """Login user via Telegram ID"""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT id, status FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            user = await cursor.fetchone()
            
            if not user:
                return {"ok": False, "error": "user_not_found"}
            
            if user["status"] != "active":
                return {"ok": False, "error": "account_suspended"}
            
            token = AuthService.create_jwt_token(user["id"], telegram_id)
            
            return {
                "ok": True,
                "user_id": user["id"],
                "token": token
            }
            
        finally:
            await db.close()
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT id, telegram_id, username, email, kyc_status, 
                       risk_level, status, created_at
                FROM users WHERE id = ?
            """, (user_id,))
            user = await cursor.fetchone()
            return dict(user) if user else None
        finally:
            await db.close()
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT id, telegram_id, username, email, kyc_status,
                       risk_level, status, created_at
                FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            user = await cursor.fetchone()
            return dict(user) if user else None
        finally:
            await db.close()
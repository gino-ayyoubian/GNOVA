"""
GNOVA KYC Service - Know Your Customer verification
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Optional
from database import get_db


class KYCService:
    """Handle KYC submission and approval"""
    
    @staticmethod
    async def init_kyc_table():
        """Create KYC submissions table if not exists"""
        db = await get_db()
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS kyc_submissions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    national_id TEXT NOT NULL,
                    birth_date TEXT NOT NULL,
                    address TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    document_url TEXT,
                    selfie_url TEXT,
                    status TEXT DEFAULT 'pending',
                    rejection_reason TEXT,
                    submitted_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            await db.commit()
        finally:
            await db.close()
    
    @staticmethod
    async def submit_kyc(
        user_id: str,
        full_name: str,
        national_id: str,
        birth_date: str,
        address: str,
        phone: str,
        document_url: Optional[str] = None,
        selfie_url: Optional[str] = None
    ) -> Dict:
        """Submit KYC application"""
        db = await get_db()
        try:
            await db.execute("BEGIN")
            
            # Check if already submitted
            cursor = await db.execute(
                "SELECT id, status FROM kyc_submissions WHERE user_id = ?",
                (user_id,)
            )
            existing = await cursor.fetchone()
            
            if existing:
                if existing["status"] == "approved":
                    await db.rollback()
                    return {"ok": False, "error": "KYC already approved"}
                if existing["status"] == "pending":
                    await db.rollback()
                    return {"ok": False, "error": "KYC submission pending review"}
                
                # Allow resubmission if previously rejected
                await db.execute("""
                    UPDATE kyc_submissions 
                    SET full_name=?, national_id=?, birth_date=?, address=?, phone=?,
                        document_url=?, selfie_url=?, status='pending', 
                        rejection_reason=NULL, submitted_at=?
                    WHERE user_id=?
                """, (full_name, national_id, birth_date, address, phone,
                       document_url, selfie_url, 
                       datetime.now(timezone.utc).isoformat(), user_id))
            else:
                kyc_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()
                
                await db.execute("""
                    INSERT INTO kyc_submissions
                    (id, user_id, full_name, national_id, birth_date, address, phone,
                     document_url, selfie_url, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (kyc_id, user_id, full_name, national_id, birth_date, 
                       address, phone, document_url, selfie_url, now))
            
            # Update user's KYC status to "submitted"
            await db.execute("""
                UPDATE users SET kyc_status='submitted', updated_at=? WHERE id=?
            """, (datetime.now(timezone.utc).isoformat(), user_id))
            
            await db.commit()
            return {"ok": True, "message": "KYC submitted successfully"}
            
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()
    
    @staticmethod
    async def get_kyc_status(user_id: str) -> Optional[Dict]:
        """Get user's KYC submission status"""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT * FROM kyc_submissions WHERE user_id = ?
            """, (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await db.close()
    
    @staticmethod
    async def approve_kyc(user_id: str) -> Dict:
        """Auto-approve KYC (for demo/testing)"""
        db = await get_db()
        try:
            await db.execute("BEGIN")
            
            now = datetime.now(timezone.utc).isoformat()
            
            # Update submission
            cursor = await db.execute(
                "UPDATE kyc_submissions SET status='approved', reviewed_at=? WHERE user_id=?",
                (now, user_id)
            )
            
            # Update user
            await db.execute(
                "UPDATE users SET kyc_status='approved', updated_at=? WHERE id=?",
                (now, user_id)
            )
            
            await db.commit()
            return {"ok": True, "message": "KYC approved"}
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()

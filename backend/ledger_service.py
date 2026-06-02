"""
GNOVA Ledger Service - Double Entry Bookkeeping
The Internal Ledger is the single source of truth.
Balances are derived, never stored. Transactions are immutable.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, List
from database import get_db


class LedgerService:
    """Handle all ledger operations with ACID guarantees"""
    
    @staticmethod
    async def compute_balance(account_id: str) -> int:
        """
        Compute account balance from ledger entries.
        Balance = SUM(FINAL credits) - SUM(FINAL debits)
        """
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT 
                    COALESCE(SUM(credit_minor), 0) - COALESCE(SUM(debit_minor), 0) as balance
                FROM ledger_entries
                WHERE account_id = ? AND status = 'FINAL'
            """, (account_id,))
            row = await cursor.fetchone()
            return row["balance"] if row else 0
        finally:
            await db.close()
    
    @staticmethod
    async def compute_all_balances(user_id: str) -> List[Dict]:
        """Compute balances for all user accounts"""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT 
                    a.id as account_id,
                    a.asset_id,
                    ast.code as asset_code,
                    ast.name as asset_name,
                    ast.decimal_precision,
                    COALESCE(SUM(le.credit_minor), 0) - COALESCE(SUM(le.debit_minor), 0) as balance_minor
                FROM accounts a
                INNER JOIN assets ast ON a.asset_id = ast.id
                LEFT JOIN ledger_entries le ON le.account_id = a.id AND le.status = 'FINAL'
                WHERE a.user_id = ? AND a.status = 'active'
                GROUP BY a.id, a.asset_id, ast.code, ast.name, ast.decimal_precision
            """, (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()
    
    @staticmethod
    async def reserve_amount(
        user_id: str,
        account_id: str,
        asset_id: str,
        amount_minor: int,
        source_ref: str,
        reason: str
    ) -> Dict:
        """
        Reserve (lock) an amount for pending operations.
        Creates a PENDING debit entry.
        """
        db = await get_db()
        try:
            await db.execute("BEGIN")
            
            # Check available balance
            cursor = await db.execute("""
                SELECT 
                    COALESCE(SUM(credit_minor), 0) - COALESCE(SUM(debit_minor), 0) as balance
                FROM ledger_entries
                WHERE account_id = ? AND status = 'FINAL'
            """, (account_id,))
            row = await cursor.fetchone()
            available = row["balance"] if row else 0
            
            if available < amount_minor:
                await db.rollback()
                return {"ok": False, "error": "insufficient_funds", "available": available}
            
            # Create transaction
            tx_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            await db.execute("""
                INSERT INTO transactions 
                (id, user_id, type, amount_from_minor, status, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, user_id, "reserve", amount_minor, "processing", 
                   json.dumps({"reason": reason}), now, now))
            
            # Create pending debit ledger entry
            entry_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO ledger_entries
                (id, transaction_id, account_id, asset_id, debit_minor, credit_minor,
                 source_event, source_ref, status, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_id, tx_id, account_id, asset_id, amount_minor, 0,
                   "reserve", source_ref, "PENDING", json.dumps({"reason": reason}), now))
            
            await db.commit()
            return {"ok": True, "transaction_id": tx_id, "entry_id": entry_id}
            
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()
    
    @staticmethod
    async def credit_account(
        user_id: str,
        account_id: str,
        asset_id: str,
        amount_minor: int,
        source_event: str,
        source_ref: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Credit (add) amount to account.
        Creates a FINAL credit entry.
        Idempotent based on source_ref.
        """
        db = await get_db()
        try:
            await db.execute("BEGIN")
            
            # Check if already processed (idempotency)
            cursor = await db.execute("""
                SELECT id FROM ledger_entries WHERE source_ref = ? LIMIT 1
            """, (source_ref,))
            existing = await cursor.fetchone()
            
            if existing:
                await db.rollback()
                return {"ok": True, "message": "already_processed", "idempotent": True}
            
            # Create transaction
            tx_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            await db.execute("""
                INSERT INTO transactions
                (id, user_id, type, amount_from_minor, status, reference_id, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, user_id, source_event, amount_minor, "settled", source_ref,
                   json.dumps(metadata or {}), now, now))
            
            # Create credit ledger entry
            entry_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO ledger_entries
                (id, transaction_id, account_id, asset_id, debit_minor, credit_minor,
                 source_event, source_ref, status, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_id, tx_id, account_id, asset_id, 0, amount_minor,
                   source_event, source_ref, "FINAL", json.dumps(metadata or {}), now))
            
            await db.commit()
            return {"ok": True, "transaction_id": tx_id, "entry_id": entry_id}
            
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()
    
    @staticmethod
    async def debit_account(
        user_id: str,
        account_id: str,
        asset_id: str,
        amount_minor: int,
        source_event: str,
        source_ref: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Debit (subtract) amount from account.
        Creates a FINAL debit entry.
        Checks for sufficient balance.
        """
        db = await get_db()
        try:
            await db.execute("BEGIN")
            
            # Check if already processed
            cursor = await db.execute("""
                SELECT id FROM ledger_entries WHERE source_ref = ? LIMIT 1
            """, (source_ref,))
            existing = await cursor.fetchone()
            
            if existing:
                await db.rollback()
                return {"ok": True, "message": "already_processed", "idempotent": True}
            
            # Check balance
            cursor = await db.execute("""
                SELECT 
                    COALESCE(SUM(credit_minor), 0) - COALESCE(SUM(debit_minor), 0) as balance
                FROM ledger_entries
                WHERE account_id = ? AND status = 'FINAL'
            """, (account_id,))
            row = await cursor.fetchone()
            available = row["balance"] if row else 0
            
            if available < amount_minor:
                await db.rollback()
                return {"ok": False, "error": "insufficient_funds", "available": available}
            
            # Create transaction
            tx_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            await db.execute("""
                INSERT INTO transactions
                (id, user_id, type, amount_from_minor, status, reference_id, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, user_id, source_event, amount_minor, "settled", source_ref,
                   json.dumps(metadata or {}), now, now))
            
            # Create debit ledger entry
            entry_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO ledger_entries
                (id, transaction_id, account_id, asset_id, debit_minor, credit_minor,
                 source_event, source_ref, status, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_id, tx_id, account_id, asset_id, amount_minor, 0,
                   source_event, source_ref, "FINAL", json.dumps(metadata or {}), now))
            
            await db.commit()
            return {"ok": True, "transaction_id": tx_id, "entry_id": entry_id}
            
        except Exception as e:
            await db.rollback()
            return {"ok": False, "error": str(e)}
        finally:
            await db.close()
    
    @staticmethod
    async def get_transaction_history(
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get user transaction history"""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT 
                    t.id,
                    t.type,
                    t.status,
                    t.amount_from_minor,
                    t.amount_to_minor,
                    t.fee_minor,
                    t.reference_id,
                    t.metadata,
                    t.created_at,
                    af.code as asset_from_code,
                    at.code as asset_to_code
                FROM transactions t
                LEFT JOIN assets af ON t.asset_from_id = af.id
                LEFT JOIN assets at ON t.asset_to_id = at.id
                WHERE t.user_id = ?
                ORDER BY t.created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()
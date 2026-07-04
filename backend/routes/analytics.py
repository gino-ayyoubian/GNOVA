"""Analytics routes"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone

from deps import get_current_user
from database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary(user: dict = Depends(get_current_user)):
    """Get spending analytics summary"""
    db = await get_db()
    try:
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

        cursor = await db.execute("""
            SELECT type, COUNT(*) as count, SUM(amount_from_minor) as total
            FROM transactions
            WHERE user_id = ?
            GROUP BY type
        """, (user["id"],))
        by_type = await cursor.fetchall()

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

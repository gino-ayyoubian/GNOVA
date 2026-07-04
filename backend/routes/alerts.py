"""Rate alert routes"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from models import RateAlertRequest
from deps import get_current_user
from database import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/rate")
async def create_rate_alert(
    request: RateAlertRequest,
    user: dict = Depends(get_current_user)
):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.from_asset,))
        from_asset = await cursor.fetchone()
        cursor = await db.execute("SELECT id FROM assets WHERE code = ?", (request.to_asset,))
        to_asset = await cursor.fetchone()

        if not from_asset or not to_asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO rate_alerts
            (id, user_id, from_asset_id, to_asset_id, target_rate, condition, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (alert_id, user["id"], from_asset["id"], to_asset["id"],
              request.target_rate, request.condition, now))
        await db.commit()

        return {"success": True, "alert_id": alert_id, "message": "هشدار نرخ ایجاد شد"}
    finally:
        await db.close()


@router.get("")
async def get_rate_alerts(user: dict = Depends(get_current_user)):
    db = await get_db()
    try:
        cursor = await db.execute("""
            SELECT
                ra.id, fa.code as from_asset, ta.code as to_asset,
                ra.target_rate, ra.condition, ra.status, ra.created_at
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


@router.delete("/{alert_id}")
async def delete_rate_alert(alert_id: str, user: dict = Depends(get_current_user)):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE rate_alerts SET status='deleted' WHERE id=? AND user_id=?",
            (alert_id, user["id"])
        )
        await db.commit()
        return {"success": True}
    finally:
        await db.close()

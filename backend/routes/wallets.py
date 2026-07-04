"""Wallet and transaction routes"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from deps import get_current_user
from ledger_service import LedgerService
from rate_service import RateService

router = APIRouter(tags=["wallets"])


@router.get("/wallets")
async def get_wallets(user: dict = Depends(get_current_user)):
    """Get user wallet balances with live-rate valuation"""
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
        amount_display = amount / (10 ** precision) if precision > 0 else amount

        result["balances"].append({
            "asset_code": bal["asset_code"],
            "asset_name": bal["asset_name"],
            "balance_minor": amount,
            "balance_display": amount_display,
            "decimal_precision": precision
        })

        code = bal["asset_code"]
        if code in ("IRR", "CREDIT"):
            result["total_value_irr"] += amount
        elif amount > 0:
            rate = await RateService.get_rate(code, "IRR")
            result["total_value_irr"] += int((amount / (10 ** precision)) * rate)

    return result


@router.get("/transactions")
async def get_transactions(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    history = await LedgerService.get_transaction_history(
        user_id=user["id"], limit=limit, offset=offset
    )
    return {"transactions": history, "total": len(history), "limit": limit, "offset": offset}

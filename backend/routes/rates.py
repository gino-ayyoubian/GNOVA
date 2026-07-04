"""Live exchange rate routes"""

from fastapi import APIRouter
from datetime import datetime, timezone
from rate_service import RateService

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("")
async def get_current_rates():
    rates = await RateService.get_all_rates()
    return {"rates": rates, "updated_at": datetime.now(timezone.utc).isoformat()}


@router.get("/{from_asset}/{to_asset}")
async def get_specific_rate(from_asset: str, to_asset: str):
    rate = await RateService.get_rate(from_asset.upper(), to_asset.upper())
    return {
        "from": from_asset.upper(),
        "to": to_asset.upper(),
        "rate": rate,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

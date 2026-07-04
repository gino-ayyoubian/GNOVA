"""
GNOVA Rate Service - Live Exchange Rates
Primary: Nobitex (Iranian exchange) for IRR pairs
Fallback: CoinGecko (USD pairs) with manual IRR conversion
Caches rates for 30 seconds to reduce API calls
"""

import aiohttp
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Cache structure: {pair: {"rate": float, "fetched_at": datetime}}
_rate_cache: Dict[str, Dict] = {}
CACHE_TTL_SECONDS = 30

# Fallback rates (used if all APIs fail)
FALLBACK_RATES = {
    ("USDT", "IRR"): 65000,
    ("IRR", "USDT"): 1 / 65000,
    ("BTC", "IRR"): 2850000000,
    ("IRR", "BTC"): 1 / 2850000000,
    ("USDT", "BTC"): 1 / 43846,
    ("BTC", "USDT"): 43846,
    ("CREDIT", "USDT"): 1 / 65000,
    ("USDT", "CREDIT"): 65000,
    ("CREDIT", "BTC"): 1 / 2850000000,
    ("BTC", "CREDIT"): 2850000000,
    ("CREDIT", "IRR"): 1,
    ("IRR", "CREDIT"): 1,
}


class RateService:
    """Fetch live exchange rates"""
    
    @staticmethod
    async def get_nobitex_rate(src: str, dst: str = "rls") -> Optional[float]:
        """
        Fetch rate from Nobitex (Iranian exchange)
        Returns: IRR per 1 unit of src (e.g., USDT->IRR = 65000)
        """
        try:
            url = "https://apiv2.nobitex.ir/market/stats"
            params = {"srcCurrency": src.lower(), "dstCurrency": dst.lower()}
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=params) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    
                    # Parse Nobitex response
                    # stats: {"btc-rls": {"latest": "...", "bestSell": "...", ...}}
                    stats = data.get("stats", {})
                    pair_key = f"{src.lower()}-{dst.lower()}"
                    pair_data = stats.get(pair_key)
                    
                    if pair_data and "latest" in pair_data:
                        # Nobitex returns price in rials (rls)
                        # Convert rls to toman if needed (1 toman = 10 rials)
                        rate_rls = float(pair_data["latest"])
                        # Return in IRR (rial)
                        return rate_rls
                    
                    return None
        except Exception as e:
            logger.warning(f"Nobitex API error for {src}->{dst}: {e}")
            return None
    
    @staticmethod
    async def get_coingecko_rate(coin_id: str, vs_currency: str = "usd") -> Optional[float]:
        """
        Fetch rate from CoinGecko (USD pairs)
        coin_id: 'bitcoin', 'tether', etc.
        Returns: price in vs_currency
        """
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": coin_id, "vs_currencies": vs_currency}
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    return data.get(coin_id, {}).get(vs_currency)
        except Exception as e:
            logger.warning(f"CoinGecko API error for {coin_id}: {e}")
            return None
    
    @staticmethod
    def _normalize_asset(asset: str) -> str:
        """Normalize CREDIT as IRR equivalent"""
        return "IRR" if asset == "CREDIT" else asset

    @staticmethod
    def _get_cached_rate(cache_key: str) -> Optional[float]:
        """Return a cached rate if it exists and has not expired"""
        cached = _rate_cache.get(cache_key)
        if not cached:
            return None
        age = (datetime.now(timezone.utc) - cached["fetched_at"]).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return cached["rate"]
        return None

    @staticmethod
    def _set_cached_rate(cache_key: str, rate: float):
        """Store a rate in the cache"""
        _rate_cache[cache_key] = {
            "rate": rate,
            "fetched_at": datetime.now(timezone.utc)
        }

    @staticmethod
    async def _fetch_rate_to_irr(from_asset: str) -> Optional[float]:
        """Fetch asset -> IRR rate via Nobitex (e.g., USDT -> IRR)"""
        return await RateService.get_nobitex_rate(from_asset, "rls")

    @staticmethod
    async def _fetch_rate_from_irr(to_asset: str) -> Optional[float]:
        """Fetch IRR -> asset rate (inverse of asset -> IRR via Nobitex)"""
        asset_to_irr = await RateService.get_nobitex_rate(to_asset, "rls")
        if asset_to_irr and asset_to_irr > 0:
            return 1 / asset_to_irr
        return None

    @staticmethod
    async def _fetch_crypto_cross_rate(from_asset: str, to_asset: str) -> Optional[float]:
        """Fetch crypto-to-crypto rate via CoinGecko USD prices (e.g., BTC -> USDT)"""
        coin_map = {"BTC": "bitcoin", "USDT": "tether"}
        from_id = coin_map.get(from_asset)
        to_id = coin_map.get(to_asset)

        if not from_id or not to_id:
            return None

        from_usd = await RateService.get_coingecko_rate(from_id, "usd")
        to_usd = await RateService.get_coingecko_rate(to_id, "usd")
        if from_usd and to_usd and to_usd > 0:
            return from_usd / to_usd
        return None

    @staticmethod
    async def _fetch_live_rate(from_asset: str, to_asset: str) -> Optional[float]:
        """Pick and run the correct rate-fetching strategy for the pair"""
        if to_asset == "IRR":
            return await RateService._fetch_rate_to_irr(from_asset)
        if from_asset == "IRR":
            return await RateService._fetch_rate_from_irr(to_asset)
        return await RateService._fetch_crypto_cross_rate(from_asset, to_asset)

    @staticmethod
    def _get_fallback_rate(from_asset: str, to_asset: str) -> float:
        """Return hardcoded fallback rate for the pair"""
        rate = FALLBACK_RATES.get((from_asset, to_asset), 1.0)
        logger.warning(f"Using fallback rate for {from_asset}->{to_asset}: {rate}")
        return rate

    @staticmethod
    async def get_rate(from_asset: str, to_asset: str) -> float:
        """
        Get exchange rate from from_asset to to_asset.
        Returns: how many to_asset you get for 1 from_asset
        Uses cache, Nobitex (primary), CoinGecko (fallback), hardcoded (last resort)
        """
        from_normalized = RateService._normalize_asset(from_asset)
        to_normalized = RateService._normalize_asset(to_asset)

        if from_normalized == to_normalized:
            return 1.0

        cache_key = f"{from_normalized}_{to_normalized}"
        cached_rate = RateService._get_cached_rate(cache_key)
        if cached_rate is not None:
            return cached_rate

        rate = await RateService._fetch_live_rate(from_normalized, to_normalized)

        if rate is None:
            rate = RateService._get_fallback_rate(from_normalized, to_normalized)

        RateService._set_cached_rate(cache_key, rate)
        return rate
    
    @staticmethod
    async def get_all_rates() -> Dict:
        """Get current rates for all supported pairs"""
        pairs = [
            ("USDT", "IRR"),
            ("BTC", "IRR"),
            ("BTC", "USDT"),
        ]
        
        results = {}
        tasks = [RateService.get_rate(s, d) for s, d in pairs]
        rates = await asyncio.gather(*tasks)
        
        for (src, dst), rate in zip(pairs, rates):
            results[f"{src}_{dst}"] = {
                "from": src,
                "to": dst,
                "rate": rate,
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
        
        return results

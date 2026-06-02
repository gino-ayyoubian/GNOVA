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
    async def get_rate(from_asset: str, to_asset: str) -> float:
        """
        Get exchange rate from from_asset to to_asset.
        Returns: how many to_asset you get for 1 from_asset
        Uses cache, Nobitex (primary), CoinGecko (fallback), hardcoded (last resort)
        """
        # Normalize CREDIT as IRR equivalent
        from_normalized = "IRR" if from_asset == "CREDIT" else from_asset
        to_normalized = "IRR" if to_asset == "CREDIT" else to_asset
        
        if from_normalized == to_normalized:
            return 1.0
        
        # Check cache
        cache_key = f"{from_normalized}_{to_normalized}"
        cached = _rate_cache.get(cache_key)
        if cached:
            age = (datetime.now(timezone.utc) - cached["fetched_at"]).total_seconds()
            if age < CACHE_TTL_SECONDS:
                return cached["rate"]
        
        rate = None
        
        # Try Nobitex for IRR pairs
        if to_normalized == "IRR":
            # USDT -> IRR, BTC -> IRR
            nobitex_rate = await RateService.get_nobitex_rate(from_normalized, "rls")
            if nobitex_rate:
                rate = nobitex_rate
        elif from_normalized == "IRR":
            # IRR -> USDT, IRR -> BTC (inverse of asset -> IRR)
            asset_to_irr = await RateService.get_nobitex_rate(to_normalized, "rls")
            if asset_to_irr and asset_to_irr > 0:
                rate = 1 / asset_to_irr
        else:
            # Crypto-to-crypto (e.g., BTC -> USDT)
            coin_map = {"BTC": "bitcoin", "USDT": "tether"}
            from_id = coin_map.get(from_normalized)
            to_id = coin_map.get(to_normalized)
            
            if from_id and to_id:
                from_usd = await RateService.get_coingecko_rate(from_id, "usd")
                to_usd = await RateService.get_coingecko_rate(to_id, "usd")
                if from_usd and to_usd and to_usd > 0:
                    rate = from_usd / to_usd
        
        # Fallback to hardcoded rates
        if rate is None:
            fallback_key = (from_normalized, to_normalized)
            rate = FALLBACK_RATES.get(fallback_key, 1.0)
            logger.warning(f"Using fallback rate for {from_normalized}->{to_normalized}: {rate}")
        
        # Cache the rate
        _rate_cache[cache_key] = {
            "rate": rate,
            "fetched_at": datetime.now(timezone.utc)
        }
        
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

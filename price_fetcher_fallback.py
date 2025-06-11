import aiohttp
import asyncio
from typing import Dict, List, Optional

# Mapping từ CoinGecko ID sang symbol cho các API khác
COINGECKO_TO_SYMBOL = {
    "bitcoin": "BTC",
    "ethereum": "ETH", 
    "ripple": "XRP",
    "bitcoin-cash": "BCH",
    "litecoin": "LTC",
    "cardano": "ADA",
    "polkadot": "DOT",
    "chainlink": "LINK",
    "binancecoin": "BNB",
    "stellar": "XLM",
    "dogecoin": "DOGE",
    "tether": "USDT",
    "usd-coin": "USDC",
    "shiba-inu": "SHIB",
    "polygon": "MATIC",
    "solana": "SOL",
    "avalanche-2": "AVAX",
    "celestia": "TIA",
    "arbitrum": "ARB",
    "render-token": "RNDR",
    "ondo-finance": "ONDO",
    "mantra-dao": "OM",
    "pixels": "PIXEL",
    "jupiter": "JUP",
    "pendle": "PENDLE",
    "ace-casino": "ACE"
}

async def fetch_from_coingecko(coin_ids: List[str]) -> Dict[str, Dict]:
    """Lấy giá từ CoinGecko"""
    try:
        ids_str = ",".join(coin_ids)
        # Thêm include_market_cap=true
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = {}
                    for coin_id in coin_ids:
                        if coin_id in data:
                            result[coin_id] = {
                                "current_price": data[coin_id]["usd"],
                                "market_cap": data[coin_id].get("usd_market_cap", 0),
                                "price_change_24h": data[coin_id].get("usd_24h_change", 0)
                            }
                    print(f"CoinGecko fetched prices for {len(result)} coins")
                    return result
    except Exception as e:
        print(f"CoinGecko error: {e}")
    return {}

async def fetch_from_binance(symbols: List[str]) -> Dict[str, Dict]:
    """Lấy giá từ Binance (không cần API key)"""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = {}
                    
                    # Tạo mapping từ symbol sang data
                    binance_data = {item["symbol"]: item for item in data}
                    
                    for symbol in symbols:
                        # Thử với USDT pair trước
                        usdt_pair = f"{symbol}USDT"
                        if usdt_pair in binance_data:
                            item = binance_data[usdt_pair]
                            result[symbol] = {
                                "current_price": float(item["lastPrice"]),
                                "price_change_24h": float(item["priceChangePercent"])
                            }
                    
                    print(f"Binance fetched prices for {len(result)} symbols")
                    return result
    except Exception as e:
        print(f"Binance error: {e}")
    return {}

async def fetch_coin_prices_with_fallback(coin_ids: List[str]) -> Dict[str, Dict]:
    """
    Lấy giá từ nhiều nguồn với fallback
    1. CoinGecko (nguồn chính)
    2. Binance (fallback) 
    """
    print(f"Fetching prices for {len(coin_ids)} coins with fallback...")
    
    # Bước 1: Thử CoinGecko trước
    coingecko_prices = await fetch_from_coingecko(coin_ids)
    
    # Tìm các coin chưa có giá
    missing_coins = [coin_id for coin_id in coin_ids if coin_id not in coingecko_prices]
    
    if not missing_coins:
        print("All prices fetched from CoinGecko")
        return coingecko_prices
    
    print(f"Missing {len(missing_coins)} coins from CoinGecko, trying Binance...")
    
    # Chuyển đổi missing coins sang symbols
    missing_symbols = []
    coin_to_symbol_map = {}
    for coin_id in missing_coins:
        if coin_id in COINGECKO_TO_SYMBOL:
            symbol = COINGECKO_TO_SYMBOL[coin_id]
            missing_symbols.append(symbol)
            coin_to_symbol_map[symbol] = coin_id
    
    # Bước 2: Thử Binance
    binance_prices = await fetch_from_binance(missing_symbols)
    
    # Kết hợp kết quả
    final_result = coingecko_prices.copy()
    
    # Thêm giá từ Binance
    for symbol, price_data in binance_prices.items():
        if symbol in coin_to_symbol_map:
            coin_id = coin_to_symbol_map[symbol]
            final_result[coin_id] = price_data
    
    print(f"Final result: {len(final_result)} coins with prices")
    print(f"Sources used: CoinGecko({len(coingecko_prices)}), Binance({len(binance_prices)})")
    
    return final_result

class price_fetcher_fallback:
    @staticmethod
    async def fetch_coin_prices_with_fallback(coin_ids):
        print(f"Mock fetch_coin_prices_with_fallback called with {coin_ids}")
        return {coin_id: {"current_price": 0} for coin_id in coin_ids}  # Trả về giá = 0
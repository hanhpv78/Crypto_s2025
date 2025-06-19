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
    """Lấy giá từ CoinGecko với rate limit handling"""
    try:
        # Thêm delay để tránh rate limit
        await asyncio.sleep(1.0)
        
        ids_str = ",".join(coin_ids)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
        
        # Headers để tránh rate limit
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        timeout = aiohttp.ClientTimeout(total=20)  # Tăng timeout
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                print(f"CoinGecko response status: {response.status}")
                
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
                    print(f"✅ CoinGecko fetched {len(result)} coins")
                    return result
                elif response.status == 429:
                    print("⚠️ CoinGecko rate limit, fallback to Binance")
                    return {}
                else:
                    print(f"❌ CoinGecko error: {response.status}")
                    return {}
    except Exception as e:
        print(f"❌ CoinGecko exception: {e}")
    return {}

async def fetch_from_binance(coin_ids: List[str]) -> Dict[str, Dict]:
    """Lấy giá từ Binance cho fallback"""
    try:
        await asyncio.sleep(0.5)  # Rate limit protection
        
        url = "https://api.binance.com/api/v3/ticker/24hr"
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = {}
                    
                    # Tạo mapping từ CoinGecko ID sang Binance symbols
                    for coin_id in coin_ids:
                        symbol = COINGECKO_TO_SYMBOL.get(coin_id, "").upper()
                        if symbol:
                            # Tìm symbol trong Binance data
                            for item in data:
                                if item.get("symbol") == f"{symbol}USDT":
                                    result[coin_id] = {
                                        "current_price": float(item["lastPrice"]),
                                        "market_cap": 0,  # Binance không có market cap
                                        "price_change_24h": float(item["priceChangePercent"])
                                    }
                                    break
                    
                    print(f"✅ Binance fetched {len(result)} coins")
                    return result
                else:
                    print(f"❌ Binance error: {response.status}")
    except Exception as e:
        print(f"❌ Binance exception: {e}")
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

def get_potential_coins_with_live_prices():
    """Get potential coins with live prices"""
    try:
        potential_data = get_potential_coins()
        
        if not potential_data:
            return []
        
        # Lấy coin IDs từ potential coins
        coin_ids = [coin.get("Coin ID", "") for coin in potential_data if coin.get("Coin ID")]
        
        if coin_ids:
            # Fetch live prices
            live_prices = fetch_current_prices(coin_ids)
            
            # Update prices
            for coin in potential_data:
                coin_id = coin.get("Coin ID", "").lower()
                if coin_id in live_prices:
                    price_data = live_prices[coin_id]
                    coin["Current Price"] = price_data.get("current_price", 0)
                    coin["Market Cap"] = price_data.get("market_cap", 0)
                    coin["Price Change 24h"] = price_data.get("price_change_24h", 0)
        
        return potential_data
        
    except Exception as e:
        print(f"Error getting potential coins with live prices: {e}")
        return get_potential_coins()

def fetch_current_prices(coin_ids):
    """
    Wrapper function for compatibility with data_access.py
    """
    import asyncio
    
    try:
        # Event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Gọi async function chính
        result = loop.run_until_complete(
            fetch_coin_prices_with_fallback(coin_ids)
        )
        
        return result
        
    except Exception as e:
        print(f"Error in fetch_current_prices: {e}")
        # Fallback prices
        fallback = {}
        price_map = {"bitcoin": 67000, "ethereum": 3200, "cardano": 0.52, "solana": 140}
        
        for coin_id in coin_ids:
            fallback[coin_id] = {
                "current_price": price_map.get(coin_id, 1.0),
                "market_cap": 1000000000,
                "price_change_24h": 2.5
            }
        
        return fallback

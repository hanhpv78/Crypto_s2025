import os
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import requests
import asyncio
import aiohttp

def get_google_sheets_client():
    """Kết nối Google Sheets using Streamlit secrets"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        if not hasattr(st, 'secrets') or 'gcp_service_account' not in st.secrets:
            st.error("❌ No Google credentials found in secrets")
            return None
        
        service_account_info = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(
            service_account_info, 
            scopes=scopes
        )
        
        return gspread.authorize(credentials)
        
    except Exception as e:
        st.error(f"❌ Google Sheets connection failed: {str(e)}")
        return None

def get_tier1_googlesheet_data(spreadsheet_url):
    """Load data from Tier1_Real_Time sheet"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
            
        # Mở spreadsheet
        sheet = client.open_by_url(spreadsheet_url)
        
        # Tìm sheet Tier1_Real_Time
        try:
            worksheet = sheet.worksheet("Tier1_Real_Time")
        except gspread.WorksheetNotFound:
            st.error("❌ Sheet 'Tier1_Real_Time' not found")
            return pd.DataFrame()
        
        # Lấy data
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            st.warning("⚠️ No data found in Tier1_Real_Time sheet")
            return pd.DataFrame()
            
        st.success(f"✅ Loaded {len(df)} rows from Tier1_Real_Time @google sheet")
        return df
        
    except Exception as e:
        st.error(f"❌ Failed to load from Tier1_Real_Time: {str(e)}")
        return pd.DataFrame()

def append_to_tier1_realtime(new_data, spreadsheet_url):
    """Append new data to Tier1_Real_Time sheet"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        

        # Convert data to string format
        if isinstance(new_data, pd.DataFrame):
            # Convert all columns to string
            new_data_clean = new_data.copy()
            for col in new_data_clean.columns:
                new_data_clean[col] = new_data_clean[col].astype(str)
            values = new_data_clean.values.tolist()
        else:
            # Convert each value to string
            values = [[str(cell) for cell in row] for row in new_data]
            
        # Append data
        worksheet.append_rows(values)
        st.success(f"✅ Appended {len(values)} rows to Tier1_Real_Time")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to append data: {str(e)}")
        return False

def update_tier1_realtime_full(df, spreadsheet_url):
    """Update entire Tier1_Real_Time sheet with new data"""
    try:
        # Kiểm tra input
        if not isinstance(df, pd.DataFrame):
            st.error(f"❌ Expected DataFrame, got {type(df)}")
            return False
            
        if df.empty:
            st.warning("⚠️ DataFrame is empty")
            return False
        
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        
        # Clear existing data
        worksheet.clear()
        
        # Convert DataFrame to safe format
        df_clean = df.copy()
        
        # Handle NaN values and convert to string
        df_clean = df_clean.fillna('')
        
        # Convert all values to string safely
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str)
        
        # Prepare data
        headers = df_clean.columns.tolist()
        rows = df_clean.values.tolist()
        
        # Final safety check - ensure all are strings
        clean_headers = [str(h) for h in headers]
        clean_rows = []
        for row in rows:
            clean_row = [str(cell) for cell in row]
            clean_rows.append(clean_row)
        
        # Combine
        all_data = [clean_headers] + clean_rows
        
        # Update sheet
        worksheet.update('A1', all_data)
        st.success(f"✅ Updated Tier1_Real_Time with {len(df)} rows")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to update sheet: {str(e)}")
        import traceback
        st.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def append_live_data_to_tier1(new_df, spreadsheet_url):
    """Append new live data to Tier1_Real_Time sheet (không xóa data cũ)"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        
        if new_df.empty:
            st.warning("⚠️ No new data to append")
            return False
        
        # Convert to string format
        df_clean = new_df.copy()
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('').astype(str)
        
        # Get data as rows (không include headers vì đã có trong sheet)
        rows = df_clean.values.tolist()
        
        # Convert to strings
        clean_rows = []
        for row in rows:
            clean_row = [str(cell) for cell in row]
            clean_rows.append(clean_row)
        
        # Append to sheet (không xóa data cũ)
        worksheet.append_rows(clean_rows)
        st.success(f"✅ Appended {len(clean_rows)} new rows to Tier1_Real_Time")
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to append data: {str(e)}")
        return False

# Backward compatibility - giữ tên cũ
def get_universe_data(spreadsheet_url):
    """Alias for get_tier1_googlesheet_data"""
    return get_tier1_googlesheet_data(spreadsheet_url)

def export_tier1_to_existing_gsheet(data, spreadsheet_url):
    """Alias for update_tier1_realtime_full"""
    return update_tier1_realtime_full(data, spreadsheet_url)

def load_tier1_universe_from_gsheet(spreadsheet_url):
    """Alias for get_tier1_googlesheet_data"""
    return get_tier1_googlesheet_data(spreadsheet_url)

def export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export):
    """Append new data to Google Sheets with duplicate detection"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.worksheet("Tier1_Real_Time")
        
        # Get existing data
        existing_data = worksheet.get_all_records()
        existing_df = pd.DataFrame(existing_data)
        
        # New data
        new_df = pd.DataFrame(data_to_export[1:], columns=data_to_export[0])
        
        if existing_df.empty:
            # Empty sheet, add headers + all data
            all_data = [data_to_export[0]] + data_to_export[1:]
            worksheet.update(all_data)
            st.success(f"✅ Added {len(data_to_export[1:])} rows to empty sheet")
        else:
            # Check for duplicates (by symbol và timestamp)
            if 'Symbol' in new_df.columns and 'Last_Updated' in new_df.columns:
                # Filter out duplicates
                new_df['timestamp_check'] = new_df['Last_Updated'].astype(str)
                existing_df['timestamp_check'] = existing_df['Last_Updated'].astype(str)
                
                # Find truly new rows
                merged = new_df.merge(
                    existing_df[['Symbol', 'timestamp_check']], 
                    on=['Symbol', 'timestamp_check'], 
                    how='left', 
                    indicator=True
                )
                truly_new = merged[merged['_merge'] == 'left_only']
                
                if not truly_new.empty:
                    # Remove merge column
                    truly_new = truly_new.drop(['_merge', 'timestamp_check'], axis=1)
                    
                    # Append only new rows
                    new_rows = truly_new.values.tolist()
                    worksheet.append_rows(new_rows)
                    
                    st.success(f"✅ Appended {len(new_rows)} new rows (filtered duplicates)")
                    st.info(f"📊 Skipped {len(new_df) - len(new_rows)} duplicate rows")
                else:
                    st.warning("⚠️ All data already exists - no new rows added")
            else:
                # No duplicate detection, just append all
                new_rows = new_df.values.tolist()
                worksheet.append_rows(new_rows)
                st.success(f"✅ Appended {len(new_rows)} rows (no duplicate check)")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Append failed: {e}")
        return False

COINGECKO_ID_TO_SYMBOL = {}
SYMBOL_TO_COINGECKO_ID = {}

# Mapping từ CoinGecko id sang symbol (bạn nên build mapping này đầy đủ)
def build_coingecko_id_symbol_map():
    url = "https://api.coingecko.com/api/v3/coins/list"
    resp = requests.get(url)
    data = resp.json()
    return {item["id"]: item["symbol"].upper() for item in data}

COINGECKO_ID_TO_SYMBOL = build_coingecko_id_symbol_map()
SYMBOL_TO_COINGECKO_ID = {v: k for k, v in COINGECKO_ID_TO_SYMBOL.items()}

# 1. Lấy danh sách coin đạt chuẩn từ CoinGecko
def fetch_coingecko_universe(min_market_cap=2e9, min_volume=5e7):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": False
    }
    coins = []
    for page in range(1, 10):  # Lấy tối đa 2500 coin
        params["page"] = page
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        coins.extend(data)
    df = pd.DataFrame(coins)
    print(f"[DEBUG] Tổng số coin lấy từ CoinGecko: {len(df)}")
    # Lọc theo market cap và volume
    df = df[
        (df["market_cap"] > min_market_cap) &
        (df["total_volume"] > min_volume)
    ]
    print(f"[DEBUG] Số coin đạt chuẩn (market cap > 2B, volume > 50M): {len(df)}")
    print(df)
    df["source"] = "coingecko"
    return df[["id", "symbol", "name", "market_cap", "total_volume", "current_price", "source"]].reset_index(drop=True)

# 2. Lấy giá từ CoinGecko (async)
async def fetch_from_coingecko(coin_ids):
    await asyncio.sleep(1.0)
    ids_str = ",".join(coin_ids)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    }
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                result = {}
                for coin_id in coin_ids:
                    if coin_id in data:
                        result[coin_id] = {
                            "current_price": data[coin_id].get("usd", 0),
                            "market_cap": data[coin_id].get("usd_market_cap", 0),
                            "price_change_24h": data[coin_id].get("usd_24h_change", 0)
                        }
                return result
            return {}

# 3. Lấy giá từ Binance (async)
async def fetch_from_binance(symbols):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                result = {}
                for symbol in symbols:
                    for item in data:
                        if item.get("symbol") == f"{symbol}USDT":
                            result[symbol] = {
                                "current_price": float(item["lastPrice"]),
                                "market_cap": 0,
                                "price_change_24h": float(item["priceChangePercent"])
                            }
                            break
                return result
            return {}

# 4. Fallback lấy giá (async)
async def fetch_coin_prices_with_fallback(coin_ids):
    coingecko_prices = await fetch_from_coingecko(coin_ids)
    missing_ids = [cid for cid in coin_ids if cid not in coingecko_prices]
    missing_symbols = [COINGECKO_ID_TO_SYMBOL.get(cid, "").upper() for cid in missing_ids if cid in COINGECKO_ID_TO_SYMBOL]
    binance_prices = await fetch_from_binance(missing_symbols) if missing_symbols else {}
    final_result = coingecko_prices.copy()
    for cid, symbol in zip(missing_ids, missing_symbols):
        if symbol in binance_prices:
            final_result[cid] = binance_prices[symbol]
    return final_result

# 5. Wrapper sync cho Streamlit
def fetch_current_prices(coin_ids):
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_coin_prices_with_fallback(coin_ids))
        return result
    except Exception as e:
        print(f"Error in fetch_current_prices: {e}")
        return {}

# 6. Hàm tổng hợp: lấy universe đạt chuẩn và giá mới nhất
def get_tier1_universe_from_sources():
    df = fetch_coingecko_universe()
    coin_ids = df["id"].tolist()
    price_data = fetch_current_prices(coin_ids)
    # Cập nhật giá mới nhất vào DataFrame
    df["current_price"] = df["id"].map(lambda cid: price_data.get(cid, {}).get("current_price", 0))
    df["market_cap"] = df["id"].map(lambda cid: price_data.get(cid, {}).get("market_cap", 0))
    df["price_change_24h"] = df["id"].map(lambda cid: price_data.get(cid, {}).get("price_change_24h", 0))
    return df.reset_index(drop=True)

# Ví dụ sử dụng:
if __name__ == "__main__":
    df = get_tier1_universe_from_sources()
    print(df.head())
    print(f"Tổng số coin đạt chuẩn: {len(df)}")

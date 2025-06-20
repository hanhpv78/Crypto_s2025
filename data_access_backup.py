import os
import gspread
import json
from google.oauth2.service_account import Credentials  # ← Đúng import
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import numpy as np

# Import mapping từ file riêng (nếu có)
try:
    from coin_mapping import TICKER_TO_ID_MAPPING
except ImportError:
    TICKER_TO_ID_MAPPING = {}

def get_google_sheets_client():
    """Kết nối Google Sheets using Streamlit secrets"""
    client = None  # Khởi tạo biến
    
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Kiểm tra secrets
        if not hasattr(st, 'secrets'):
            st.error("❌ No Streamlit secrets found")
            return None
            
        if 'gcp_service_account' not in st.secrets:
            st.error("❌ No gcp_service_account in secrets")
            return None
        
        # Lấy service account info
        service_account_info = dict(st.secrets["gcp_service_account"])
        
        # Tạo credentials
        creds = Credentials.from_service_account_info(
            service_account_info, 
            scopes=scopes
        )
        
        # Authorize
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        st.error(f"❌ Google Sheets connection failed: {str(e)}")
        return None

def clean_numeric_value(value):
    """Clean numeric values for Google Sheets"""
    if pd.isna(value) or value is None:
        return 0
    if np.isinf(value):
        return 0
    if isinstance(value, (int, float)):
        if abs(value) > 1e15:
            return int(value / 1e9)
        return float(value)
    try:
        return float(value)
    except:
        return 0

def export_tier1_to_existing_gsheet(spreadsheet_url: str, data: list = None) -> bool:
    """Export data to existing Google Sheet with proper data cleaning"""
    try:
        client = get_google_sheets_client()
        if not client:
            return False
        
        # Extract spreadsheet ID from URL
        sheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = client.open_by_key(sheet_id)
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet("Tier1_Real_Time")
        except:
            worksheet = spreadsheet.add_worksheet("Tier1_Real_Time", rows=1000, cols=20)
        
        # Clear existing data
        worksheet.clear()
        
        # Clean and prepare data
        if data and len(data) > 1:
            cleaned_data = []
            header = data[0]
            cleaned_data.append(header)
            for row in data[1:]:
                cleaned_row = []
                for i, cell in enumerate(row):
                    if i in [2, 3, 4, 5, 6, 7, 8]:  # Price, Market_Cap, Change columns, Volume, Rank
                        cleaned_row.append(clean_numeric_value(cell))
                    else:
                        cleaned_row.append(str(cell) if cell is not None else "")
                cleaned_data.append(cleaned_row)
            worksheet.update('A1', cleaned_data)
            worksheet.format('A1:Z1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}}
            })
            st.success(f"✅ Successfully exported {len(cleaned_data)-1} coins to Google Sheet")
            return True
        else:
            st.warning("⚠️ No valid data to export")
            return False
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")
        return False

# Khởi tạo các biến sheet là None để tránh lỗi khi không kết nối được
portfolio_sheet = None
potential_coins_sheet = None
notification_settings_sheet = None
spreadsheet = None

try:
    # Khởi tạo client với thông tin từ file
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)

    # Hiển thị email service account để người dùng kiểm tra
    with open(creds_file, 'r') as f:
        credentials = json.load(f)
    print(f"Using service account: {credentials['client_email']}")

    # Mở spreadsheet
    spreadsheet = client.open("CryptoInvestmentDB")

    # Lấy các sheet
    portfolio_sheet = spreadsheet.worksheet("Portfolio")
    potential_coins_sheet = spreadsheet.worksheet("PotentialCoins")
    notification_settings_sheet = spreadsheet.worksheet("NotificationSettings")
    
    print(f"Connected to Google Sheet: {spreadsheet.title}")
    
except Exception as e:
    print(f"❌ Google Sheets connection error: {e}")
    # Cho phép app chạy tiếp với sample data

# ==================== DATA ACCESS FUNCTIONS ====================

# Sửa function get_portfolio để check live prices

def get_portfolio():
    """Get portfolio data with live prices option"""
    try:
        # Check if live prices requested
        use_live = False
        try:
            import streamlit as st
            use_live = st.session_state.get('use_live_prices', False)
            print(f"📊 Use live prices: {use_live}")
        except Exception:
            pass
        
        if use_live:
            print("🔄 Getting portfolio with live prices...")
            return get_portfolio_with_live_prices()
        
        # Normal flow - get from Google Sheets
        if portfolio_sheet is not None:
            try:
                print("📊 Loading portfolio from Google Sheets...")
                records = portfolio_sheet.get_all_records()
                print(f"✅ Loaded {len(records)} portfolio records")
                return records
            except Exception as e:
                print(f"❌ Google Sheets error: {e}")
        
        # Fallback sample data
        print("📝 Using sample portfolio data")
        return [
            {"Coin Name": "Bitcoin", "Coin ID": "BTC", "Quantity": 0.5, "Avg Buy Price": 45000, "Current Price": 47000, "Current Value": 23500, "P&L": 1000, "ROI %": 4.44},
            {"Coin Name": "Ethereum", "Coin ID": "ETH", "Quantity": 2, "Avg Buy Price": 3000, "Current Price": 3200, "Current Value": 6400, "P&L": 400, "ROI %": 6.67},
            {"Coin Name": "Cardano", "Coin ID": "ADA", "Quantity": 1000, "Avg Buy Price": 0.45, "Current Price": 0.52, "Current Value": 520, "P&L": 70, "ROI %": 15.56}
        ]
        
    except Exception as e:
        print(f"❌ Error in get_portfolio: {e}")
        return []

def get_potential_coins():
    if potential_coins_sheet is not None:
        try:
            records = potential_coins_sheet.get_all_records()
            if records:  # Nếu có data từ Google Sheets
                return records
        except Exception as e:
            print(f"Error reading potential coins: {e}")
    
    # Sample data nếu không có Google Sheets hoặc sheet trống
    return [
        {
            "Coin ID": "solana",
            "Coin Name": "Solana", 
            "Current Price": 0,  # Sẽ được update bởi live prices
            "Market Cap": 0,
            "Recommendation": "BUY",
            "Date Added": "2025-06-10",
            "Reason": "Strong ecosystem growth and DeFi adoption"
        },
        {
            "Coin ID": "polkadot", 
            "Coin Name": "Polkadot",
            "Current Price": 0,
            "Market Cap": 0,
            "Recommendation": "HOLD",
            "Date Added": "2025-06-08", 
            "Reason": "Waiting for parachain development progress"
        },
        {
            "Coin ID": "chainlink",
            "Coin Name": "Chainlink",
            "Current Price": 0,
            "Market Cap": 0,
            "Recommendation": "BUY",
            "Date Added": "2025-06-05",
            "Reason": "Oracle market leader with expanding partnerships"
        }
    ]

def get_notification_settings():
    if notification_settings_sheet is not None:
        try:
            return notification_settings_sheet.get_all_records()
        except Exception as e:
            print(f"Error reading notification settings: {e}")
    return []

def append_historical_price(coin_id, date, price, market_cap=0):
    """
    Ghi một dòng dữ liệu vào sheet 'historicals_price' với market cap.
    """
    if spreadsheet is None:
        print("❌ No spreadsheet connection.")
        return
    try:
        historical_sheet = spreadsheet.worksheet("historicals_price")
        historical_sheet.append_row([coin_id, date, price, market_cap])
        print(f"✅ Saved {coin_id}: ${price} (MC: ${market_cap:,.0f}) on {date}")
    except Exception as e:
        print(f"❌ Error saving historical price for {coin_id}: {e}")
        # Thử tạo sheet nếu chưa có
        try:
            new_sheet = spreadsheet.add_worksheet(title="historicals_price", rows="1000", cols="10")
            new_sheet.update('A1:D1', [["Coin ID", "Date", "Price", "Market Cap"]])
            new_sheet.append_row([coin_id, date, price, market_cap])
            print(f"✅ Created new sheet and saved {coin_id}: ${price}")
        except Exception as e2:
            print(f"❌ Failed to create sheet: {e2}")

def update_portfolio_prices(prices):
    """Cập nhật giá hiện tại và market cap cho portfolio - batch update"""
    if portfolio_sheet is None:
        print("❌ No portfolio sheet connection.")
        return
    try:
        portfolio_data = portfolio_sheet.get_all_records()
        updates = []
        for i, row in enumerate(portfolio_data, start=2):
            coin_id = row.get("Coin ID", "").lower()
            if coin_id in prices:
                current_price = prices[coin_id].get("current_price", 0)
                market_cap = prices[coin_id].get("market_cap", 0)
                updates.append({'range': f'E{i}', 'values': [[current_price]]})
                updates.append({'range': f'G{i}', 'values': [[market_cap]]})
                quantity = row.get("Quantity", 0)
                if quantity and isinstance(quantity, (int, float)) and quantity > 0:
                    total_value = float(quantity) * float(current_price)
                    updates.append({'range': f'F{i}', 'values': [[total_value]]})
        if updates:
            portfolio_sheet.batch_update(updates[:20])  # Limit to 20 updates per batch
            print(f"✅ Updated {min(len(updates), 20)} portfolio cells")
    except Exception as e:
        print(f"❌ Error updating portfolio prices: {e}")

def update_potential_coin_prices(prices):
    """Cập nhật giá hiện tại và market cap cho potential coins - batch update"""
    if potential_coins_sheet is None:
        print("❌ No potential coins sheet connection.")
        return
    try:
        potential_data = potential_coins_sheet.get_all_records()
        updates = []
        for i, row in enumerate(potential_data, start=2):
            coin_id = row.get("Coin ID", "").lower()
            if coin_id in prices:
                current_price = prices[coin_id].get("current_price", 0)
                market_cap = prices[coin_id].get("market_cap", 0)
                updates.append({'range': f'C{i}', 'values': [[current_price]]})
                updates.append({'range': f'D{i}', 'values': [[market_cap]]})
        if updates:
            potential_coins_sheet.batch_update(updates[:20])  # Limit to 20 updates per batch
            print(f"✅ Updated {min(len(updates), 20)} potential coin cells")
    except Exception as e:
        print(f"❌ Error updating potential coin prices: {e}")

def save_notification_settings(coin_id, coin_name, desired_buy_price, desired_sell_price, buy_threshold_percent, sell_threshold_percent, email):
    if notification_settings_sheet is None:
        print("❌ No notification settings sheet connection.")
        return
    records = notification_settings_sheet.get_all_records()
    for i, record in enumerate(records, start=2):
        if record["Coin ID"] == coin_id:
            notification_settings_sheet.update_cell(i, 2, coin_name)
            notification_settings_sheet.update_cell(i, 3, desired_buy_price)
            notification_settings_sheet.update_cell(i, 4, desired_sell_price)
            notification_settings_sheet.update_cell(i, 5, buy_threshold_percent)
            notification_settings_sheet.update_cell(i, 6, sell_threshold_percent)
            notification_settings_sheet.update_cell(i, 7, email)
            return
    # New entry
    notification_settings_sheet.append_row([
        coin_id, coin_name, desired_buy_price, desired_sell_price,
        buy_threshold_percent, sell_threshold_percent, email, 0, 0
    ])

def add_portfolio_entry(coin_id, coin_name, quantity, avg_buy_price):
    if portfolio_sheet is not None:
        portfolio_sheet.append_row([
            coin_id, coin_name, quantity, avg_buy_price, 0, 0
        ])

def add_potential_coin(coin_id, coin_name, recommendation, reason):
    if potential_coins_sheet is not None:
        potential_coins_sheet.append_row([
            coin_id, coin_name, 0, recommendation, datetime.now().strftime("%Y-%m-%d"), reason
        ])

def update_notification_status(coin_id, last_buy_price, last_sell_price):
    if notification_settings_sheet is None:
        return
    records = notification_settings_sheet.get_all_records()
    for i, record in enumerate(records, start=2):
        if record["Coin ID"] == coin_id:
            notification_settings_sheet.update_cell(i, 8, last_buy_price)
            notification_settings_sheet.update_cell(i, 9, last_sell_price)
            break

def normalize_coin_ids_in_sheet():
    """
    Chuẩn hóa Coin ID và Coin Name trong sheet về đúng chuẩn CoinGecko.
    """
    OLD_TO_NEW_ID = {
        "fusionist": "ace-casino",
        "jupiter-exchange": "jupiter", 
        "matic-network": "polygon"
    }
    if portfolio_sheet is not None:
        all_data = portfolio_sheet.get_all_values()
        if len(all_data) > 1:
            header = all_data[0]
            coin_id_idx = header.index("Coin ID") + 1
            for i, row in enumerate(all_data[1:], start=2):
                coin_id = row[coin_id_idx - 1]
                if coin_id in OLD_TO_NEW_ID:
                    new_id = OLD_TO_NEW_ID[coin_id]
                    portfolio_sheet.update_cell(i, coin_id_idx, new_id)
                    print(f"Updated Portfolio: {coin_id} → {new_id}")
    if potential_coins_sheet is not None:
        all_data = potential_coins_sheet.get_all_values()
        if len(all_data) > 1:
            header = all_data[0]
            coin_id_idx = header.index("Coin ID") + 1
            for i, row in enumerate(all_data[1:], start=2):
                coin_id = row[coin_id_idx - 1]
                if coin_id in OLD_TO_NEW_ID:
                    new_id = OLD_TO_NEW_ID[coin_id]
                    potential_coins_sheet.update_cell(i, coin_id_idx, new_id)
                    print(f"Updated Potential Coins: {coin_id} → {new_id}")

def get_historical_data(days=30):
    """Lấy dữ liệu historical prices từ sheet"""
    if spreadsheet is None:
        return {}
    try:
        historical_sheet = spreadsheet.worksheet("historicals_price")
        all_data = historical_sheet.get_all_records()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        historical_by_date = {}
        for row in all_data:
            date_str = row.get("Date", "")
            coin_id = row.get("Coin ID", "").lower()
            price = float(row.get("Price", 0) or 0)
            try:
                row_date = datetime.strptime(date_str, "%Y-%m-%d")
                if start_date <= row_date <= end_date:
                    if date_str not in historical_by_date:
                        historical_by_date[date_str] = {}
                    historical_by_date[date_str][coin_id] = price
            except ValueError:
                continue
        return historical_by_date
    except Exception as e:
        print(f"Error getting historical data: {e}")
        return {}

def get_coin_historical_prices(coin_id, days=30):
    """Lấy historical prices cho một coin cụ thể"""
    if spreadsheet is None:
        return []
    try:
        historical_sheet = spreadsheet.worksheet("historicals_price")
        all_data = historical_sheet.get_all_records()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        coin_prices = []
        for row in all_data:
            if row.get("Coin ID", "").lower() == coin_id.lower():
                date_str = row.get("Date", "")
                price = float(row.get("Price", 0) or 0)
                try:
                    row_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if start_date <= row_date <= end_date:
                        coin_prices.append({
                            "date": date_str,
                            "price": price
                        })
                except ValueError:
                    continue
        coin_prices.sort(key=lambda x: x["date"])
        return coin_prices
    except Exception as e:
        print(f"Error getting coin historical prices: {e}")
        return []

# Thay thế function fetch_current_prices

def fetch_current_prices(coin_ids):
    """
    Fetch current prices using price_fetcher_fallback module
    """
    try:
        print(f"🔄 Fetching live prices for: {coin_ids}")
        
        import price_fetcher_fallback
        
        # Convert coin symbols to CoinGecko IDs
        formatted_ids = []
        symbol_to_original = {}
        
        for coin_id in coin_ids:
            coin_str = str(coin_id).lower()
            
            # Map symbols to CoinGecko IDs
            if coin_str in ["btc", "bitcoin"]:
                formatted_ids.append("bitcoin")
                symbol_to_original["bitcoin"] = coin_str
            elif coin_str in ["eth", "ethereum"]:
                formatted_ids.append("ethereum")
                symbol_to_original["ethereum"] = coin_str
            elif coin_str in ["ada", "cardano"]:
                formatted_ids.append("cardano")
                symbol_to_original["cardano"] = coin_str
            elif coin_str in ["sol", "solana"]:
                formatted_ids.append("solana")
                symbol_to_original["solana"] = coin_str
            elif coin_str in ["dot", "polkadot"]:
                formatted_ids.append("polkadot")
                symbol_to_original["polkadot"] = coin_str
            else:
                # Assume it's already a CoinGecko ID
                formatted_ids.append(coin_str)
                symbol_to_original[coin_str] = coin_str
        
        print(f"📡 Mapped to CoinGecko IDs: {formatted_ids}")
        
        # Fetch prices
        if hasattr(price_fetcher_fallback, 'fetch_current_prices'):
            result = price_fetcher_fallback.fetch_current_prices(formatted_ids)
        elif hasattr(price_fetcher_fallback, 'fetch_coin_prices_with_fallback'):
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                price_fetcher_fallback.fetch_coin_prices_with_fallback(formatted_ids)
            )
        else:
            print("❌ No price function found")
            return get_fallback_prices(coin_ids)
        
        # Map back to original coin IDs
        final_result = {}
        for gecko_id, price_data in result.items():
            if gecko_id in symbol_to_original:
                original_id = symbol_to_original[gecko_id]
                final_result[original_id] = price_data
        
        print(f"✅ Final mapped result: {final_result}")
        return final_result if final_result else get_fallback_prices(coin_ids)
        
    except Exception as e:
        print(f"❌ fetch_current_prices error: {e}")
        import traceback
        traceback.print_exc()
        return get_fallback_prices(coin_ids)

def get_fallback_prices(coin_ids):
    """Fallback prices khi API fail"""
    result = {}
    price_map = {"btc": 67000, "eth": 3200, "ada": 0.52, "sol": 140, "dot": 7.5}
    
    for coin_id in coin_ids:
        coin_lower = str(coin_id).lower()
        result[coin_lower] = {
            "current_price": price_map.get(coin_lower, 1.0),
            "market_cap": 1000000000,
            "price_change_24h": 2.5
        }
    
    print(f"📝 Using fallback prices: {result}")
    return result

def get_portfolio_with_live_prices():
    """Get portfolio with live prices (timeout protected)"""
    try:
        print("🔄 Loading portfolio with live prices...")
        
        # Timeout protection
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("Live prices timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(20)  # 20 second timeout
        
        try:
            # Lấy portfolio base data
            portfolio_data = []
            if portfolio_sheet is not None:
                try:
                    portfolio_data = portfolio_sheet.get_all_records()
                except Exception:
                    portfolio_data = get_fallback_portfolio()  # fallback
            else:
                portfolio_data = get_fallback_portfolio()  # fallback
            
            # Lấy coin IDs
            coin_ids = [coin.get("Coin ID", "") for coin in portfolio_data if coin.get("Coin ID")]
            
            if not coin_ids:
                signal.alarm(0)
                return portfolio_data
            
            print(f"📊 Portfolio coins: {coin_ids}")
            
            # Fetch live prices
            live_prices = fetch_current_prices(coin_ids)
            print(f"📈 Live prices result: {live_prices}")
            
            # Update prices
            for coin in portfolio_data:
                coin_id = coin.get("Coin ID", "").lower()
                if coin_id in live_prices:
                    current_price = live_prices[coin_id]["current_price"]
                    coin["Current Price"] = current_price
                    
                    # Recalculate values
                    quantity = coin.get("Quantity", 0)
                    avg_buy_price = coin.get("Avg Buy Price", 0)
                    
                    if quantity and current_price:
                        current_value = quantity * current_price
                        coin["Current Value"] = current_value
                        
                        if avg_buy_price:
                            total_cost = quantity * avg_buy_price
                            pnl = current_value - total_cost
                            roi_percent = (pnl / total_cost) * 100 if total_cost > 0 else 0
                            
                            coin["P&L"] = pnl
                            coin["ROI %"] = round(roi_percent, 2)
            
            signal.alarm(0)  # Cancel timeout
            print(f"✅ Portfolio updated with live prices")
            return portfolio_data
            
        except TimeoutError:
            signal.alarm(0)
            print("⏰ Live prices timeout, using static data")
            return get_fallback_portfolio()
            
    except Exception as e:
        print(f"❌ get_portfolio_with_live_prices error: {e}")
        return get_fallback_portfolio()

def get_fallback_portfolio():
    """Fallback portfolio data"""
    return [
        {"Coin Name": "Bitcoin", "Coin ID": "BTC", "Quantity": 0.5, "Avg Buy Price": 45000, "Current Price": 47000, "Current Value": 23500, "P&L": 1000, "ROI %": 4.44},
        {"Coin Name": "Ethereum", "Coin ID": "ETH", "Quantity": 2, "Avg Buy Price": 3000, "Current Price": 3200, "Current Value": 6400, "P&L": 400, "ROI %": 6.67},
        {"Coin Name": "Cardano", "Coin ID": "ADA", "Quantity": 1000, "Avg Buy Price": 0.45, "Current Price": 0.52, "Current Value": 520, "P&L": 70, "ROI %": 15.56}
    ]

# Thay thế function test_live_prices_direct

def test_live_prices_direct():
    """Test live prices với debug output chi tiết"""
    try:
        test_coins = ["bitcoin", "ethereum", "solana"]
        print(f"🧪 Testing live prices for: {test_coins}")
        
        import price_fetcher_fallback
        
        # Debug: Kiểm tra các function có sẵn
        print("📋 Available functions in price_fetcher_fallback:")
        for attr in dir(price_fetcher_fallback):
            if not attr.startswith('_'):
                print(f"  - {attr}")
        
        # Test function chính
        if hasattr(price_fetcher_fallback, 'fetch_current_prices'):
            print("✅ Found fetch_current_prices")
            result = price_fetcher_fallback.fetch_current_prices(test_coins)
            print(f"✅ Result: {result}")
            return result
        else:
            print("❌ fetch_current_prices not found!")
            return {}
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return {}

def save_historical_prices_batch():
    """
    Lấy giá hiện tại và lưu vào historical sheet sử dụng append_historical_price
    """
    try:
        print("📊 Starting batch historical price save...")
        
        # Lấy danh sách coins từ portfolio và potential coins
        all_coins = set()
        
        # Từ portfolio
        try:
            portfolio_data = get_portfolio()
            for coin in portfolio_data:
                coin_id = coin.get("Coin ID", "")
                if coin_id:
                    all_coins.add(coin_id.lower())
        except Exception as e:
            print(f"Error getting portfolio for historical save: {e}")
        
        # Từ potential coins
        try:
            potential_data = get_potential_coins()
            for coin in potential_data:
                coin_id = coin.get("Coin ID", "")
                if coin_id:
                    all_coins.add(coin_id.lower())
        except Exception as e:
            print(f"Error getting potential coins for historical save: {e}")
        
        # Thêm top coins quan trọng
        top_coins = ["bitcoin", "ethereum", "solana", "cardano", "polkadot", "chainlink"]
        all_coins.update(top_coins)
        
        coin_list = list(all_coins)
        print(f"📈 Fetching historical prices for {len(coin_list)} coins: {coin_list}")
        
        # Fetch current prices
        current_prices = fetch_current_prices(coin_list)
        
        if not current_prices:
            print("❌ No prices fetched for historical save")
            return 0
        
        # Save to historical sheet using existing function
        current_date = datetime.now().strftime("%Y-%m-%d")
        saved_count = 0
        
        for coin_id, price_data in current_prices.items():
            try:
                current_price = price_data.get("current_price", 0)
                market_cap = price_data.get("market_cap", 0)
                
                if current_price > 0:
                    # Sử dụng function có sẵn append_historical_price
                    append_historical_price(coin_id, current_date, current_price, market_cap)
                    saved_count += 1
                    
            except Exception as e:
                print(f"Error saving historical price for {coin_id}: {e}")
        
        print(f"✅ Saved {saved_count} historical prices for {current_date}")
        return saved_count
        
    except Exception as e:
        print(f"❌ Error in save_historical_prices_batch: {e}")
        import traceback
        traceback.print_exc()
        return 0

def manual_historical_update():
    """
    Manual trigger for historical price update
    """
    try:
        print("🔄 Manual historical price update triggered...")
        count = save_historical_prices_batch()
        return f"✅ Updated {count} coins with historical prices"
        
    except Exception as e:
        error_msg = f"❌ Manual update failed: {e}"
        print(error_msg)
        return error_msg

def schedule_historical_price_updates():
    """
    Schedule historical price updates (call this daily)
    """
    try:
        import threading
        import time
        
        def daily_update():
            while True:
                try:
                    # Check if it's a new day (run at 00:05 daily)
                    current_hour = datetime.now().hour
                    current_minute = datetime.now().minute
                    
                    if current_hour == 0 and current_minute == 5:
                        print("🕐 Running daily historical price update...")
                        save_historical_prices_batch()
                        time.sleep(3600)  # Sleep 1 hour to avoid duplicate runs
                    else:
                        time.sleep(300)  # Check every 5 minutes
                        
                except Exception as e:
                    print(f"Error in daily update: {e}")
                    time.sleep(3600)  # Sleep 1 hour on error
        
        # Start background thread
        thread = threading.Thread(target=daily_update, daemon=True)
        thread.start()
        print("✅ Historical price scheduler started")
        
    except Exception as e:
        print(f"Error starting scheduler: {e}")

def test_historical_save():
    """
    Test function để kiểm tra historical save
    """
    try:
        print("🧪 Testing historical price save...")
        
        # Test với một vài coins
        test_coins = ["bitcoin", "ethereum"]
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Fetch prices
        prices = fetch_current_prices(test_coins)
        print(f"📊 Fetched prices: {prices}")
        
        # Save using existing function
        saved_count = 0
        for coin_id, price_data in prices.items():
            current_price = price_data.get("current_price", 0)
            market_cap = price_data.get("market_cap", 0)
            
            if current_price > 0:
                append_historical_price(coin_id, current_date, current_price, market_cap)
                saved_count += 1
        
        return f"✅ Test saved {saved_count} historical prices"
        
    except Exception as e:
        error_msg = f"❌ Test failed: {e}"
        print(error_msg)
        return error_msg

def load_tier1_universe_from_gsheet(spreadsheet_url: str) -> pd.DataFrame:
    """Load Tier 1 universe from Google Sheet"""
    try:
        client = get_google_sheets_client()
        if not client:
            return pd.DataFrame()
        sheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = client.open_by_key(sheet_id)
        try:
            worksheet = spreadsheet.worksheet("Tier1_Real_Time")
            data = worksheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                numeric_cols = ['Price', 'Market_Cap', 'Change_24h', 'Change_7d', 'Change_30d', 'Volume_24h', 'Rank']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                df.columns = df.columns.str.lower()
                st.info(f"📊 Loaded {len(df)} coins from Tier1_Real_Time sheet")
                return df
        except Exception as e:
            st.warning(f"⚠️ Could not load Tier1_Real_Time: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Failed to load from Google Sheet: {str(e)}")
        return pd.DataFrame()

def get_universe_data(spreadsheet_url):
    """Load universe data from Google Sheets"""
    try:
        client = get_google_sheets_client()
        if client is None:
            return pd.DataFrame()
            
        # Mở spreadsheet
        sheet = client.open_by_url(spreadsheet_url)
        worksheet = sheet.get_worksheet(0)  # Sheet đầu tiên
        
        # Lấy data
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            st.warning("⚠️ No data found in Google Sheet")
            return pd.DataFrame()
            
        return df
        
    except Exception as e:
        st.error(f"❌ Failed to load from Google Sheet: {str(e)}")
        return pd.DataFrame()

import os
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st
import price_fetcher_fallback

# Ticker mapping - moved from Main.py
TICKER_TO_ID_MAPPING = {
    "BTC": "bitcoin",
    "ETH": "ethereum", 
    "XRP": "ripple",
    "BCH": "bitcoin-cash",
    "LTC": "litecoin",
    "ADA": "cardano",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "BNB": "binancecoin",
    "XLM": "stellar",
    "DOGE": "dogecoin",
    "USDT": "tether",
    "USDC": "usd-coin",
    "SHIB": "shiba-inu",
    "MATIC": "polygon",
    "SOL": "solana",
    "AVAX": "avalanche-2",
    "TIA": "celestia",
    "ARB": "arbitrum",
    "RNDR": "render-token",
    "ONDO": "ondo-finance",
    "OM": "mantra-dao",
    "PIXEL": "pixels",
    "JUP": "jupiter",
    "PENDLE": "pendle",
    "ACE": "ace-casino"
}

# Đường dẫn đến file credentials - sửa để tìm trong thư mục hiện tại
creds_file = "gcp_credentials.json"

try:
    # Khởi tạo client với thông tin từ file
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
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
    print(f"Error connecting to Google Sheets: {str(e)}")
    print("Please check if:")
    print("1. The file gcp_credentials.json exists in the current folder")
    print("2. Google Sheet 'CryptoInvestmentDB' exists and is shared with the service account")
    print("3. The required worksheets (Portfolio, PotentialCoins, NotificationSettings) exist")
    
    # Initialize as None để Streamlit có thể handle gracefully
    client = None
    spreadsheet = None
    portfolio_sheet = None
    potential_coins_sheet = None
    notification_settings_sheet = None

# Các hàm thao tác với dữ liệu - thêm error handling cho Streamlit
def get_portfolio():
    """Get portfolio với option cho live prices"""
    try:
        # Check if we should use live prices
        use_live_prices = st.sidebar.checkbox("🔴 Use Live Prices", value=False)
        
        # Load base portfolio data
        if client and portfolio_sheet:
            portfolio = portfolio_sheet.get_all_records()
            if not portfolio:
                portfolio = get_sample_portfolio()
        else:
            portfolio = get_sample_portfolio()
        
        # Update với live prices nếu được enable
        if use_live_prices:
            portfolio = update_portfolio_with_live_prices(portfolio)
        
        return portfolio
        
    except Exception as e:
        st.error(f"❌ Error in get_portfolio: {str(e)}")
        return get_sample_portfolio()

def get_potential_coins():
    try:
        if potential_coins_sheet is None:
            return get_sample_potential_coins()
        records = potential_coins_sheet.get_all_records()
        return records if records else get_sample_potential_coins()
    except Exception as e:
        print(f"Error getting potential coins: {e}")
        return get_sample_potential_coins()

def get_notification_settings():
    try:
        if notification_settings_sheet is None:
            return []
        records = notification_settings_sheet.get_all_records()
        return records
    except Exception as e:
        print(f"Error getting notification settings: {e}")
        return []

def get_sample_portfolio():
    """Dữ liệu portfolio mẫu để test"""
    return [
        {
            "Coin ID": "BTC",
            "Coin Name": "Bitcoin",
            "Quantity": 0.5,
            "Avg Buy Price": 45000.0,
            "Current Price": 47000.0,
            "Total Value": 23500.0,
            "Market Cap": 900000000000
        },
        {
            "Coin ID": "ETH", 
            "Coin Name": "Ethereum",
            "Quantity": 2.0,
            "Avg Buy Price": 3000.0,
            "Current Price": 3200.0,
            "Total Value": 6400.0,
            "Market Cap": 380000000000
        },
        {
            "Coin ID": "ADA",
            "Coin Name": "Cardano", 
            "Quantity": 1000.0,
            "Avg Buy Price": 0.45,
            "Current Price": 0.52,
            "Total Value": 520.0,
            "Market Cap": 18000000000
        }
    ]

def get_sample_potential_coins():
    """Dữ liệu potential coins mẫu để test"""
    return [
        {
            "Coin ID": "SOL",
            "Coin Name": "Solana",
            "Current Price": 65.0,
            "Market Cap": 25000000000,
            "Recommendation": "BUY",
            "Date Added": "2025-06-10",
            "Reason": "Strong ecosystem growth"
        },
        {
            "Coin ID": "DOT",
            "Coin Name": "Polkadot",
            "Current Price": 8.5,
            "Market Cap": 9000000000,
            "Recommendation": "HOLD", 
            "Date Added": "2025-06-08",
            "Reason": "Waiting for parachain development"
        }
    ]

# Giữ nguyên các function khác từ file gốc
def append_historical_price(coin_id, date, price, market_cap=0):
    """
    Ghi một dòng dữ liệu vào sheet 'historicals_price' với market cap.
    """
    try:
        if spreadsheet is None:
            print(f"Cannot save historical price - no spreadsheet connection")
            return
            
        # Sử dụng spreadsheet thay vì sheet
        historical_sheet = spreadsheet.worksheet("historicals_price")
        historical_sheet.append_row([coin_id, date, price, market_cap])
        print(f"✅ Saved {coin_id}: ${price} (MC: ${market_cap:,.0f}) on {date}")
    except Exception as e:
        print(f"❌ Error saving historical price for {coin_id}: {e}")
        # Thử tạo sheet nếu chưa có
        try:
            if spreadsheet:
                new_sheet = spreadsheet.add_worksheet(title="historicals_price", rows="1000", cols="10")
                new_sheet.update('A1:D1', [["Coin ID", "Date", "Price", "Market Cap"]])
                new_sheet.append_row([coin_id, date, price, market_cap])
                print(f"✅ Created new sheet and saved {coin_id}: ${price}")
        except Exception as e2:
            print(f"❌ Failed to create sheet: {e2}")

def update_portfolio_prices(prices):
    """Cập nhật giá hiện tại và market cap cho portfolio - batch update"""
    try:
        if portfolio_sheet is None:
            print("Cannot update portfolio prices - no sheet connection")
            return
            
        portfolio_data = portfolio_sheet.get_all_records()
        
        # Collect all updates để batch process
        updates = []
        
        for i, row in enumerate(portfolio_data, start=2):
            coin_id = row.get("Coin ID", "").lower()
            if coin_id in prices:
                current_price = prices[coin_id].get("current_price", 0)
                market_cap = prices[coin_id].get("market_cap", 0)
                
                # Add to batch updates
                updates.append({
                    'range': f'E{i}',
                    'values': [[current_price]]
                })
                updates.append({
                    'range': f'G{i}',
                    'values': [[market_cap]]
                })
                
                # Tính total value nếu có quantity
                quantity = row.get("Quantity", 0)
                if quantity and isinstance(quantity, (int, float)) and quantity > 0:
                    total_value = float(quantity) * float(current_price)
                    updates.append({
                        'range': f'F{i}',
                        'values': [[total_value]]
                    })
        
        # Batch update to reduce API calls
        if updates:
            portfolio_sheet.batch_update(updates[:20])  # Limit to 20 updates per batch
            print(f"✅ Updated {min(len(updates), 20)} portfolio cells")
    except Exception as e:
        print(f"❌ Error updating portfolio prices: {e}")

def update_potential_coin_prices(prices):
    """Cập nhật giá hiện tại và market cap cho potential coins - batch update"""
    try:
        if potential_coins_sheet is None:
            print("Cannot update potential coin prices - no sheet connection")
            return
            
        potential_data = potential_coins_sheet.get_all_records()
        
        # Collect all updates để batch process
        updates = []
        
        for i, row in enumerate(potential_data, start=2):
            coin_id = row.get("Coin ID", "").lower()
            if coin_id in prices:
                current_price = prices[coin_id].get("current_price", 0)
                market_cap = prices[coin_id].get("market_cap", 0)
                
                # Add to batch updates
                updates.append({
                    'range': f'C{i}',
                    'values': [[current_price]]
                })
                updates.append({
                    'range': f'D{i}',
                    'values': [[market_cap]]
                })
        
        # Batch update to reduce API calls
        if updates:
            potential_coins_sheet.batch_update(updates[:20])  # Limit to 20 updates per batch
            print(f"✅ Updated {min(len(updates), 20)} potential coin cells")
    except Exception as e:
        print(f"❌ Error updating potential coin prices: {e}")

def save_notification_settings(coin_id, coin_name, desired_buy_price, desired_sell_price, buy_threshold_percent, sell_threshold_percent, email):
    try:
        if notification_settings_sheet is None:
            print("Cannot save notification settings - no sheet connection")
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
    except Exception as e:
        print(f"Error saving notification settings: {e}")

def add_portfolio_entry(coin_id, coin_name, quantity, avg_buy_price):
    try:
        if portfolio_sheet is None:
            print("Cannot add portfolio entry - no sheet connection")
            return
        portfolio_sheet.append_row([
            coin_id, coin_name, quantity, avg_buy_price, 0, 0
        ])
    except Exception as e:
        print(f"Error adding portfolio entry: {e}")

def add_potential_coin(coin_id, coin_name, recommendation, reason):
    try:
        if potential_coins_sheet is None:
            print("Cannot add potential coin - no sheet connection")
            return
        potential_coins_sheet.append_row([
            coin_id, coin_name, 0, 0, recommendation, datetime.now().strftime("%Y-%m-%d"), reason
        ])
    except Exception as e:
        print(f"Error adding potential coin: {e}")

def update_notification_status(coin_id, last_buy_price, last_sell_price):
    try:
        if notification_settings_sheet is None:
            return
        records = notification_settings_sheet.get_all_records()
        for i, record in enumerate(records, start=2):
            if record["Coin ID"] == coin_id:
                notification_settings_sheet.update_cell(i, 8, last_buy_price)
                notification_settings_sheet.update_cell(i, 9, last_sell_price)
                break
    except Exception as e:
        print(f"Error updating notification status: {e}")

def normalize_coin_ids_in_sheet():
    """
    Chuẩn hóa Coin ID và Coin Name trong sheet về đúng chuẩn CoinGecko.
    """
    if portfolio_sheet is None or potential_coins_sheet is None:
        print("Cannot normalize coin IDs - no sheet connection")
        return
        
    # Mapping các ID cũ sang ID mới
    OLD_TO_NEW_ID = {
        "fusionist": "ace-casino",
        "jupiter-exchange": "jupiter", 
        "matic-network": "polygon"
    }
    
    try:
        # Chuẩn hóa Portfolio sheet
        all_data = portfolio_sheet.get_all_values()
        if len(all_data) > 1:  # Có dữ liệu ngoài header
            header = all_data[0]
            coin_id_idx = header.index("Coin ID") + 1
            
            for i, row in enumerate(all_data[1:], start=2):
                coin_id = row[coin_id_idx - 1]
                if coin_id in OLD_TO_NEW_ID:
                    new_id = OLD_TO_NEW_ID[coin_id]
                    portfolio_sheet.update_cell(i, coin_id_idx, new_id)
                    print(f"Updated Portfolio: {coin_id} → {new_id}")
        
        # Chuẩn hóa Potential Coins sheet
        all_data = potential_coins_sheet.get_all_values()
        if len(all_data) > 1:  # Có dữ liệu ngoài header
            header = all_data[0]
            coin_id_idx = header.index("Coin ID") + 1
            
            for i, row in enumerate(all_data[1:], start=2):
                coin_id = row[coin_id_idx - 1]
                if coin_id in OLD_TO_NEW_ID:
                    new_id = OLD_TO_NEW_ID[coin_id]
                    potential_coins_sheet.update_cell(i, coin_id_idx, new_id)
                    print(f"Updated Potential Coins: {coin_id} → {new_id}")
    except Exception as e:
        print(f"Error normalizing coin IDs: {e}")

def get_historical_data(days=30):
    """Lấy dữ liệu historical prices từ sheet"""
    try:
        if spreadsheet is None:
            return {}
            
        historical_sheet = spreadsheet.worksheet("historicals_price")
        all_data = historical_sheet.get_all_records()
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Group by date
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
    try:
        if spreadsheet is None:
            return []
            
        historical_sheet = spreadsheet.worksheet("historicals_price")
        all_data = historical_sheet.get_all_records()
        
        from datetime import datetime, timedelta
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
        
        # Sort by date
        coin_prices.sort(key=lambda x: x["date"])
        return coin_prices
        
    except Exception as e:
        print(f"Error getting coin historical prices: {e}")
        return []

def get_google_sheets_client():
    """Tạo Google Sheets client với debug info"""
    try:
        # Debug: Check if secrets exist
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            st.write("✅ Found GCP credentials in secrets")
            credentials_info = dict(st.secrets["gcp_service_account"])
            
            # Debug: Check key fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials_info]
            
            if missing_fields:
                st.error(f"❌ Missing fields in credentials: {missing_fields}")
                return None
                
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
            client = gspread.authorize(credentials)
            
            st.success("✅ Google Sheets client created successfully!")
            return client
        else:
            st.warning("⚠️ No GCP credentials found in secrets, using sample data")
            return None
            
    except Exception as e:
        st.error(f"❌ Error creating Google Sheets client: {str(e)}")
        return None

def load_portfolio_data():
    """Load portfolio với debug info"""
    try:
        client = get_google_sheets_client()
        
        if client is None:
            st.info("📊 Using sample portfolio data")
            return get_sample_portfolio_data()
        
        # Try to open the spreadsheet
        spreadsheet = client.open("Crypto Portfolio Tracker")
        worksheet = spreadsheet.sheet1
        
        # Get data
        data = worksheet.get_all_records()
        st.success(f"✅ Loaded {len(data)} coins from Google Sheets")
        
        return data
        
    except Exception as e:
        st.error(f"❌ Error loading portfolio: {str(e)}")
        st.info("📊 Falling back to sample data")
        return get_sample_portfolio_data()

def update_portfolio_with_live_prices(portfolio):
    """Update portfolio với giá real-time"""
    try:
        st.write("🔄 Updating portfolio with live prices...")
        
        # Get all coin IDs
        coin_ids = [coin.get("Coin ID") for coin in portfolio if coin.get("Coin ID")]
        st.write(f"Coins to update: {coin_ids}")
        
        if not coin_ids:
            st.warning("⚠️ No coin IDs found in portfolio")
            return portfolio
        
        # Fetch live prices
        live_prices = price_fetcher_fallback.fetch_current_prices(coin_ids)
        st.write(f"Live prices fetched: {live_prices}")
        
        # Update portfolio
        updated_portfolio = []
        for coin in portfolio:
            coin_id = coin.get("Coin ID")
            if coin_id and coin_id in live_prices:
                coin["Current Price"] = live_prices[coin_id]["current_price"]
                coin["Market Cap"] = live_prices[coin_id]["market_cap"]
                
                # Recalculate Total Value
                quantity = coin.get("Quantity", 0)
                if quantity:
                    coin["Total Value"] = float(quantity) * live_prices[coin_id]["current_price"]
                    
                st.write(f"✅ Updated {coin_id}: ${live_prices[coin_id]['current_price']}")
            else:
                st.warning(f"⚠️ Could not update price for {coin_id}")
            
            updated_portfolio.append(coin)
        
        st.success(f"✅ Updated {len(updated_portfolio)} coins with live prices")
        return updated_portfolio
        
    except Exception as e:
        st.error(f"❌ Error updating prices: {str(e)}")
        return portfolio
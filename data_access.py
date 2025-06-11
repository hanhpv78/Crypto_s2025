import os
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Import mapping từ file riêng (nếu có)
try:
    from coin_mapping import TICKER_TO_ID_MAPPING
except ImportError:
    TICKER_TO_ID_MAPPING = {}

# Đường dẫn đến file credentials
creds_file = os.path.join(os.path.dirname(__file__), "gcp_credentials.json")

# Khởi tạo các biến sheet là None để tránh lỗi khi không kết nối được
portfolio_sheet = None
potential_coins_sheet = None
notification_settings_sheet = None
spreadsheet = None

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
    print(f"❌ Google Sheets connection error: {e}")
    # Cho phép app chạy tiếp với sample data

# ==================== DATA ACCESS FUNCTIONS ====================

def get_portfolio():
    if portfolio_sheet is not None:
        try:
            return portfolio_sheet.get_all_records()
        except Exception as e:
            print(f"Error reading portfolio: {e}")
    # Fallback sample data
    return [
        {"Coin Name": "Bitcoin", "Coin ID": "BTC", "Quantity": 0.5, "Avg Buy Price": 45000, "Current Price": 47000, "Current Value": 23500, "P&L": 1000, "ROI %": 4.44},
        {"Coin Name": "Ethereum", "Coin ID": "ETH", "Quantity": 2, "Avg Buy Price": 3000, "Current Price": 3200, "Current Value": 6400, "P&L": 400, "ROI %": 6.67},
        {"Coin Name": "Cardano", "Coin ID": "ADA", "Quantity": 1000, "Avg Buy Price": 0.45, "Current Price": 0.52, "Current Value": 520, "P&L": 70, "ROI %": 15.56}
    ]

def get_potential_coins():
    if potential_coins_sheet is not None:
        try:
            return potential_coins_sheet.get_all_records()
        except Exception as e:
            print(f"Error reading potential coins: {e}")
    return []

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
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import aiohttp
import os
import sys
from pathlib import Path
import requests  # For API testing
import price_fetcher_fallback  # For live prices

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import modules với error handling
try:
    import data_access
    import notification
    import_success = True
except ImportError as e:
    import_success = False
    import_error = str(e)

# Cấu hình trang
st.set_page_config(
    page_title="🚀 Crypto Portfolio Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kiểm tra import status
if not import_success:
    st.error(f"❌ Import error: {import_error}")
    st.error("Please check if all required files are in the same directory")
    
    # Debug info
    st.write("**Debug Information:**")
    st.write(f"Current directory: {os.getcwd()}")
    st.write(f"Python path: {sys.path}")
    
    files_in_dir = os.listdir('.')
    st.write("Files in current directory:")
    for file in files_in_dir:
        st.write(f"- {file}")
    
    st.info("Required files: data_access.py, price_fetcher_fallback.py, notification.py, gcp_credentials.json")
    st.stop()
else:
    st.success("✅ All modules imported successfully!")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .profit { 
        color: #4CAF50; 
        font-weight: bold;
    }
    .loss { 
        color: #f44336; 
        font-weight: bold;
    }
    .sidebar-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .status-success {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Mapping từ Main.py
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

@st.cache_data(ttl=300)  # Cache 5 phút
def load_portfolio_data():
    """Load portfolio data với caching"""
    try:
        portfolio = data_access.get_portfolio()
        potential_coins = data_access.get_potential_coins()
        return portfolio, potential_coins, None
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        # Trả về dữ liệu mẫu thay vì crash
        return get_sample_data(), [], None

def get_sample_data():
    """Dữ liệu mẫu khi Google Sheets lỗi"""
    return [
        {
            "Coin ID": "BTC",
            "Coin Name": "Bitcoin", 
            "Quantity": 0.5,
            "Avg Buy Price": 45000,
            "Current Price": 47000,
            "Market Cap": 900000000000
        }
    ]

@st.cache_data(ttl=600)  # Cache 10 phút
def load_analytics_data():
    """Load analytics data với caching"""
    try:
        portfolio = data_access.get_portfolio()
        
        total_value = 0
        total_cost = 0
        analytics = {
            "total_coins": len(portfolio),
            "performance_by_coin": [],
            "summary": {}
        }
        
        for coin in portfolio:
            quantity = coin.get("Quantity", 0) or 0
            avg_buy_price = coin.get("Avg Buy Price", 0) or 0
            current_price = coin.get("Current Price", 0) or 0
            market_cap = coin.get("Market Cap", 0) or 0
            
            current_value = quantity * current_price
            cost = quantity * avg_buy_price
            gain_loss = current_value - cost
            roi_percent = (gain_loss / cost * 100) if cost > 0 else 0
            
            total_value += current_value
            total_cost += cost
            
            coin_analytics = {
                "coin_name": coin.get("Coin Name", coin.get("Coin ID")),
                "coin_id": coin.get("Coin ID"),
                "current_value": current_value,
                "cost": cost,
                "gain_loss": gain_loss,
                "roi_percent": roi_percent,
                "market_cap": market_cap,
                "allocation_percent": 0
            }
            analytics["performance_by_coin"].append(coin_analytics)
        
        # Calculate allocation percentages
        for coin_analytics in analytics["performance_by_coin"]:
            coin_analytics["allocation_percent"] = (coin_analytics["current_value"] / total_value * 100) if total_value > 0 else 0
        
        # Sort by performance
        analytics["performance_by_coin"].sort(key=lambda x: x["roi_percent"], reverse=True)
        
        # Summary
        total_gain_loss = total_value - total_cost
        total_roi = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        analytics["summary"] = {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_gain_loss": total_gain_loss,
            "total_roi_percent": total_roi,
            "profitable_coins": len([c for c in analytics["performance_by_coin"] if c["roi_percent"] > 0]),
            "losing_coins": len([c for c in analytics["performance_by_coin"] if c["roi_percent"] < 0])
        }
        
        return analytics, None
    except Exception as e:
        return {}, str(e)

def main():
    st.markdown('<h1 class="main-header">🚀 Crypto Portfolio Dashboard</h1>', unsafe_allow_html=True)

    # ========== DEBUG PANEL LUÔN HIỂN THỊ ĐẦU SIDEBAR ==========
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 Debug Panel")
    debug_enabled = st.sidebar.checkbox("🔍 Show Debug Info")
    if debug_enabled:
        st.sidebar.markdown("#### 🔐 Credentials")
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            st.sidebar.success("✅ GCP Secrets Found")
            st.sidebar.code(f"Project: {st.secrets['gcp_service_account'].get('project_id', 'N/A')}")
        else:
            st.sidebar.error("❌ No GCP Secrets")

        st.sidebar.markdown("#### 🌐 API Tests")
        if st.sidebar.button("Test CoinGecko"):
            with st.spinner("Testing..."):
                try:
                    resp = requests.get("https://api.coingecko.com/api/v3/ping", timeout=5)
                    if resp.status_code == 200:
                        st.sidebar.success("✅ CoinGecko OK")
                        price_resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=5)
                        if price_resp.status_code == 200:
                            prices = price_resp.json()
                            st.sidebar.json(prices)
                        else:
                            st.sidebar.error(f"Price fetch failed: {price_resp.status_code}")
                    else:
                        st.sidebar.error(f"API failed: {resp.status_code}")
                except Exception as e:
                    st.sidebar.error(f"Error: {str(e)}")

        if st.sidebar.button("Test Live Prices"):
            with st.spinner("Fetching..."):
                try:
                    live_prices = price_fetcher_fallback.fetch_current_prices(["BTC", "ETH", "SOL"])
                    st.sidebar.success("✅ Live prices working!")
                    st.sidebar.json(live_prices)
                except Exception as e:
                    st.sidebar.error(f"Error: {str(e)}")

        st.sidebar.markdown("#### ⚡ Actions")
        if st.sidebar.button("🔄 Use Live Prices"):
            st.session_state['use_live_prices'] = True
            st.cache_data.clear()
            st.sidebar.success("✅ Switched to live prices!")
            st.sidebar.info("Refresh page to see changes")
        if st.sidebar.button("📊 Use Sample Data"):
            st.session_state['use_live_prices'] = False
            st.cache_data.clear()
            st.sidebar.success("✅ Switched to sample data!")
    # ========== END DEBUG PANEL ==========

    # Sidebar
    st.sidebar.title("🔧 Dashboard Controls")
    
    # Connection status check - KHÔNG RETURN KHI LỖI
    st.sidebar.markdown("### 📊 System Status")
    google_sheets_error = None
    try:
        # Test Google Sheets connection
        test_portfolio = data_access.get_portfolio()
        st.sidebar.markdown('<div class="status-success">✅ Google Sheets Connected</div>', unsafe_allow_html=True)
        st.sidebar.markdown(f"📈 Found {len(test_portfolio)} coins in portfolio")
    except Exception as e:
        google_sheets_error = str(e)
        st.sidebar.markdown('<div class="status-error">❌ Google Sheets Error</div>', unsafe_allow_html=True)
        st.sidebar.error(f"Error: {str(e)}")
        # KHÔNG return ở đây - tiếp tục hiển thị debug panel
    
    # Manual refresh controls
    st.sidebar.markdown("### 🔄 Data Controls")
    if st.sidebar.button("🔄 Refresh All Data", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Time info
    st.sidebar.markdown("### ⏰ Last Updated")
    st.sidebar.markdown(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Main content - CÓ THỂ FAIL NHƯNG SIDEBAR VẪN HIỂN THỊ
    if google_sheets_error:
        st.error(f"🚨 Cannot connect to Google Sheets: {google_sheets_error}")
        st.info("🔧 Use the Debug Panel in sidebar to troubleshoot")
        
        # Hiển thị sample data thay vì crash
        st.warning("📊 Displaying sample data for demonstration")
        portfolio = get_sample_data()
        potential_coins = []
    else:
        # Load real data
        portfolio, potential_coins, error = load_portfolio_data()
        if error:
            st.error(f"❌ Error loading data: {error}")
            portfolio = get_sample_data()
            potential_coins = []
    
    # Continue với analytics và rest of dashboard...
    analytics, analytics_error = load_analytics_data()
    
    if not portfolio:
        st.warning("⚠️ No portfolio data found. Using sample data.")
        portfolio = get_sample_data()
    
    # Metrics dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_color = "normal" if analytics["summary"]["total_gain_loss"] >= 0 else "inverse"
        st.metric(
            label="💰 Total Value",
            value=f"${analytics['summary']['total_value']:,.2f}",
            delta=f"${analytics['summary']['total_gain_loss']:,.2f}",
            delta_color=delta_color
        )
    
    with col2:
        st.metric(
            label="📊 Total Cost",
            value=f"${analytics['summary']['total_cost']:,.2f}"
        )
    
    with col3:
        roi_delta_color = "normal" if analytics["summary"]["total_roi_percent"] >= 0 else "inverse"
        st.metric(
            label="📈 ROI %",
            value=f"{analytics['summary']['total_roi_percent']:.2f}%",
            delta=f"{analytics['summary']['total_roi_percent']:.2f}%",
            delta_color=roi_delta_color
        )
    
    with col4:
        st.metric(
            label="🎯 Profitable Coins",
            value=f"{analytics['summary']['profitable_coins']}/{len(portfolio)}",
            delta=f"+{analytics['summary']['profitable_coins']}"
        )
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Portfolio", "🔍 Potential Coins", "📊 Analytics"])
    
    with tab1:
        st.subheader("💼 Current Portfolio")
        
        if portfolio:
            # Create enhanced dataframe
            portfolio_df = pd.DataFrame(portfolio)
            
            # Calculate additional columns
            portfolio_df['Current Value'] = portfolio_df.apply(
                lambda row: (row.get('Quantity', 0) or 0) * (row.get('Current Price', 0) or 0), axis=1
            )
            portfolio_df['Cost'] = portfolio_df.apply(
                lambda row: (row.get('Quantity', 0) or 0) * (row.get('Avg Buy Price', 0) or 0), axis=1
            )
            portfolio_df['P&L'] = portfolio_df['Current Value'] - portfolio_df['Cost']
            portfolio_df['ROI %'] = portfolio_df.apply(
                lambda row: (row['P&L'] / row['Cost'] * 100) if row['Cost'] > 0 else 0, axis=1
            )
            
            # Format for display
            display_df = portfolio_df.copy()
            display_df['Current Price'] = display_df['Current Price'].apply(lambda x: f"${x:.4f}" if pd.notnull(x) else "N/A")
            display_df['Avg Buy Price'] = display_df['Avg Buy Price'].apply(lambda x: f"${x:.4f}" if pd.notnull(x) else "N/A")
            display_df['Current Value'] = display_df['Current Value'].apply(lambda x: f"${x:,.2f}")
            display_df['Cost'] = display_df['Cost'].apply(lambda x: f"${x:,.2f}")
            display_df['P&L'] = display_df['P&L'].apply(lambda x: f"${x:,.2f}")
            display_df['ROI %'] = display_df['ROI %'].apply(lambda x: f"{x:.2f}%")
            
            # Display table
            st.dataframe(
                display_df[['Coin Name', 'Coin ID', 'Quantity', 'Avg Buy Price', 'Current Price', 'Current Value', 'P&L', 'ROI %']],
                use_container_width=True,
                hide_index=True
            )
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Portfolio Allocation")
                if len(portfolio_df) > 0 and portfolio_df['Current Value'].sum() > 0:
                    fig_pie = px.pie(
                        portfolio_df, 
                        values='Current Value', 
                        names='Coin Name',
                        title="Portfolio Allocation by Value"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No data available for pie chart")
            
            with col2:
                st.subheader("📈 Performance Overview")
                if len(portfolio_df) > 0:
                    # Sort by P&L for better visualization
                    portfolio_sorted = portfolio_df.sort_values('P&L', ascending=True)
                    
                    fig_bar = px.bar(
                        portfolio_sorted,
                        x='P&L',
                        y='Coin Name',
                        orientation='h',
                        color='P&L',
                        color_continuous_scale=['red', 'yellow', 'green'],
                        title="Profit/Loss by Coin"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No data available for bar chart")
    
    with tab2:
        st.subheader("🔍 Potential Coins")
        
        if potential_coins:
            potential_df = pd.DataFrame(potential_coins)
            st.dataframe(potential_df, use_container_width=True, hide_index=True)
        else:
            st.info("No potential coins data found.")
    
    with tab3:
        st.subheader("📊 Advanced Analytics")
        
        if analytics and analytics["performance_by_coin"]:
            # Performance table
            st.subheader("📈 Detailed Performance")
            perf_display = pd.DataFrame(analytics["performance_by_coin"])
            perf_display['current_value'] = perf_display['current_value'].apply(lambda x: f"${x:,.2f}")
            perf_display['cost'] = perf_display['cost'].apply(lambda x: f"${x:,.2f}")
            perf_display['gain_loss'] = perf_display['gain_loss'].apply(lambda x: f"${x:,.2f}")
            perf_display['roi_percent'] = perf_display['roi_percent'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(
                perf_display.rename(columns={
                    'coin_name': 'Coin',
                    'current_value': 'Current Value',
                    'cost': 'Cost',
                    'gain_loss': 'Gain/Loss',
                    'roi_percent': 'ROI %'
                })[['Coin', 'Current Value', 'Cost', 'Gain/Loss', 'ROI %']],
                use_container_width=True,
                hide_index=True
            )

    # ========== HISTORICAL DATA PANEL ==========
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Historical Data")
    
    if st.sidebar.button("💾 Update Historical Prices"):
        with st.spinner("Updating historical prices..."):
            result = manual_historical_update()
            st.success(result)
    
    if st.sidebar.button("🧪 Test Historical Save"):
        with st.spinner("Testing historical save..."):
            result = test_historical_save()
            st.info(result)
    
    # Thêm info về historical data
    if st.sidebar.button("📈 Show Historical Stats"):
        historical_data = get_historical_data(30)
        if historical_data:
            total_days = len(historical_data)
            total_records = sum(len(coins) for coins in historical_data.values())
            st.sidebar.info(f"📊 Historical Data:\n- {total_days} days\n- {total_records} price records")
        else:
            st.sidebar.warning("No historical data found")

# Thêm vào main app để start scheduler

# Start historical price scheduler (chỉ chạy 1 lần)
if 'scheduler_started' not in st.session_state:
    try:
        schedule_historical_price_updates()
        st.session_state.scheduler_started = True
        print("✅ Historical price scheduler initialized")
    except Exception as e:
        print(f"❌ Failed to start scheduler: {e}")

if __name__ == "__main__":
    main()
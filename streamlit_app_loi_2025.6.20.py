import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# Add modules directory to path
current_dir = os.path.dirname(__file__)
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

# Set page config FIRST
st.set_page_config(
    page_title="Crypto Investment Platform", 
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Step 2 modules with error handling
step2_modules = {}
try:
    from modules.technical_indicators import show_technical_dashboard
    step2_modules['technical'] = True
except ImportError:
    step2_modules['technical'] = False

try:
    from modules.alerts_notifications import show_alerts_dashboard
    step2_modules['alerts'] = True
except ImportError:
    step2_modules['alerts'] = False

try:
    from modules.portfolio_tracker import show_portfolio_dashboard
    step2_modules['portfolio'] = True
except ImportError:
    step2_modules['portfolio'] = False

try:
    from modules.backtest_strategy import show_backtest_dashboard
    step2_modules['backtest'] = True
except ImportError:
    step2_modules['backtest'] = False

try:
    from modules.sentiment_analysis import show_sentiment_dashboard
    step2_modules['sentiment'] = True
except ImportError:
    step2_modules['sentiment'] = False

try:
    from modules.indicators_engine import show_indicators_engine_dashboard
    step2_modules['indicators_engine'] = True
except ImportError:
    step2_modules['indicators_engine'] = False


def get_spreadsheet_url():
    """Get spreadsheet URL from secrets"""
    try:
        return st.secrets["gsheet_url"]
    except Exception as e:
        st.error(f"❌ Cannot get gsheet_url: {e}")
        return ""

spreadsheet_url = get_spreadsheet_url()
# === PRICE FETCHER CLASS ===
class TierOnePriceFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Top tier 1 coins
        self.tier1_coins = {
            'bitcoin': {'symbol': 'BTC', 'name': 'Bitcoin'},
            'ethereum': {'symbol': 'ETH', 'name': 'Ethereum'},
            'binancecoin': {'symbol': 'BNB', 'name': 'BNB'},
            'solana': {'symbol': 'SOL', 'name': 'Solana'},
            'cardano': {'symbol': 'ADA', 'name': 'Cardano'},
            'avalanche-2': {'symbol': 'AVAX', 'name': 'Avalanche'},
            'polkadot': {'symbol': 'DOT', 'name': 'Polkadot'},
            'chainlink': {'symbol': 'LINK', 'name': 'Chainlink'},
            'polygon': {'symbol': 'MATIC', 'name': 'Polygon'},
            'uniswap': {'symbol': 'UNI', 'name': 'Uniswap'},
            'litecoin': {'symbol': 'LTC', 'name': 'Litecoin'},
            'internet-computer': {'symbol': 'ICP', 'name': 'Internet Computer'},
            'ethereum-classic': {'symbol': 'ETC', 'name': 'Ethereum Classic'},
            'stellar': {'symbol': 'XLM', 'name': 'Stellar'},
            'vechain': {'symbol': 'VET', 'name': 'VeChain'},
            'filecoin': {'symbol': 'FIL', 'name': 'Filecoin'},
            'tron': {'symbol': 'TRX', 'name': 'TRON'},
            'algorand': {'symbol': 'ALGO', 'name': 'Algorand'},
            'cosmos': {'symbol': 'ATOM', 'name': 'Cosmos'},
            'near': {'symbol': 'NEAR', 'name': 'NEAR Protocol'}
        }
    
    def create_tier1_universe(self) -> pd.DataFrame:
        """Fetch real-time Tier 1 universe from CoinGecko"""
        try:
            # Fetch top 200 coins
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 200,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '1h,24h,7d,30d'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Filter only tier 1 coins
                tier1_data = []
                for coin in data:
                    if coin['id'] in self.tier1_coins or coin['market_cap_rank'] <= 50:
                        symbol = coin['symbol'].upper()
                        
                        tier1_data.append({
                            'symbol': symbol,
                            'name': coin['name'],
                            'price': coin['current_price'] or 0,
                            'market_cap': coin['market_cap'] or 0,
                            'change_1h': coin.get('price_change_percentage_1h_in_currency', 0) or 0,
                            'change_24h': coin.get('price_change_percentage_24h', 0) or 0,
                            'change_7d': coin.get('price_change_percentage_7d_in_currency', 0) or 0,
                            'change_30d': coin.get('price_change_percentage_30d_in_currency', 0) or 0,
                            'volume_24h': coin['total_volume'] or 0,
                            'rank': coin['market_cap_rank'] or 999,
                            'source': 'CoinGecko',
                            'last_updated': datetime.now().isoformat(),
                            'coin_id': coin['id']
                        })
                
                df = pd.DataFrame(tier1_data)
                df = df.sort_values('rank').reset_index(drop=True)
                
                st.success(f"✅ Fetched {len(df)} Tier 1 coins from CoinGecko")
                return df
            
            else:
                st.warning(f"⚠️ CoinGecko API returned {response.status_code}")
                return self._get_fallback_data()
                
        except Exception as e:
            st.error(f"❌ Error fetching data: {str(e)}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> pd.DataFrame:
        """Fallback demo data"""
        fallback_data = []
        
        for i, (coin_id, info) in enumerate(self.tier1_coins.items()):
            # Generate realistic demo prices
            base_prices = {
                'BTC': 67000, 'ETH': 3500, 'BNB': 600, 'SOL': 160, 'ADA': 0.52,
                'AVAX': 35, 'DOT': 6.8, 'LINK': 15.2, 'MATIC': 0.95, 'UNI': 12.5,
                'LTC': 180, 'ICP': 12.8, 'ETC': 32.5, 'XLM': 0.12, 'VET': 0.045,
                'FIL': 8.2, 'TRX': 0.11, 'ALGO': 0.28, 'ATOM': 11.5, 'NEAR': 3.8
            }
            
            symbol = info['symbol']
            price = base_prices.get(symbol, 1.0)
            
            fallback_data.append({
                'symbol': symbol,
                'name': info['name'],
                'price': price,
                'market_cap': price * 1000000000 * (50 - i),  # Decreasing market cap
                'change_1h': np.random.uniform(-2, 2),
                'change_24h': np.random.uniform(-10, 10),
                'change_7d': np.random.uniform(-20, 20),
                'change_30d': np.random.uniform(-40, 40),
                'volume_24h': price * 1000000 * (100 - i),
                'rank': i + 1,
                'source': 'Demo',
                'last_updated': datetime.now().isoformat(),
                'coin_id': coin_id
            })
        
        df = pd.DataFrame(fallback_data)
        st.warning(f"⚠️ Using demo data ({len(df)} coins)")
        return df
    
    def detect_universe_changes(self, current_df: pd.DataFrame, previous_symbols: set) -> Dict:
        """Detect changes in universe"""
        current_symbols = set(current_df['symbol'].tolist())
        
        new_coins = current_symbols - previous_symbols
        removed_coins = previous_symbols - current_symbols
        
        return {
            'new_coins': list(new_coins),
            'removed_coins': list(removed_coins),
            'total_current': len(current_symbols),
            'total_previous': len(previous_symbols)
        }

    def detect_significant_movements(self, df: pd.DataFrame, threshold: float = 20.0) -> pd.DataFrame:
        """Detect significant movements"""
        if df.empty:
            return pd.DataFrame()
        
        significant_moves = df[
            (abs(df['change_30d']) >= threshold) & 
            (df['change_30d'] != 0)
        ].copy()
        
        if not significant_moves.empty:
            significant_moves = significant_moves.sort_values('change_30d', key=abs, ascending=False)
            significant_moves['movement_type'] = significant_moves['change_30d'].apply(
                lambda x: '🚀 PUMP' if x > 0 else '📉 DUMP'
            )
        
        return significant_moves

# === HISTORICAL DATA FUNCTIONS ===
@st.cache_data(ttl=600)
def get_historical_prices_top10(symbols_list, period="1y"):
    """Get historical prices for top 10 coins"""
    historical_data = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(symbols_list[:10]):  # Limit to 10
        try:
            status_text.text(f"Loading {symbol} historical data... ({i+1}/{min(len(symbols_list), 10)})")
            
            # Create ticker symbol for yfinance
            ticker_map = {
                'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'BNB': 'BNB-USD',
                'SOL': 'SOL-USD', 'ADA': 'ADA-USD', 'AVAX': 'AVAX-USD',
                'DOT': 'DOT-USD', 'LINK': 'LINK-USD', 'MATIC': 'MATIC-USD',
                'UNI': 'UNI-USD', 'LTC': 'LTC-USD'
            }
            
            ticker = ticker_map.get(symbol, f'{symbol}-USD')
            
            # Get data from yfinance
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if not hist.empty:
                historical_data[symbol] = {
                    'dates': hist.index.tolist(),
                    'prices': hist['Close'].tolist(),
                    'symbol': symbol
                }
            
            progress_bar.progress((i + 1) / min(len(symbols_list), 10))
            
        except Exception as e:
            st.warning(f"⚠️ Cannot get data for {symbol}: {str(e)}")
            continue
    
    status_text.empty()
    progress_bar.empty()
    
    return historical_data

# === NAVIGATION FUNCTION (THÊM MỚI) ===
def show_navigation():
    """Enhanced navigation with Step 2 modules"""
    st.sidebar.title("🚀 Crypto Investment Platform")
    
    # Build module list
    modules = ["📊 Crypto Dashboard (Step 1)"]
    
    if step2_modules['technical']:
        modules.append("📈 Technical Indicators")
    if step2_modules['alerts']:
        modules.append("🚨 Alerts & Notifications")
    if step2_modules['portfolio']:
        modules.append("💼 Portfolio Tracker")
    if step2_modules['backtest']:
        modules.append("🔬 Strategy Backtesting")
    if step2_modules['sentiment']:
        modules.append("🧠 Sentiment Analysis")
    if step2_modules['indicators_engine']:
        modules.append("⚙️ Indicators Engine")
    
    selected_module = st.sidebar.selectbox("Choose Module", modules)
    
    # Module status
    available_count = sum(step2_modules.values())
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Platform Status")
    st.sidebar.success(f"✅ Step 1: Crypto Dashboard")
    
    if available_count == 6:
        st.sidebar.success(f"🚀 Step 2: {available_count}/6 modules ready")
    else:
        st.sidebar.info(f"⏳ Step 2: {available_count}/6 modules loading...")
    
    if available_count < 6:
        missing_modules = [k for k, v in step2_modules.items() if not v]
        st.sidebar.warning(f"📦 Loading: {', '.join(missing_modules)}")
    
    return selected_module

# === MODIFIED MAIN FUNCTION ===
def main():
    """Main function with Step 1 + Step 2 integration"""
    
    # Navigation
    selected_module = show_navigation()
    
    # Route to appropriate module
    if selected_module == "📊 Crypto Dashboard (Step 1)":
        show_crypto_dashboard()  # Your existing main function renamed
        
    elif selected_module == "📈 Technical Indicators" and step2_modules['technical']:
        show_technical_dashboard()
        
    elif selected_module == "🚨 Alerts & Notifications" and step2_modules['alerts']:
        show_alerts_dashboard()
        
    elif selected_module == "💼 Portfolio Tracker" and step2_modules['portfolio']:
        show_portfolio_dashboard()
        
    elif selected_module == "🔬 Strategy Backtesting" and step2_modules['backtest']:
        show_backtest_dashboard()
        
    elif selected_module == "🧠 Sentiment Analysis" and step2_modules['sentiment']:
        show_sentiment_dashboard()
    
    elif selected_module == "⚙️ Indicators Engine" and step2_modules.get('indicators_engine'):
        show_indicators_engine_dashboard()
    
    else:
        st.error("❌ Module not available yet")
        st.info("💡 This module is being deployed. Please refresh in a moment!")

# === YOUR EXISTING MAIN FUNCTION (RENAMED) ===
def show_crypto_dashboard():
    # Khởi tạo
    universe_df = pd.DataFrame()
    
    # Load data từ Tier1_Real_Time sheet
    try:
        spreadsheet_url = st.secrets.get("gsheet_url", "")
        if spreadsheet_url:
            from data_access import get_tier1_realtime_data
            universe_df = get_tier1_realtime_data(spreadsheet_url)
            
            if not universe_df.empty:
                # Lưu vào session state để button có thể access
                st.session_state.universe_df = universe_df
                st.session_state.spreadsheet_url = spreadsheet_url
                
                # Debug: show column names
                st.write("**Debug - Column names:**", list(universe_df.columns))
                st.write("**Debug - DataFrame shape:**", universe_df.shape)
                st.write("**Debug - First row:**", universe_df.iloc[0].to_dict() if len(universe_df) > 0 else "No data")
                
                st.info(f"📊 Loaded {len(universe_df)} coins from Tier1_Real_Time")
                # Hiển thị preview data
                with st.expander("📋 Preview Tier1 Data"):
                    st.dataframe(universe_df.head())
    except Exception as e:
        st.error(f"❌ Error loading Tier1 data: {e}")
    
    # Sửa line export:
    data_to_export = []
    #st.info("📊 Google Sheets temporarily disabled for debugging")

    st.title("💎 Tier 1 Crypto Portfolio Dashboard")
    st.markdown("**Real-time Tier 1 Cryptocurrency Universe Tracker**")
    st.markdown("---")
    
    # Sidebar controls
    st.sidebar.header("⚙️ Dashboard Controls")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=False)
    
    # Manual refresh
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        data_to_export = [universe_df.columns.tolist()] + universe_df.values.tolist()
        export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export)
        st.success("Đã lưu danh sách coin Tier 1 mới nhất lên Google Sheet!")
        st.cache_data.clear()
        st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Load real-time data
    with st.spinner("🔵 Fetching Tier 1 cryptocurrency data..."):
        fetcher = TierOnePriceFetcher()
        try:
            universe_df = fetcher.create_tier1_universe()
            if universe_df is None or not isinstance(universe_df, pd.DataFrame):
                universe_df = pd.DataFrame()
        except Exception as e:
            st.error(f"Lỗi khi lấy dữ liệu Tier 1: {e}")
            universe_df = pd.DataFrame()

    if isinstance(universe_df, pd.DataFrame) and not universe_df.empty:
        data_to_export = [universe_df.columns.tolist()] + universe_df.values.tolist()
        export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export)
        st.success("Đã lưu danh sách coin Tier 1 mới nhất lên Google Sheet!")
    else:
        st.error("Không lấy được dữ liệu Tier 1 coin.")

    # Store in session state for change detection
    if "last_universe" not in st.session_state:
        #st.session_state["last_universe"] = set(universe_df['symbol'].tolist())
        try:
            if not universe_df.empty:
                symbol_col = None
                for col in universe_df.columns:
                    if col.lower() in ['symbol', 'ticker', 'coin']:
                        symbol_col = col
                        break
                
                if symbol_col:
                    st.session_state["last_universe"] = set(universe_df[symbol_col].tolist())
                else:
                    st.session_state["last_universe"] = set()
            else:
                st.session_state["last_universe"] = set()
        except Exception as e:
            st.error(f"❌ Error setting last_universe: {e}")
            st.session_state["last_universe"] = set()
    
    # === 1. UNIVERSE OVERVIEW ===
    st.header("1️⃣ Tier 1 Crypto Universe Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Coins", len(universe_df), help="Number of Tier 1 cryptocurrencies")
    
    with col2:
        # Sửa line 455:
        try:
            if not universe_df.empty:
                # Thử các tên column có thể có
                mcap_col = None
                for col in universe_df.columns:
                    if col.lower() in ['market_cap', 'market cap', 'marketcap']:
                        mcap_col = col
                        break
        
            if mcap_col:
                total_mcap = pd.to_numeric(universe_df[mcap_col], errors='coerce').sum()
            else:
                total_mcap = 0
                st.warning(f"⚠️ Market cap column not found in: {list(universe_df.columns)}")
        except Exception as e:
            st.error(f"❌ Error calculating market cap: {e}")
            total_mcap = 0
        
        st.metric("Total Market Cap", f"${total_mcap/1e12:.2f}T", help="Combined market capitalization")
    
    with col3:
        try:
            if not universe_df.empty:
                # Tìm column change 24h với các tên có thể có
                change_col = None
                for col in universe_df.columns:
                    if 'change' in col.lower() and '24' in col:
                        change_col = col
                        break
                
                if change_col:
                    avg_change = pd.to_numeric(universe_df[change_col], errors='coerce').mean()
                else:
                    avg_change = 0
                    st.warning(f"⚠️ Change 24h column not found in: {list(universe_df.columns)}")
            else:
                avg_change = 0
        except Exception as e:
            st.error(f"❌ Error calculating avg change: {e}")
            avg_change = 0
        
        st.metric("Avg 24h Change", f"{avg_change:+.2f}%", help="Average 24-hour price change")
    
    with col4:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric("Last Update", current_time, help="Data refresh time")
    
    # Display universe table
    st.subheader("📊 Live Universe Data")
    
    # Format data for display
    display_df = universe_df.copy()
    display_df['Price'] = display_df['price'].apply(lambda x: f"${x:,.4f}")
    display_df['Market Cap'] = display_df['market_cap'].apply(lambda x: f"${x/1e9:.2f}B")
    display_df['24h Change'] = display_df['change_24h'].apply(lambda x: f"{x:+.2f}%")
    display_df['7d Change'] = display_df['change_7d'].apply(lambda x: f"{x:+.2f}%")
    display_df['Rank'] = display_df['rank']
    
    # Select columns to display
    display_columns = ['symbol', 'name', 'Price', 'Market Cap', '24h Change', '7d Change', 'Rank', 'source']
    st.dataframe(
        display_df[display_columns], 
        use_container_width=True,
        hide_index=True
    )
    
    # === 2. TOP 10 HISTORICAL CHARTS ===
    st.header("2️⃣ Top 10 Coins - Historical Price Charts (1 Year)")
    
    if len(universe_df) >= 10:
        top_10 = universe_df.head(10).copy()
        top_10_symbols = top_10['symbol'].tolist()
        
        with st.expander("📈 View Individual Price Charts", expanded=True):
            st.info(f"📊 Loading 1-year historical data for: {', '.join(top_10_symbols[:5])}...")
            
            # Get historical data
            historical_data = get_historical_prices_top10(top_10_symbols, period="1y")
            
            if historical_data:
                # Create individual charts in 2 columns
                col1, col2 = st.columns(2)
                
                for i, (symbol, data) in enumerate(historical_data.items()):
                    if i >= 10:  # Limit to 10 charts
                        break
                        
                    target_col = col1 if i % 2 == 0 else col2
                    
                    with target_col:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=data['dates'],
                            y=data['prices'],
                            mode='lines',
                            name=symbol,
                            line=dict(width=2),
                            hovertemplate=f'{symbol}<br>Date: %{{x}}<br>Price: $%{{y:,.2f}}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title=f"{symbol} - 1 Year Price Chart",
                            xaxis_title="Date",
                            yaxis_title="Price (USD)",
                            height=300,
                            showlegend=False,
                            template="plotly_dark"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Combined normalized chart
                st.subheader("📈 Combined Performance Comparison")
                
                fig_combined = go.Figure()
                
                for symbol, data in historical_data.items():
                    if data['prices']:
                        # Normalize prices to show percentage change from start
                        start_price = data['prices'][0]
                        normalized_prices = [(price/start_price - 1) * 100 for price in data['prices']]
                        
                        fig_combined.add_trace(go.Scatter(
                            x=data['dates'],
                            y=normalized_prices,
                            mode='lines',
                            name=symbol,
                            line=dict(width=2),
                            hovertemplate=f'{symbol}<br>Date: %{{x}}<br>Change: %{{y:+.2f}}%<extra></extra>'
                        ))
                
                fig_combined.update_layout(
                    title="Top 10 Coins - Normalized Performance (% change from 1 year ago)",
                    xaxis_title="Date",
                    yaxis_title="Price Change (%)",
                    height=500,
                    hovermode='x unified',
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig_combined, use_container_width=True)
            
            else:
                st.error("❌ Cannot load historical data")
    
    # === 3. INDIVIDUAL COIN ANALYSIS ===
    st.header("3️⃣ Individual Coin Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_coin = st.selectbox(
            "Select Cryptocurrency",
            options=universe_df['symbol'].tolist(),
            index=0
        )
    
    with col2:
        time_period = st.selectbox(
            "Time Period",
            options=["1y", "6mo", "3mo", "1mo", "7d"],
            index=0
        )
    
    # Display selected coin info and chart
    if selected_coin:
        coin_data = universe_df[universe_df['symbol'] == selected_coin].iloc[0]
        
        # Coin info cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Price", f"${coin_data['price']:,.4f}")
        with col2:
            st.metric("Market Cap", f"${coin_data['market_cap']/1e9:.2f}B")
        with col3:
            st.metric("24h Change", f"{coin_data['change_24h']:+.2f}%")
        with col4:
            st.metric("Market Rank", f"#{coin_data['rank']}")
        
        # Individual coin chart
        try:
            ticker_map = {
                'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'BNB': 'BNB-USD',
                'SOL': 'SOL-USD', 'ADA': 'ADA-USD', 'AVAX': 'AVAX-USD',
                'DOT': 'DOT-USD', 'LINK': 'LINK-USD', 'MATIC': 'MATIC-USD',
                'UNI': 'UNI-USD', 'LTC': 'LTC-USD'
            }
            
            ticker = ticker_map.get(selected_coin, f'{selected_coin}-USD')
            
            with st.spinner(f"Loading {selected_coin} chart..."):
                stock = yf.Ticker(ticker)
                hist = stock.history(period=time_period)
                
                if not hist.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=hist.index,
                        open=hist['Open'],
                        high=hist['High'],
                        low=hist['Low'],
                        close=hist['Close'],
                        name=selected_coin
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_coin} - {time_period.upper()} Candlestick Chart",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        height=400,
                        template="plotly_dark"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"⚠️ No historical data available for {selected_coin}")
                    
        except Exception as e:
            st.error(f"❌ Error loading {selected_coin} data: {str(e)}")
    
    # === 4. MARKET ANALYSIS ===
    st.header("4️⃣ Market Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Top Gainers (24h)")
        top_gainers = universe_df.nlargest(5, 'change_24h')[['symbol', 'name', 'change_24h']]
        for _, coin in top_gainers.iterrows():
            st.success(f"🚀 **{coin['symbol']}** ({coin['name']}): +{coin['change_24h']:.2f}%")
    
    with col2:
        st.subheader("📉 Top Losers (24h)")
        top_losers = universe_df.nsmallest(5, 'change_24h')[['symbol', 'name', 'change_24h']]
        for _, coin in top_losers.iterrows():
            st.error(f"📉 **{coin['symbol']}** ({coin['name']}): {coin['change_24h']:.2f}%")
    
    # === 5. SIGNIFICANT MOVEMENTS ===
    st.header("5️⃣ Significant Movements (30-day)")
    
    significant_moves = fetcher.detect_significant_movements(universe_df, threshold=20.0)
    
    if not significant_moves.empty:
        st.warning(f"⚠️ {len(significant_moves)} coins with >20% movement in 30 days")
        
        moves_display = significant_moves[['symbol', 'name', 'price', 'change_30d', 'movement_type']].copy()
        moves_display['Price'] = moves_display['price'].apply(lambda x: f"${x:,.4f}")
        moves_display['30d Change'] = moves_display['change_30d'].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            moves_display[['symbol', 'name', 'Price', '30d Change', 'movement_type']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No significant movements (>20%) in the last 30 days")
    
    # === FOOTER ===
    st.markdown("---")
    st.markdown("""
    **💎 Tier 1 Crypto Dashboard** | Data sources: CoinGecko API, Yahoo Finance  
    📊 Real-time tracking of top-tier cryptocurrencies | Updated every 30 seconds with auto-refresh
    """)

    # Export data to Google Sheets
    try:
        ##spreadsheet_url = "https://docs.google.com/spreadsheets/d/xxxxxx/edit#gid=0"  # Thay bằng URL thật hoặc lấy từ st.secrets
        if universe_df is not None and hasattr(universe_df, 'columns') and len(universe_df) > 0:
            data_to_export = [universe_df.columns.tolist()] + universe_df.values.tolist()
        else:
            data_to_export = []
            st.warning("⚠️ No universe data available for export")
        
        export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export)
        st.success("✅ Đã xuất dữ liệu lên Google Sheets thành công!")
    except Exception as e:
        st.error(f"❌ Lỗi xuất dữ liệu lên Google Sheets: {str(e)}")

# Force reload modules
import importlib
import sys

def force_reload_modules():
    """Force reload all Step 2 modules"""
    modules_to_reload = [
        'modules.technical_indicators',
        'modules.alerts_notifications', 
        'modules.backtest_strategy'
    ]
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

# Import Step 2 modules with force reload
if st.sidebar.button("🔄 Force Reload Modules"):
    force_reload_modules()
    st.rerun()

# Load data from Google Sheets

df_universe = load_tier1_universe_from_gsheet(spreadsheet_url)


# === RUN APP ===
if __name__ == "__main__":
    main()

# Thêm vào sidebar hoặc main area:
if st.button("🔧 Test Google Sheets Connection"):
    try:
        from data_access import get_google_sheets_client
        client = get_google_sheets_client()
        if client:
            st.success("✅ Google Sheets connection successful!")
            
            # Test mở spreadsheet
            spreadsheet_url = st.secrets.get("gsheet_url", "")
            if spreadsheet_url:
                sheet = client.open_by_url(spreadsheet_url)
                st.success(f"✅ Spreadsheet opened: {sheet.title}")
                
                # Test đọc data từ Tier1_Real_Time (không phải sheet đầu tiên)
                try:
                    worksheet = sheet.worksheet("Tier1_Real_Time")  # ← Sửa ở đây
                    data = worksheet.get_all_records()
                    st.success(f"✅ Data loaded from Tier1_Real_Time: {len(data)} rows")
                except Exception as e:
                    st.error(f"❌ Cannot read Tier1_Real_Time sheet: {e}")
                
            else:
                st.error("❌ No spreadsheet URL in secrets")
        else:
            st.error("❌ Failed to create Google Sheets client")
    except Exception as e:
        st.error(f"❌ Test failed: {str(e)}")
        
# Sửa button để dùng session state:
if st.button("🔄 Manual Update Tier1_Real_Time Sheet"):
    try:
        from data_access import update_tier1_realtime_full
        
        # Lấy data từ session state
        if 'universe_df' in st.session_state and 'spreadsheet_url' in st.session_state:
            universe_df = st.session_state.universe_df
            spreadsheet_url = st.session_state.spreadsheet_url
            
            if not universe_df.empty:
                st.info(f"📤 Updating sheet with {len(universe_df)} rows...")
                
                # Debug info
                st.write("**Data info before update:**")
                st.write(f"Type: {type(universe_df)}")
                st.write(f"Shape: {universe_df.shape}")
                st.write(f"Columns: {list(universe_df.columns)}")
                
                # Try update
                success = update_tier1_realtime_full(universe_df, spreadsheet_url)
                if success:
                    st.success("✅ Manual update successful!")
                else:
                    st.error("❌ Manual update failed!")
            else:
                st.error("❌ DataFrame is empty")
        else:
            st.error("❌ No data found in session. Please refresh page to load data first.")
    except Exception as e:
        st.error(f"❌ Manual update error: {str(e)}")

def fetch_live_tier1_data():
    """Fetch live data for Tier1 coins từ CoinGecko/Binance"""
    try:
        # Dynamic import để tránh syntax error
        from price_fetcher_fallback import fetch_current_prices
        
        # Danh sách Tier1 coins (có thể lấy từ Google Sheet hoặc hardcode)
        tier1_coins = [
            "bitcoin", "ethereum", "cardano", "solana", "binancecoin",
            "ripple", "polkadot", "chainlink", "litecoin", "avalanche-2",
            "polygon", "shiba-inu", "dogecoin", "stellar", "bitcoin-cash"
        ]
        
        st.info(f"🔄 Fetching live prices for {len(tier1_coins)} Tier1 coins...")
        
        # Fetch prices từ CoinGecko/Binance
        price_data = fetch_current_prices(tier1_coins)
        
        # Convert to DataFrame format giống Google Sheet
        rows = []
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for rank, coin_id in enumerate(tier1_coins, 1):
            if coin_id in price_data:
                data = price_data[coin_id]
                
                # Map coin_id to symbol và name
                symbol_map = {
                    "bitcoin": ("BTC", "Bitcoin"),
                    "ethereum": ("ETH", "Ethereum"),
                    "cardano": ("ADA", "Cardano"),
                    "solana": ("SOL", "Solana"),
                    "binancecoin": ("BNB", "BNB"),
                    "ripple": ("XRP", "XRP"),
                    "polkadot": ("DOT", "Polkadot"),
                    "chainlink": ("LINK", "Chainlink"),
                    "litecoin": ("LTC", "Litecoin"),
                    "avalanche-2": ("AVAX", "Avalanche")
                }
                
                symbol, name = symbol_map.get(coin_id, (coin_id.upper(), coin_id.title()))
                
                row = {
                    "Symbol": symbol,
                    "Name": name,
                    "Price": data.get("current_price", 0),
                    "Market_Cap": data.get("market_cap", 0),
                    "Change_24h": data.get("price_change_24h", 0),
                    "Change_7d": 0,  # Placeholder
                    "Change_30d": 0,  # Placeholder
                    "Volume_24h": 0,  # Placeholder
                    "Rank": rank,
                    "Source": "CoinGecko",
                    "Last_Updated": current_time
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        st.success(f"✅ Fetched live data for {len(df)} coins")
        return df
        
    except Exception as e:
        st.error(f"❌ Error fetching live data: {e}")
        return pd.DataFrame()

# Thêm Refresh Data button mới:
if st.button("🔄 Refresh Data from Live Sources"):
    try:
        # Fetch live data
        live_df = fetch_live_tier1_data()
        
        if not live_df.empty:
            # Save to session state
            st.session_state.live_df = live_df
            st.session_state.spreadsheet_url = st.secrets.get("gsheet_url", "")
            
            # Show preview
            with st.expander("📊 Live Data Preview"):
                st.dataframe(live_df)
            
            # Option to append to Google Sheet
            if st.button("📤 Append Live Data to Google Sheet"):
                from data_access import append_live_data_to_tier1
                spreadsheet_url = st.session_state.spreadsheet_url
                
                if spreadsheet_url:
                    success = append_live_data_to_tier1(live_df, spreadsheet_url)
                    if success:
                        st.success("✅ Live data appended successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to append live data")
                else:
                    st.error("❌ No spreadsheet URL found")
        else:
            st.error("❌ No live data fetched")
            
    except Exception as e:
        st.error(f"❌ Error refreshing data: {str(e)}")

def get_safe_column_data(df, target_patterns, default_value=0, operation='sum'):
    """Get data from DataFrame with safe column name matching"""
    if df.empty:
        return default_value
    
    # Find matching column
    for pattern in target_patterns:
        for col in df.columns:
            if pattern.lower() in col.lower():
                try:
                    if operation == 'sum':
                        return pd.to_numeric(df[col], errors='coerce').fillna(0).sum()
                    elif operation == 'mean':
                        return pd.to_numeric(df[col], errors='coerce').fillna(0).mean()
                    elif operation == 'list':
                        return df[col].tolist()
                    elif operation == 'count':
                        return len(df[col])
                    else:
                        return df[col]
                except Exception as e:
                    st.error(f"Error processing column {col}: {e}")
                    continue
    
    # Not found
    st.warning(f"⚠️ Columns {target_patterns} not found in: {list(df.columns)}")
    return default_value if operation != 'list' else []

# Sử dụng trong show_crypto_dashboard():
def show_crypto_dashboard():
    # Khởi tạo
    universe_df = pd.DataFrame()
    
    # Load data từ Tier1_Real_Time sheet
    try:
        spreadsheet_url = st.secrets.get("gsheet_url", "")
        if spreadsheet_url:
            from data_access import get_tier1_realtime_data
            universe_df = get_tier1_realtime_data(spreadsheet_url)
            
            if not universe_df.empty:
                # Lưu vào session state để button có thể access
                st.session_state.universe_df = universe_df
                st.session_state.spreadsheet_url = spreadsheet_url
                
                # Debug: show column names
                st.write("**Debug - Column names:**", list(universe_df.columns))
                st.write("**Debug - DataFrame shape:**", universe_df.shape)
                st.write("**Debug - First row:**", universe_df.iloc[0].to_dict() if len(universe_df) > 0 else "No data")
                
                st.info(f"📊 Loaded {len(universe_df)} coins from Tier1_Real_Time")
                # Hiển thị preview data
                with st.expander("📋 Preview Tier1 Data"):
                    st.dataframe(universe_df.head())
    except Exception as e:
        st.error(f"❌ Error loading Tier1 data: {e}")
    
    # Sửa line export:
    data_to_export = []
    #st.info("📊 Google Sheets temporarily disabled for debugging")

    st.title("💎 Tier 1 Crypto Portfolio Dashboard")
    st.markdown("**Real-time Tier 1 Cryptocurrency Universe Tracker**")
    st.markdown("---")
    
    # Sidebar controls
    st.sidebar.header("⚙️ Dashboard Controls")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=False)
    
    # Manual refresh
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        data_to_export = [universe_df.columns.tolist()] + universe_df.values.tolist()
        export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export)
        st.success("Đã lưu danh sách coin Tier 1 mới nhất lên Google Sheet!")
        st.cache_data.clear()
        st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Load real-time data
    with st.spinner("🔵 Fetching Tier 1 cryptocurrency data..."):
        fetcher = TierOnePriceFetcher()
        try:
            universe_df = fetcher.create_tier1_universe()
            if universe_df is None or not isinstance(universe_df, pd.DataFrame):
                universe_df = pd.DataFrame()
        except Exception as e:
            st.error(f"Lỗi khi lấy dữ liệu Tier 1: {e}")
            universe_df = pd.DataFrame()

    if isinstance(universe_df, pd.DataFrame) and not universe_df.empty:
        data_to_export = [universe_df.columns.tolist()] + universe_df.values.tolist()
        export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export)
        st.success("Đã lưu danh sách coin Tier 1 mới nhất lên Google Sheet!")
    else:
        st.error("Không lấy được dữ liệu Tier 1 coin.")

    # Store in session state for change detection
    if "last_universe" not in st.session_state:
        #st.session_state["last_universe"] = set(universe_df['symbol'].tolist())
        try:
            if not universe_df.empty:
                symbol_col = None
                for col in universe_df.columns:
                    if col.lower() in ['symbol', 'ticker', 'coin']:
                        symbol_col = col
                        break
                
                if symbol_col:
                    st.session_state["last_universe"] = set(universe_df[symbol_col].tolist())
                else:
                    st.session_state["last_universe"] = set()
            else:
                st.session_state["last_universe"] = set()
        except Exception as e:
            st.error(f"❌ Error setting last_universe: {e}")
            st.session_state["last_universe"] = set()
    
    # === 1. UNIVERSE OVERVIEW ===
    st.header("1️⃣ Tier 1 Crypto Universe Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Coins", len(universe_df), help="Number of Tier 1 cryptocurrencies")
    
    with col2:
        # Sửa line 455:
        try:
            if not universe_df.empty:
                # Thử các tên column có thể có
                mcap_col = None
                for col in universe_df.columns:
                    if col.lower() in ['market_cap', 'market cap', 'marketcap']:
                        mcap_col = col
                        break
        
            if mcap_col:
                total_mcap = pd.to_numeric(universe_df[mcap_col], errors='coerce').sum()
            else:
                total_mcap = 0
                st.warning(f"⚠️ Market cap column not found in: {list(universe_df.columns)}")
        except Exception as e:
            st.error(f"❌ Error calculating market cap: {e}")
            total_mcap = 0
        
        st.metric("Total Market Cap", f"${total_mcap/1e12:.2f}T", help="Combined market capitalization")
    
    with col3:
        try:
            if not universe_df.empty:
                # Tìm column change 24h với các tên có thể có
                change_col = None
                for col in universe_df.columns:
                    if 'change' in col.lower() and '24' in col:
                        change_col = col
                        break
                
                if change_col:
                    avg_change = pd.to_numeric(universe_df[change_col], errors='coerce').mean()
                else:
                    avg_change = 0
                    st.warning(f"⚠️ Change 24h column not found in: {list(universe_df.columns)}")
            else:
                avg_change = 0
        except Exception as e:
            st.error(f"❌ Error calculating avg change: {e}")
            avg_change = 0
        
        st.metric("Avg 24h Change", f"{avg_change:+.2f}%", help="Average 24-hour price change")
    
    with col4:
        current_time = dt.now().strftime("%H:%M:%S")
        st.metric("Last Update", current_time, help="Data refresh time")
    
    # Display universe table
    st.subheader("📊 Live Universe Data")
    
    # Format data for display
    display_df = universe_df.copy()
    display_df['Price'] = display_df['price'].apply(lambda x: f"${x:,.4f}")
    display_df['Market Cap'] = display_df['market_cap'].apply(lambda x: f"${x/1e9:.2f}B")
    display_df['24h Change'] = display_df['change_24h'].apply(lambda x: f"{x:+.2f}%")
    display_df['7d Change'] = display_df['change_7d'].apply(lambda x: f"{x:+.2f}%")
    display_df['Rank'] = display_df['rank']
    
    # Select columns to display
    display_columns = ['symbol', 'name', 'Price', 'Market Cap', '24h Change', '7d Change', 'Rank', 'source']
    st.dataframe(
        display_df[display_columns], 
        use_container_width=True,
        hide_index=True
    )
    
    # === 2. TOP 10 HISTORICAL CHARTS ===
    st.header("2️⃣ Top 10 Coins - Historical Price Charts (1 Year)")
    
    if len(universe_df) >= 10:
        top_10 = universe_df.head(10).copy()
        top_10_symbols = top_10['symbol'].tolist()
        
        with st.expander("📈 View Individual Price Charts", expanded=True):
            st.info(f"📊 Loading 1-year historical data for: {', '.join(top_10_symbols[:5])}...")
            
            # Get historical data
            historical_data = get_historical_prices_top10(top_10_symbols, period="1y")
            
            if historical_data:
                # Create individual charts in 2 columns
                col1, col2 = st.columns(2)
                
                for i, (symbol, data) in enumerate(historical_data.items()):
                    if i >= 10:  # Limit to 10 charts
                        break
                        
                    target_col = col1 if i % 2 == 0 else col2
                    
                    with target_col:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=data['dates'],
                            y=data['prices'],
                            mode='lines',
                            name=symbol,
                            line=dict(width=2),
                            hovertemplate=f'{symbol}<br>Date: %{{x}}<br>Price: $%{{y:,.2f}}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title=f"{symbol} - 1 Year Price Chart",
                            xaxis_title="Date",
                            yaxis_title="Price (USD)",
                            height=300,
                            showlegend=False,
                            template="plotly_dark"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Combined normalized chart
                st.subheader("📈 Combined Performance Comparison")
                
                fig_combined = go.Figure()
                
                for symbol, data in historical_data.items():
                    if data['prices']:
                        # Normalize prices to show percentage change from start
                        start_price = data['prices'][0]
                        normalized_prices = [(price/start_price - 1) * 100 for price in data['prices']]
                        
                        fig_combined.add_trace(go.Scatter(
                            x=data['dates'],
                            y=normalized_prices,
                            mode='lines',
                            name=symbol,
                            line=dict(width=2),
                            hovertemplate=f'{symbol}<br>Date: %{{x}}<br>Change: %{{y:+.2f}}%<extra></extra>'
                        ))
                
                fig_combined.update_layout(
                    title="Top 10 Coins - Normalized Performance (% change from 1 year ago)",
                    xaxis_title="Date",
                    yaxis_title="Price Change (%)",
                    height=500,
                    hovermode='x unified',
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig_combined, use_container_width=True)
            
            else:
                st.error("❌ Cannot load historical data")
    
    # === 3. INDIVIDUAL COIN ANALYSIS ===
    st.header("3️⃣ Individual Coin Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_coin = st.selectbox(
            "Select Cryptocurrency",
            options=universe_df['symbol'].tolist(),
            index=0
        )
    
    with col2:
        time_period = st.selectbox(
            "Time Period",
            options=["1y", "6mo", "3mo", "1mo", "7d"],
            index=0
        )
    
    # Display selected coin info and chart
    if selected_coin:
        coin_data = universe_df[universe_df['symbol'] == selected_coin].iloc[0]
        
        # Coin info cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Price", f"${coin_data['price']:,.4f}")
        with col2:
            st.metric("Market Cap", f"${coin_data['market_cap']/1e9:.2f}B")
        with col3:
            st.metric("24h Change", f"{coin_data['change_24h']:+.2f}%")
        with col4:
            st.metric("Market Rank", f"#{coin_data['rank']}")
        
        # Individual coin chart
        try:
            ticker_map = {
                'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'BNB': 'BNB-USD',
                'SOL': 'SOL-USD', 'ADA': 'ADA-USD', 'AVAX': 'AVAX-USD',
                'DOT': 'DOT-USD', 'LINK': 'LINK-USD', 'MATIC': 'MATIC-USD',
                'UNI': 'UNI-USD', 'LTC': 'LTC-USD'
            }
            
            ticker = ticker_map.get(selected_coin, f'{selected_coin}-USD')
            
            with st.spinner(f"Loading {selected_coin} chart..."):
                stock = yf.Ticker(ticker)
                hist = stock.history(period=time_period)
                
                if not hist.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=hist.index,
                        open=hist['Open'],
                        high=hist['High'],
                        low=hist['Low'],
                        close=hist['Close'],
                        name=selected_coin
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_coin} - {time_period.upper()} Candlestick Chart",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        height=400,
                        template="plotly_dark"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"⚠️ No historical data available for {selected_coin}")
                    
        except Exception as e:
            st.error(f"❌ Error loading {selected_coin} data: {str(e)}")
    
    # === 4. MARKET ANALYSIS ===
    st.header("4️⃣ Market Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Top Gainers (24h)")
        top_gainers = universe_df.nlargest(5, 'change_24h')[['symbol', 'name', 'change_24h']]
        for _, coin in top_gainers.iterrows():
            st.success(f"🚀 **{coin['symbol']}** ({coin['name']}): +{coin['change_24h']:.2f}%")
    
    with col2:
        st.subheader("📉 Top Losers (24h)")
        top_losers = universe_df.nsmallest(5, 'change_24h')[['symbol', 'name', 'change_24h']]
        for _, coin in top_losers.iterrows():
            st.error(f"📉 **{coin['symbol']}** ({coin['name']}): {coin['change_24h']:.2f}%")
    
    # === 5. SIGNIFICANT MOVEMENTS ===
    st.header("5️⃣ Significant Movements (30-day)")
    
    significant_moves = fetcher.detect_significant_movements(universe_df, threshold=20.0)
    
    if not significant_moves.empty:
        st.warning(f"⚠️ {len(significant_moves)} coins with >20% movement in 30 days")
        
        moves_display = significant_moves[['symbol', 'name', 'price', 'change_30d', 'movement_type']].copy()
        moves_display['Price'] = moves_display['price'].apply(lambda x: f"${x:,.4f}")
        moves_display['30d Change'] = moves_display['change_30d'].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            moves_display[['symbol', 'name', 'Price', '30d Change', 'movement_type']], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No significant movements (>20%) in the last 30 days")
    
    # === FOOTER ===
    st.markdown("---")
    st.markdown("""
    **💎 Tier 1 Crypto Dashboard** | Data sources: CoinGecko API, Yahoo Finance  
    📊 Real-time tracking of top-tier cryptocurrencies | Updated every 30 seconds with auto-refresh
    """)

    # Export data to Google Sheets
    try:
        ##spreadsheet_url = "https://docs.google.com/spreadsheets/d/xxxxxx/edit#gid=0"  # Thay bằng URL thật hoặc lấy từ st.secrets
        if universe_df is not None and hasattr(universe_df, 'columns') and len(universe_df) > 0:
            data_to_export = [universe_df.columns.tolist()] + universe_df.values.tolist()
        else:
            data_to_export = []
            st.warning("⚠️ No universe data available for export")
        
        export_tier1_to_existing_gsheet(spreadsheet_url, data_to_export)
        st.success("✅ Đã xuất dữ liệu lên Google Sheets thành công!")
    except Exception as e:
        st.error(f"❌ Lỗi xuất dữ liệu lên Google Sheets: {str(e)}")

# Force reload modules
import importlib
import sys

def force_reload_modules():
    """Force reload all Step 2 modules"""
    modules_to_reload = [
        'modules.technical_indicators',
        'modules.alerts_notifications', 
        'modules.backtest_strategy'
    ]
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

# Import Step 2 modules with force reload
if st.sidebar.button("🔄 Force Reload Modules"):
    force_reload_modules()
    st.rerun()

# Load data from Google Sheets

df_universe = load_tier1_universe_from_gsheet(spreadsheet_url)


# === RUN APP ===
if __name__ == "__main__":
    main()

# Thêm vào sidebar hoặc main area:
if st.button("🔧 Test Google Sheets Connection"):
    try:
        from data_access import get_google_sheets_client
        client = get_google_sheets_client()
        if client:
            st.success("✅ Google Sheets connection successful!")
            
            # Test mở spreadsheet
            spreadsheet_url = st.secrets.get("gsheet_url", "")
            if spreadsheet_url:
                sheet = client.open_by_url(spreadsheet_url)
                st.success(f"✅ Spreadsheet opened: {sheet.title}")
                
                # Test đọc data từ Tier1_Real_Time (không phải sheet đầu tiên)
                try:
                    worksheet = sheet.worksheet("Tier1_Real_Time")  # ← Sửa ở đây
                    data = worksheet.get_all_records()
                    st.success(f"✅ Data loaded from Tier1_Real_Time: {len(data)} rows")
                except Exception as e:
                    st.error(f"❌ Cannot read Tier1_Real_Time sheet: {e}")
                
            else:
                st.error("❌ No spreadsheet URL in secrets")
        else:
            st.error("❌ Failed to create Google Sheets client")
    except Exception as e:
        st.error(f"❌ Test failed: {str(e)}")
        
# Sửa button để dùng session state:
if st.button("🔄 Manual Update Tier1_Real_Time Sheet"):
    try:
        from data_access import update_tier1_realtime_full
        
        # Lấy data từ session state
        if 'universe_df' in st.session_state and 'spreadsheet_url' in st.session_state:
            universe_df = st.session_state.universe_df
            spreadsheet_url = st.session_state.spreadsheet_url
            
            if not universe_df.empty:
                st.info(f"📤 Updating sheet with {len(universe_df)} rows...")
                
                # Debug info
                st.write("**Data info before update:**")
                st.write(f"Type: {type(universe_df)}")
                st.write(f"Shape: {universe_df.shape}")
                st.write(f"Columns: {list(universe_df.columns)}")
                
                # Try update
                success = update_tier1_realtime_full(universe_df, spreadsheet_url)
                if success:
                    st.success("✅ Manual update successful!")
                else:
                    st.error("❌ Manual update failed!")
            else:
                st.error("❌ DataFrame is empty")
        else:
            st.error("❌ No data found in session. Please refresh page to load data first.")
    except Exception as e:
        st.error(f"❌ Manual update error: {str(e)}")

def fetch_live_tier1_data():
    """Fetch live data for Tier1 coins từ CoinGecko/Binance"""
    try:
        # Dynamic import để tránh syntax error
        from price_fetcher_fallback import fetch_current_prices
        
        # Danh sách Tier1 coins (có thể lấy từ Google Sheet hoặc hardcode)
        tier1_coins = [
            "bitcoin", "ethereum", "cardano", "solana", "binancecoin",
            "ripple", "polkadot", "chainlink", "litecoin", "avalanche-2",
            "polygon", "shiba-inu", "dogecoin", "stellar", "bitcoin-cash"
        ]
        
        st.info(f"🔄 Fetching live prices for {len(tier1_coins)} Tier1 coins...")
        
        # Fetch prices từ CoinGecko/Binance
        price_data = fetch_current_prices(tier1_coins)
        
        # Convert to DataFrame format giống Google Sheet
        rows = []
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for rank, coin_id in enumerate(tier1_coins, 1):
            if coin_id in price_data:
                data = price_data[coin_id]
                
                # Map coin_id to symbol và name
                symbol_map = {
                    "bitcoin": ("BTC", "Bitcoin"),
                    "ethereum": ("ETH", "Ethereum"),
                    "cardano": ("ADA", "Cardano"),
                    "solana": ("SOL", "Solana"),
                    "binancecoin": ("BNB", "BNB"),
                    "ripple": ("XRP", "XRP"),
                    "polkadot": ("DOT", "Polkadot"),
                    "chainlink": ("LINK", "Chainlink"),
                    "litecoin": ("LTC", "Litecoin"),
                    "avalanche-2": ("AVAX", "Avalanche")
                }
                
                symbol, name = symbol_map.get(coin_id, (coin_id.upper(), coin_id.title()))
                
                row = {
                    "Symbol": symbol,
                    "Name": name,
                    "Price": data.get("current_price", 0),
                    "Market_Cap": data.get("market_cap", 0),
                    "Change_24h": data.get("price_change_24h", 0),
                    "Change_7d": 0,  # Placeholder
                    "Change_30d": 0,  # Placeholder
                    "Volume_24h": 0,  # Placeholder
                    "Rank": rank,
                    "Source": "CoinGecko",
                    "Last_Updated": current_time
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        st.success(f"✅ Fetched live data for {len(df)} coins")
        return df
        
    except Exception as e:
        st.error(f"❌ Error fetching live data: {e}")
        return pd.DataFrame()

# Thêm Refresh Data button mới:
if st.button("🔄 Refresh Data from Live Sources"):
    try:
        # Fetch live data
        live_df = fetch_live_tier1_data()
        
        if not live_df.empty:
            # Save to session state
            st.session_state.live_df = live_df
            st.session_state.spreadsheet_url = st.secrets.get("gsheet_url", "")
            
            # Show preview
            with st.expander("📊 Live Data Preview"):
                st.dataframe(live_df)
            
            # Option to append to Google Sheet
            if st.button("📤 Append Live Data to Google Sheet"):
                from data_access import append_live_data_to_tier1
                spreadsheet_url = st.session_state.spreadsheet_url
                
                if spreadsheet_url:
                    success = append_live_data_to_tier1(live_df, spreadsheet_url)
                    if success:
                        st.success("✅ Live data appended successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to append live data")
                else:
                    st.error("❌ No spreadsheet URL found")
        else:
            st.error("❌ No live data fetched")
            
    except Exception as e:
        st.error(f"❌ Error refreshing data: {str(e)}")
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import talib
from typing import Dict, List, Tuple, Optional
import sqlite3
import json

class BacktestEngine:
    def __init__(self):
        self.db_path = "backtest_results.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for backtest results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                final_value REAL NOT NULL,
                total_return REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                losing_trades INTEGER NOT NULL,
                win_rate REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                sharpe_ratio REAL,
                parameters TEXT, -- JSON string of strategy parameters
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_crypto_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Fetch cryptocurrency data"""
        try:
            ticker = f"{symbol}-USD"
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            
            if data.empty:
                st.error(f"❌ No data found for {symbol}")
                return pd.DataFrame()
            
            # Calculate technical indicators
            data['SMA_20'] = talib.SMA(data['Close'].values, timeperiod=20)
            data['SMA_50'] = talib.SMA(data['Close'].values, timeperiod=50)
            data['EMA_12'] = talib.EMA(data['Close'].values, timeperiod=12)
            data['EMA_26'] = talib.EMA(data['Close'].values, timeperiod=26)
            data['RSI'] = talib.RSI(data['Close'].values, timeperiod=14)
            data['MACD'], data['MACD_signal'], data['MACD_hist'] = talib.MACD(data['Close'].values)
            data['BB_upper'], data['BB_middle'], data['BB_lower'] = talib.BBANDS(data['Close'].values)
            
            # Volume indicators
            data['Volume_SMA'] = talib.SMA(data['Volume'].values, timeperiod=20)
            
            return data.dropna()
            
        except Exception as e:
            st.error(f"❌ Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def sma_crossover_strategy(self, data: pd.DataFrame, short_period: int = 20, long_period: int = 50) -> Dict:
        """Simple Moving Average Crossover Strategy"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        signals['short_sma'] = talib.SMA(data['Close'].values, timeperiod=short_period)
        signals['long_sma'] = talib.SMA(data['Close'].values, timeperiod=long_period)
        
        # Generate signals
        signals['signal'] = 0
        signals['signal'][short_period:] = np.where(
            signals['short_sma'][short_period:] > signals['long_sma'][short_period:], 1, 0
        )
        signals['positions'] = signals['signal'].diff()
        
        return {
            'signals': signals,
            'strategy_name': f'SMA Crossover ({short_period}/{long_period})',
            'description': f'Buy when {short_period}-day SMA crosses above {long_period}-day SMA'
        }
    
    def rsi_strategy(self, data: pd.DataFrame, rsi_period: int = 14, oversold: int = 30, overbought: int = 70) -> Dict:
        """RSI Mean Reversion Strategy"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        signals['rsi'] = talib.RSI(data['Close'].values, timeperiod=rsi_period)
        
        # Generate signals
        signals['signal'] = 0
        signals['signal'] = np.where(signals['rsi'] < oversold, 1,  # Buy when oversold
                                   np.where(signals['rsi'] > overbought, -1, 0))  # Sell when overbought
        
        # Convert to position signals
        signals['positions'] = signals['signal'].diff()
        
        return {
            'signals': signals,
            'strategy_name': f'RSI Strategy ({oversold}/{overbought})',
            'description': f'Buy when RSI < {oversold}, Sell when RSI > {overbought}'
        }
    
    def macd_strategy(self, data: pd.DataFrame) -> Dict:
        """MACD Crossover Strategy"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        signals['macd'], signals['macd_signal'], signals['macd_hist'] = talib.MACD(data['Close'].values)
        
        # Generate signals
        signals['signal'] = 0
        signals['signal'] = np.where(signals['macd'] > signals['macd_signal'], 1, 0)
        signals['positions'] = signals['signal'].diff()
        
        return {
            'signals': signals,
            'strategy_name': 'MACD Crossover',
            'description': 'Buy when MACD line crosses above signal line'
        }
    
    def bollinger_bands_strategy(self, data: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict:
        """Bollinger Bands Mean Reversion Strategy"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        signals['bb_upper'], signals['bb_middle'], signals['bb_lower'] = talib.BBANDS(
            data['Close'].values, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev
        )
        
        # Generate signals
        signals['signal'] = 0
        signals['signal'] = np.where(signals['price'] < signals['bb_lower'], 1,  # Buy at lower band
                                   np.where(signals['price'] > signals['bb_upper'], -1, 0))  # Sell at upper band
        
        signals['positions'] = signals['signal'].diff()
        
        return {
            'signals': signals,
            'strategy_name': f'Bollinger Bands ({period}, {std_dev}σ)',
            'description': 'Buy at lower band, sell at upper band'
        }
    
    def golden_cross_strategy(self, data: pd.DataFrame) -> Dict:
        """Golden Cross Strategy (50/200 SMA)"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        signals['sma_50'] = talib.SMA(data['Close'].values, timeperiod=50)
        signals['sma_200'] = talib.SMA(data['Close'].values, timeperiod=200)
        
        # Generate signals
        signals['signal'] = 0
        signals['signal'][200:] = np.where(
            signals['sma_50'][200:] > signals['sma_200'][200:], 1, 0
        )
        signals['positions'] = signals['signal'].diff()
        
        return {
            'signals': signals,
            'strategy_name': 'Golden Cross (50/200 SMA)',
            'description': 'Buy when 50-day SMA crosses above 200-day SMA'
        }
    
    def run_backtest(self, signals_data: Dict, initial_capital: float = 10000, 
                    commission: float = 0.001) -> Dict:
        """Run backtest simulation"""
        
        signals = signals_data['signals'].copy()
        strategy_name = signals_data['strategy_name']
        
        # Initialize portfolio
        portfolio = pd.DataFrame(index=signals.index)
        portfolio['price'] = signals['price']
        portfolio['holdings'] = 0.0  # Number of shares held
        portfolio['cash'] = float(initial_capital)  # Cash available
        portfolio['total'] = portfolio['cash']  # Total portfolio value
        portfolio['returns'] = 0.0
        
        # Track trades
        trades = []
        position = 0  # 0 = no position, 1 = long position
        
        for i in range(1, len(signals)):
            # Copy previous values
            portfolio.iloc[i]['cash'] = portfolio.iloc[i-1]['cash']
            portfolio.iloc[i]['holdings'] = portfolio.iloc[i-1]['holdings']
            
            # Check for buy signal
            if signals.iloc[i]['positions'] == 1 and position == 0:  # Buy signal
                # Calculate shares to buy (invest all available cash)
                shares_to_buy = portfolio.iloc[i]['cash'] / (signals.iloc[i]['price'] * (1 + commission))
                cost = shares_to_buy * signals.iloc[i]['price'] * (1 + commission)
                
                if cost <= portfolio.iloc[i]['cash']:
                    portfolio.iloc[i]['holdings'] = shares_to_buy
                    portfolio.iloc[i]['cash'] -= cost
                    position = 1
                    
                    trades.append({
                        'date': signals.index[i],
                        'type': 'BUY',
                        'price': signals.iloc[i]['price'],
                        'shares': shares_to_buy,
                        'cost': cost
                    })
            
            # Check for sell signal
            elif (signals.iloc[i]['positions'] == -1 or signals.iloc[i]['signal'] == 0) and position == 1:  # Sell signal
                # Sell all holdings
                shares_to_sell = portfolio.iloc[i]['holdings']
                revenue = shares_to_sell * signals.iloc[i]['price'] * (1 - commission)
                
                portfolio.iloc[i]['cash'] += revenue
                portfolio.iloc[i]['holdings'] = 0
                position = 0
                
                trades.append({
                    'date': signals.index[i],
                    'type': 'SELL',
                    'price': signals.iloc[i]['price'],
                    'shares': shares_to_sell,
                    'revenue': revenue
                })
            
            # Calculate total portfolio value
            portfolio.iloc[i]['total'] = (portfolio.iloc[i]['cash'] + 
                                        portfolio.iloc[i]['holdings'] * signals.iloc[i]['price'])
            
            # Calculate returns
            if portfolio.iloc[i-1]['total'] > 0:
                portfolio.iloc[i]['returns'] = (portfolio.iloc[i]['total'] / portfolio.iloc[i-1]['total']) - 1
        
        # Calculate performance metrics
        final_value = portfolio['total'].iloc[-1]
        total_return = (final_value - initial_capital) / initial_capital * 100
        
        # Calculate trade statistics
        buy_trades = [t for t in trades if t['type'] == 'BUY']
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        
        winning_trades = 0
        losing_trades = 0
        trade_returns = []
        
        for i in range(min(len(buy_trades), len(sell_trades))):
            trade_return = (sell_trades[i]['revenue'] - buy_trades[i]['cost']) / buy_trades[i]['cost']
            trade_returns.append(trade_return)
            
            if trade_return > 0:
                winning_trades += 1
            else:
                losing_trades += 1
        
        total_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate maximum drawdown
        portfolio['cummax'] = portfolio['total'].cummax()
        portfolio['drawdown'] = (portfolio['total'] - portfolio['cummax']) / portfolio['cummax']
        max_drawdown = portfolio['drawdown'].min() * 100
        
        # Calculate Sharpe ratio
        if len(portfolio['returns']) > 1:
            sharpe_ratio = np.sqrt(252) * portfolio['returns'].mean() / portfolio['returns'].std() if portfolio['returns'].std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Buy and hold comparison
        buy_hold_return = (signals['price'].iloc[-1] - signals['price'].iloc[0]) / signals['price'].iloc[0] * 100
        
        return {
            'strategy_name': strategy_name,
            'portfolio': portfolio,
            'trades': trades,
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'signals': signals
        }
    
    def save_backtest_result(self, result: Dict, symbol: str, start_date: str, 
                           end_date: str, parameters: Dict = None):
        """Save backtest result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO backtest_results 
                (strategy_name, symbol, start_date, end_date, initial_capital, final_value, 
                 total_return, total_trades, winning_trades, losing_trades, win_rate, 
                 max_drawdown, sharpe_ratio, parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['strategy_name'],
                symbol,
                start_date,
                end_date,
                result['initial_capital'],
                result['final_value'],
                result['total_return'],
                result['total_trades'],
                result['winning_trades'],
                result['losing_trades'],
                result['win_rate'],
                result['max_drawdown'],
                result['sharpe_ratio'],
                json.dumps(parameters) if parameters else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error saving backtest result: {str(e)}")
    
    def get_backtest_history(self) -> pd.DataFrame:
        """Get historical backtest results"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM backtest_results 
                ORDER BY created_at DESC
            ''', conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"❌ Error getting backtest history: {str(e)}")
            return pd.DataFrame()
    
    def create_performance_chart(self, result: Dict) -> go.Figure:
        """Create backtest performance chart"""
        portfolio = result['portfolio']
        signals = result['signals']
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            subplot_titles=['Portfolio Value vs Buy & Hold', 'Price with Signals', 'Drawdown'],
            vertical_spacing=0.08,
            row_heights=[0.5, 0.3, 0.2]
        )
        
        # Portfolio performance
        fig.add_trace(
            go.Scatter(
                x=portfolio.index,
                y=portfolio['total'],
                mode='lines',
                name=result['strategy_name'],
                line=dict(color='#00CC96', width=2)
            ), row=1, col=1
        )
        
        # Buy and hold
        initial_shares = result['initial_capital'] / signals['price'].iloc[0]
        buy_hold_values = initial_shares * signals['price']
        
        fig.add_trace(
            go.Scatter(
                x=portfolio.index,
                y=buy_hold_values,
                mode='lines',
                name='Buy & Hold',
                line=dict(color='#FFA15A', width=2, dash='dash')
            ), row=1, col=1
        )
        
        # Price with buy/sell signals
        fig.add_trace(
            go.Scatter(
                x=signals.index,
                y=signals['price'],
                mode='lines',
                name='Price',
                line=dict(color='white', width=1),
                showlegend=False
            ), row=2, col=1
        )
        
        # Buy signals
        buy_signals = signals[signals['positions'] == 1]
        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['price'],
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(color='green', size=8, symbol='triangle-up'),
                    showlegend=False
                ), row=2, col=1
            )
        
        # Sell signals
        sell_signals = signals[signals['positions'] == -1]
        if not sell_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=sell_signals.index,
                    y=sell_signals['price'],
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(color='red', size=8, symbol='triangle-down'),
                    showlegend=False
                ), row=2, col=1
            )
        
        # Drawdown
        fig.add_trace(
            go.Scatter(
                x=portfolio.index,
                y=portfolio['drawdown'] * 100,
                mode='lines',
                name='Drawdown',
                fill='tonexty',
                line=dict(color='red', width=1),
                showlegend=False
            ), row=3, col=1
        )
        
        fig.update_layout(
            height=800,
            template="plotly_dark",
            title=f"Backtest Results: {result['strategy_name']}"
        )
        
        fig.update_yaxes(title_text="Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Price ($)", row=2, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=3, col=1)
        fig.update_xaxes(title_text="Date", row=3, col=1)
        
        return fig

# Streamlit interface for Backtesting
def show_backtest_dashboard():
    st.header("🔬 Strategy Backtesting")
    
    backtest_engine = BacktestEngine()
    
    tab1, tab2, tab3 = st.tabs(["🧪 Run Backtest", "📊 Results", "📜 History"])
    
    with tab1:
        st.subheader("🎯 Configure Backtest")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.selectbox(
                "Cryptocurrency",
                ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI']
            )
            
            period = st.selectbox(
                "Time Period",
                ['6mo', '1y', '2y', '5y', 'max'],
                index=1
            )
            
            initial_capital = st.number_input(
                "Initial Capital ($)",
                min_value=1000,
                value=10000,
                step=1000
            )
            
            commission = st.number_input(
                "Commission (%)",
                min_value=0.0,
                max_value=5.0,
                value=0.1,
                step=0.01,
                format="%.3f"
            ) / 100
        
        with col2:
            strategy = st.selectbox(
                "Strategy",
                [
                    "SMA Crossover",
                    "RSI Mean Reversion", 
                    "MACD Crossover",
                    "Bollinger Bands",
                    "Golden Cross"
                ]
            )
            
            # Strategy-specific parameters
            if strategy == "SMA Crossover":
                short_sma = st.slider("Short SMA Period", 5, 50, 20)
                long_sma = st.slider("Long SMA Period", 20, 200, 50)
                strategy_params = {'short_period': short_sma, 'long_period': long_sma}
                
            elif strategy == "RSI Mean Reversion":
                rsi_period = st.slider("RSI Period", 7, 21, 14)
                oversold = st.slider("Oversold Level", 20, 40, 30)
                overbought = st.slider("Overbought Level", 60, 80, 70)
                strategy_params = {'rsi_period': rsi_period, 'oversold': oversold, 'overbought': overbought}
                
            elif strategy == "Bollinger Bands":
                bb_period = st.slider("BB Period", 10, 30, 20)
                bb_std = st.slider("Standard Deviations", 1.5, 3.0, 2.0, step=0.1)
                strategy_params = {'period': bb_period, 'std_dev': bb_std}
                
            else:
                strategy_params = {}
        
        if st.button("🚀 Run Backtest", type="primary"):
            with st.spinner(f"Running backtest for {symbol}..."):
                # Get data
                data = backtest_engine.get_crypto_data(symbol, period)
                
                if not data.empty:
                    # Run strategy
                    if strategy == "SMA Crossover":
                        signals_data = backtest_engine.sma_crossover_strategy(
                            data, strategy_params['short_period'], strategy_params['long_period']
                        )
                    elif strategy == "RSI Mean Reversion":
                        signals_data = backtest_engine.rsi_strategy(
                            data, strategy_params['rsi_period'], 
                            strategy_params['oversold'], strategy_params['overbought']
                        )
                    elif strategy == "MACD Crossover":
                        signals_data = backtest_engine.macd_strategy(data)
                    elif strategy == "Bollinger Bands":
                        signals_data = backtest_engine.bollinger_bands_strategy(
                            data, strategy_params['period'], strategy_params['std_dev']
                        )
                    elif strategy == "Golden Cross":
                        signals_data = backtest_engine.golden_cross_strategy(data)
                    
                    # Run backtest
                    result = backtest_engine.run_backtest(
                        signals_data, initial_capital, commission
                    )
                    
                    # Save result
                    start_date = data.index[0].strftime('%Y-%m-%d')
                    end_date = data.index[-1].strftime('%Y-%m-%d')
                    backtest_engine.save_backtest_result(
                        result, symbol, start_date, end_date, strategy_params
                    )
                    
                    # Store in session state for display
                    st.session_state['backtest_result'] = result
                    st.success("✅ Backtest completed!")
    
    with tab2:
        if 'backtest_result' in st.session_state:
            result = st.session_state['backtest_result']
            
            # Performance metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Return",
                    f"{result['total_return']:+.2f}%",
                    help="Strategy total return"
                )
            
            with col2:
                st.metric(
                    "Buy & Hold Return",
                    f"{result['buy_hold_return']:+.2f}%",
                    help="Buy and hold strategy return"
                )
            
            with col3:
                st.metric(
                    "Max Drawdown",
                    f"{result['max_drawdown']:.2f}%",
                    help="Maximum portfolio decline"
                )
            
            with col4:
                st.metric(
                    "Sharpe Ratio",
                    f"{result['sharpe_ratio']:.2f}",
                    help="Risk-adjusted return"
                )
            
            # Additional metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", result['total_trades'])
            
            with col2:
                st.metric("Win Rate", f"{result['win_rate']:.1f}%")
            
            with col3:
                st.metric("Winning Trades", result['winning_trades'])
            
            with col4:
                st.metric("Losing Trades", result['losing_trades'])
            
            # Performance chart
            fig = backtest_engine.create_performance_chart(result)
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade details
            if result['trades']:
                st.subheader("💰 Trade Details")
                trades_df = pd.DataFrame(result['trades'])
                trades_df['date'] = pd.to_datetime(trades_df['date']).dt.strftime('%Y-%m-%d')
                
                if 'cost' in trades_df.columns:
                    trades_df['cost'] = trades_df['cost'].fillna(0).apply(lambda x: f"${x:,.2f}")
                if 'revenue' in trades_df.columns:
                    trades_df['revenue'] = trades_df['revenue'].fillna(0).apply(lambda x: f"${x:,.2f}")
                
                trades_df['price'] = trades_df['price'].apply(lambda x: f"${x:,.2f}")
                trades_df['shares'] = trades_df['shares'].apply(lambda x: f"{x:.6f}")
                
                st.dataframe(trades_df, use_container_width=True)
        else:
            st.info("📝 No backtest results yet. Run a backtest to see results here.")
    
    with tab3:
        st.subheader("📜 Backtest History")
        
        history_df = backtest_engine.get_backtest_history()
        
        if not history_df.empty:
            # Format for display
            display_df = history_df.copy()
            display_df['total_return'] = display_df['total_return'].apply(lambda x: f"{x:+.2f}%")
            display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%")
            display_df['max_drawdown'] = display_df['max_drawdown'].apply(lambda x: f"{x:.2f}%")
            display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(lambda x: f"{x:.2f}")
            display_df['final_value'] = display_df['final_value'].apply(lambda x: f"${x:,.2f}")
            display_df['initial_capital'] = display_df['initial_capital'].apply(lambda x: f"${x:,.2f}")
            display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Select columns to display
            columns_to_show = [
                'created_at', 'strategy_name', 'symbol', 'total_return', 
                'total_trades', 'win_rate', 'max_drawdown', 'sharpe_ratio'
            ]
            
            display_df = display_df.rename(columns={
                'created_at': 'Date',
                'strategy_name': 'Strategy',
                'symbol': 'Symbol',
                'total_return': 'Return',
                'total_trades': 'Trades',
                'win_rate': 'Win Rate',
                'max_drawdown': 'Max DD',
                'sharpe_ratio': 'Sharpe'
            })
            
            st.dataframe(display_df[['Date', 'Strategy', 'Symbol', 'Return', 'Trades', 'Win Rate', 'Max DD', 'Sharpe']], 
                        use_container_width=True)
            
            # Strategy comparison chart
            if len(history_df) > 1:
                st.subheader("📊 Strategy Comparison")
                
                fig = px.scatter(
                    history_df,
                    x='max_drawdown',
                    y='total_return',
                    color='strategy_name',
                    size='sharpe_ratio',
                    hover_data=['symbol', 'total_trades', 'win_rate'],
                    title="Return vs Risk (Max Drawdown)",
                    labels={
                        'max_drawdown': 'Max Drawdown (%)',
                        'total_return': 'Total Return (%)',
                        'strategy_name': 'Strategy'
                    }
                )
                
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 No backtest history yet. Run some backtests to see historical results.")

if __name__ == "__main__":
    show_backtest_dashboard()
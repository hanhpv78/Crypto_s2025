import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import ta

class IndicatorsEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def sma(self, window=20):
        # Đảm bảo truyền vào Series 1 chiều
        self.df[f'SMA_{window}'] = ta.trend.sma_indicator(self.df['Close'].squeeze(), window=window)
        return self.df

    def ema(self, window=20):
        self.df[f'EMA_{window}'] = ta.trend.ema_indicator(self.df['Close'].squeeze(), window=window)
        return self.df

    def rsi(self, window=14):
        self.df[f'RSI_{window}'] = ta.momentum.rsi(self.df['Close'].squeeze(), window=window)
        return self.df

    def macd(self, window_slow=26, window_fast=12, window_sign=9):
        self.df[f'MACD_{window_fast}_{window_slow}'] = ta.trend.macd(self.df['Close'].squeeze(), window_slow=window_slow, window_fast=window_fast).squeeze()
        self.df[f'MACD_SIGNAL_{window_fast}_{window_slow}_{window_sign}'] = ta.trend.macd_signal(self.df['Close'].squeeze(), window_slow=window_slow, window_fast=window_fast, window_sign=window_sign).squeeze()
        self.df[f'MACD_DIFF_{window_fast}_{window_slow}_{window_sign}'] = ta.trend.macd_diff(self.df['Close'].squeeze(), window_slow=window_slow, window_fast=window_fast, window_sign=window_sign).squeeze()
        return self.df

    def stochastic(self, window=14, smooth_window=3):
        self.df[f'STOCH_K_{window}'] = ta.momentum.stoch(self.df['High'].squeeze(), self.df['Low'].squeeze(), self.df['Close'].squeeze(), window=window, smooth_window=smooth_window).squeeze()
        self.df[f'STOCH_D_{window}'] = ta.momentum.stoch_signal(self.df['High'].squeeze(), self.df['Low'].squeeze(), self.df['Close'].squeeze(), window=window, smooth_window=smooth_window).squeeze()
        return self.df

    def cci(self, window=20):
        self.df[f'CCI_{window}'] = ta.trend.cci(self.df['High'].squeeze(), self.df['Low'].squeeze(), self.df['Close'].squeeze(), window=window).squeeze()
        return self.df

    def bollinger_bands(self, window=20, window_dev=2):
        indicator_bb = ta.volatility.BollingerBands(self.df['Close'].squeeze(), window=window, window_dev=window_dev)
        self.df[f'BB_High_{window}'] = indicator_bb.bollinger_hband().squeeze()
        self.df[f'BB_Low_{window}'] = indicator_bb.bollinger_lband().squeeze()
        self.df[f'BB_Mavg_{window}'] = indicator_bb.bollinger_mavg().squeeze()
        self.df[f'BB_Width_{window}'] = indicator_bb.bollinger_wband().squeeze()
        return self.df

    def atr(self, window=14):
        self.df[f'ATR_{window}'] = ta.volatility.average_true_range(
            self.df['High'].squeeze(), self.df['Low'].squeeze(), self.df['Close'].squeeze(), window=window
        ).squeeze()
        return self.df

    def obv(self):
        self.df['OBV'] = ta.volume.on_balance_volume(self.df['Close'].squeeze(), self.df['Volume'].squeeze()).squeeze()
        return self.df

    def volume_oscillator(self, short_window=12, long_window=26):
        short_vol = self.df['Volume'].rolling(window=short_window).mean()
        long_vol = self.df['Volume'].rolling(window=long_window).mean()
        self.df[f'Volume_Osc_{short_window}_{long_window}'] = ((short_vol - long_vol) / long_vol).squeeze()
        return self.df

    def chaikin_money_flow(self, window=20):
        self.df[f'CMF_{window}'] = ta.volume.chaikin_money_flow(
            self.df['High'].squeeze(), self.df['Low'].squeeze(), self.df['Close'].squeeze(), self.df['Volume'].squeeze(), window=window
        ).squeeze()
        return self.df

    def ichimoku(self):
        indicator_ichimoku = ta.trend.IchimokuIndicator(self.df['High'].squeeze(), self.df['Low'].squeeze())
        self.df['Ichimoku_A'] = indicator_ichimoku.ichimoku_a().squeeze()
        self.df['Ichimoku_B'] = indicator_ichimoku.ichimoku_b().squeeze()
        self.df['Ichimoku_base_line'] = indicator_ichimoku.ichimoku_base_line().squeeze()
        self.df['Ichimoku_conversion_line'] = indicator_ichimoku.ichimoku_conversion_line().squeeze()
        return self.df

    def heikin_ashi(self):
        ha_df = ta.utils.heikin_ashi(self.df)
        self.df['HA_Open'] = ha_df['open'].squeeze()
        self.df['HA_High'] = ha_df['high'].squeeze()
        self.df['HA_Low'] = ha_df['low'].squeeze()
        self.df['HA_Close'] = ha_df['close'].squeeze()
        return self.df

    def fib_retracement(self, lookback=100):
        # Fibonacci Retracement là mức giá, không phải chỉ báo động thời gian
        # Trả về các mức fibo dựa trên giá cao/thấp trong lookback
        max_price = self.df['High'].tail(lookback).max()
        min_price = self.df['Low'].tail(lookback).min()
        diff = max_price - min_price
        levels = {
            'Fib_0.0': max_price,
            'Fib_0.236': max_price - 0.236 * diff,
            'Fib_0.382': max_price - 0.382 * diff,
            'Fib_0.5': max_price - 0.5 * diff,
            'Fib_0.618': max_price - 0.618 * diff,
            'Fib_0.786': max_price - 0.786 * diff,
            'Fib_1.0': min_price
        }
        for k, v in levels.items():
            self.df[k] = v
        return self.df

    def pivot_points(self, lookback=1):
        # Tính Pivot Points cho n phiên gần nhất
        pivots = []
        for i in range(lookback):
            high = self.df['High'].iloc[-(i+2)]
            low = self.df['Low'].iloc[-(i+2)]
            close = self.df['Close'].iloc[-(i+2)]
            pivot = (high + low + close) / 3
            pivots.append(pivot)
        self.df['Pivot'] = pivots[-1] if pivots else None
        return self.df

    # Đề xuất thêm các chỉ báo hiệu quả khác:
    def adx(self, window=14):
        self.df[f'ADX_{window}'] = ta.trend.adx(
            self.df['High'].squeeze(), self.df['Low'].squeeze(), self.df['Close'].squeeze(), window=window
        ).squeeze()
        return self.df

    def williams_r(self, lbp=14):
        self.df[f'WilliamsR_{lbp}'] = ta.momentum.williams_r(
            self.df['High'].squeeze(), self.df['Low'].squeeze(), self.df['Close'].squeeze(), lbp=lbp
        ).squeeze()
        return self.df

    def get_df(self):
        return self.df

def show_technical_dashboard():
    """Simplified Technical Analysis Dashboard"""
    
    st.title("📈 Technical Indicators & Analysis")
    st.markdown("**Advanced technical analysis with multiple indicators**")
    st.markdown("---")
    
    # Coin selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_coins = st.multiselect(
            "Select Cryptocurrencies",
            options=['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI'],
            default=['BTC', 'ETH'],
            max_selections=5
        )
    
    with col2:
        timeframe = st.selectbox(
            "Timeframe",
            options=['1mo', '3mo', '6mo', '1y', '2y'],
            index=2
        )
    
    if selected_coins:
        # Technical signals overview
        st.subheader("🎯 Trading Signals Overview")
        
        signals_data = []
        for coin in selected_coins:
            with st.spinner(f"Analyzing {coin}..."):
                signals = get_technical_signals(coin, timeframe)
                if signals and signals['current_price'] > 0:
                    signals_data.append({
                        'Symbol': coin,
                        'Price': f"${signals['current_price']:,.2f}",
                        'RSI': f"{signals.get('rsi_value', 0):.1f} ({signals['rsi_signal']})",
                        'MA Signal': signals['ma_signal'],
                        'BB Signal': signals['bb_signal'],
                        'Overall': signals['recommendation']
                    })
        
        if signals_data:
            signals_df = pd.DataFrame(signals_data)
            
            # Style the dataframe with colors
            def highlight_signals(val):
                if 'BUY' in str(val):
                    return 'background-color: darkgreen; color: white'
                elif 'SELL' in str(val):
                    return 'background-color: darkred; color: white'
                elif 'NEUTRAL' in str(val) or 'HOLD' in str(val):
                    return 'background-color: orange; color: white'
                return ''
            
            styled_df = signals_df.style.applymap(
                highlight_signals, 
                subset=['RSI', 'MA Signal', 'BB Signal', 'Overall']
            )
            
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.warning("⚠️ Unable to load signal data. Please try again.")
        
        # Individual coin analysis
        st.subheader("📈 Individual Coin Analysis")
        
        if len(selected_coins) > 0:
            analysis_coin = st.selectbox(
                "Select coin for detailed analysis",
                options=selected_coins,
                index=0
            )
            
            if analysis_coin:
                # Create technical chart
                with st.spinner(f"Loading {analysis_coin} chart..."):
                    try:
                        chart = create_technical_chart(analysis_coin, timeframe)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                        else:
                            st.error("Unable to create chart")
                    except Exception as e:
                        st.error(f"Chart error: {str(e)}")
                
                # Detailed signals
                signals = get_technical_signals(analysis_coin, timeframe)
                if signals and signals['current_price'] > 0:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        rsi_val = signals.get('rsi_value', 0)
                        rsi_signal = signals['rsi_signal']
                        st.metric(
                            "RSI", 
                            f"{rsi_val:.1f}", 
                            help=f"Signal: {rsi_signal}"
                        )
                    
                    with col2:
                        st.metric(
                            "MA Signal", 
                            signals['ma_signal'],
                            help="Moving Average crossover signal"
                        )
                    
                    with col3:
                        st.metric(
                            "Overall", 
                            signals['recommendation'],
                            help="Combined technical analysis recommendation"
                        )
                    
                    # Signal explanations
                    st.subheader("📋 Signal Explanations")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**RSI Analysis:**")
                        if rsi_val < 30:
                            st.success("🟢 RSI indicates oversold condition - potential buying opportunity")
                        elif rsi_val > 70:
                            st.error("🔴 RSI indicates overbought condition - potential selling pressure")
                        else:
                            st.info("🟡 RSI in neutral zone - no strong signal")
                    
                    with col2:
                        st.markdown("**Moving Average Analysis:**")
                        if signals['ma_signal'] == 'BUY':
                            st.success("🟢 Price above moving averages - uptrend")
                        elif signals['ma_signal'] == 'SELL':
                            st.error("🔴 Price below moving averages - downtrend")
                        else:
                            st.info("🟡 Mixed moving average signals")


def get_technical_signals(coin, timeframe):
    """Get technical signals for selected coin and timeframe"""
    
    try:
        # Map coin symbols to yfinance tickers
        ticker_map = {
            'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'BNB': 'BNB-USD',
            'SOL': 'SOL-USD', 'ADA': 'ADA-USD', 'AVAX': 'AVAX-USD',
            'DOT': 'DOT-USD', 'LINK': 'LINK-USD', 'MATIC': 'MATIC-USD',
            'UNI': 'UNI-USD', 'LTC': 'LTC-USD'
        }
        
        ticker = ticker_map.get(coin, f'{coin}-USD')
        
        # Get data from yfinance
        stock = yf.Ticker(ticker)
        df = stock.history(period=timeframe)
        
        if df.empty:
            return {
                'rsi_signal': 'No Data',
                'ma_signal': 'No Data', 
                'bb_signal': 'No Data',
                'current_price': 0,
                'recommendation': 'HOLD'
            }
        
        current_price = df['Close'].iloc[-1]
        
        # Initialize indicators engine
        indicators = IndicatorsEngine(df)
        
        # Calculate indicators
        df = (
            indicators.rsi()
            .sma(window=20)
            .sma(window=50)
            .bollinger_bands()
            .get_df()
        )
        
        # Extract latest signals
        latest_data = df.iloc[-1]
        rsi_value = latest_data[f'RSI_14']
        sma_20 = latest_data[f'SMA_20']
        sma_50 = latest_data[f'SMA_50']
        bb_upper = latest_data[f'BB_High_20']
        bb_lower = latest_data[f'BB_Low_20']
        
        # Generate signals
        rsi_signal = 'BUY' if rsi_value < 30 else 'SELL' if rsi_value > 70 else 'NEUTRAL'
        ma_signal = 'BUY' if sma_20 > sma_50 else 'SELL' if sma_20 < sma_50 else 'NEUTRAL'
        bb_signal = 'SELL' if current_price >= bb_upper else 'BUY' if current_price <= bb_lower else 'NEUTRAL'
        
        # Overall recommendation
        signals = [rsi_signal, ma_signal, bb_signal]
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count:
            recommendation = 'STRONG BUY' if buy_count >= 2 else 'BUY'
        elif sell_count > buy_count:
            recommendation = 'STRONG SELL' if sell_count >= 2 else 'SELL'
        else:
            recommendation = 'HOLD'
        
        return {
            'rsi_signal': rsi_signal,
            'ma_signal': ma_signal,
            'bb_signal': bb_signal,
            'current_price': current_price,
            'recommendation': recommendation,
            'rsi_value': rsi_value,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower
        }
        
    except Exception as e:
        st.error(f"Error generating signals for {coin}: {str(e)}")
        return {
            'rsi_signal': 'ERROR',
            'ma_signal': 'ERROR',
            'bb_signal': 'ERROR',
            'current_price': 0,
            'recommendation': 'HOLD',
            'rsi_value': 0
        }


def create_technical_chart(coin, timeframe):
    """Create technical analysis chart"""
    
    try:
        # Map coin symbols to yfinance tickers
        ticker_map = {
            'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'BNB': 'BNB-USD',
            'SOL': 'SOL-USD', 'ADA': 'ADA-USD', 'AVAX': 'AVAX-USD',
            'DOT': 'DOT-USD', 'LINK': 'LINK-USD', 'MATIC': 'MATIC-USD',
            'UNI': 'UNI-USD', 'LTC': 'LTC-USD'
        }
        
        ticker = ticker_map.get(coin, f'{coin}-USD')
        
        # Get data
        stock = yf.Ticker(ticker)
        df = stock.history(period=timeframe)
        
        if df.empty:
            return None
        
        # Initialize indicators engine
        indicators = IndicatorsEngine(df)
        
        # Calculate indicators
        df = (
            indicators.sma(window=20)
            .sma(window=50)
            .bollinger_bands()
            .get_df()
        )
        
        # Create chart
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=f'{coin} Price',
            increasing_line_color='green',
            decreasing_line_color='red'
        ))
        
        # Moving averages
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_20'],
            mode='lines', name='SMA 20',
            line=dict(color='orange', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_50'],
            mode='lines', name='SMA 50',
            line=dict(color='purple', width=1)
        ))
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Upper'],
            mode='lines', name='BB Upper',
            line=dict(color='gray', width=1, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['BB_Lower'],
            mode='lines', name='BB Lower',
            line=dict(color='gray', width=1, dash='dash'),
            fill='tonexty', fillcolor='rgba(128,128,128,0.1)'
        ))
        
        fig.update_layout(
            title=f"{coin} Technical Analysis - {timeframe}",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            height=600,
            template="plotly_dark",
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating chart for {coin}: {str(e)}")
        return None

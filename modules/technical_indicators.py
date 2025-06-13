import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Optional imports with fallbacks
try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    st.warning("⚠️ TA library not available, using manual calculations")

def show_technical_dashboard():
    """Technical Analysis Dashboard with fallbacks"""
    
    if not TA_AVAILABLE:
        st.info("🔧 Loading technical analysis module with manual calculations...")
    
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
            signals = get_technical_signals(coin, timeframe)
            if signals:
                signals_data.append({
                    'Symbol': coin,
                    'Price': f"${signals['current_price']:,.2f}",
                    'RSI': f"{signals['rsi']['value']:.1f} ({signals['rsi']['signal']})",
                    'MACD': signals['macd']['trend'],
                    'Stochastic': signals['stochastic']['signal'],
                    'Overall': signals['overall_signal']
                })
        
        if signals_data:
            signals_df = pd.DataFrame(signals_data)
            
            # Color-code the signals
            def highlight_signals(val):
                if 'BUY' in str(val) or 'BULLISH' in str(val):
                    return 'background-color: green'
                elif 'SELL' in str(val) or 'BEARISH' in str(val):
                    return 'background-color: red'
                elif 'OVERSOLD' in str(val):
                    return 'background-color: darkgreen'
                elif 'OVERBOUGHT' in str(val):
                    return 'background-color: darkred'
                return ''
            
            st.dataframe(
                signals_df.style.applymap(highlight_signals, subset=['MACD', 'Overall', 'Stochastic']),
                use_container_width=True
            )
        
        # Individual coin analysis
        st.subheader("📈 Individual Coin Analysis")
        
        analysis_coin = st.selectbox(
            "Select coin for detailed analysis",
            options=selected_coins,
            index=0
        )
        
        if analysis_coin:
            # Create technical chart
            with st.spinner(f"Loading {analysis_coin} technical analysis..."):
                chart = create_technical_chart(analysis_coin, timeframe)
                st.plotly_chart(chart, use_container_width=True)
            
            # Detailed signals
            signals = get_technical_signals(analysis_coin, timeframe)
            if signals:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("RSI", f"{signals['rsi']['value']:.1f}", 
                             help=f"Signal: {signals['rsi']['signal']}")
                
                with col2:
                    st.metric("MACD Trend", signals['macd']['trend'],
                             help=f"Crossover: {signals['macd']['crossover']}")
                
                with col3:
                    st.metric("Overall Signal", signals['overall_signal'])
                
                # Detailed analysis
                with st.expander("📋 Detailed Technical Analysis"):
                    st.json(signals)

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
        import yfinance as yf
        stock = yf.Ticker(ticker)
        df = stock.history(period=timeframe)
        
        if df.empty:
            return {
                'rsi_signal': 'No Data',
                'ma_signal': 'No Data', 
                'bb_signal': 'No Data',
                'macd_signal': 'No Data',
                'current_price': 0,
                'recommendation': 'HOLD'
            }
        
        # Calculate indicators
        df = calculate_technical_indicators(df, 14, 20, 50, 20, 2.0)
        
        current_price = df['Close'].iloc[-1]
        current_rsi = df['RSI'].iloc[-1]
        
        # Generate signals
        rsi_signal = 'BUY' if current_rsi < 30 else 'SELL' if current_rsi > 70 else 'NEUTRAL'
        
        # Moving average signal
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        ma_signal = 'BUY' if current_price > sma_20 > sma_50 else 'SELL' if current_price < sma_20 < sma_50 else 'NEUTRAL'
        
        # Bollinger Bands signal  
        bb_upper = df['BB_Upper'].iloc[-1]
        bb_lower = df['BB_Lower'].iloc[-1]
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
            'macd_signal': 'NEUTRAL',  # Placeholder
            'current_price': current_price,
            'recommendation': recommendation,
            'rsi_value': current_rsi,
            'sma_20': sma_20,
            'sma_50': sma_50
        }
        
    except Exception as e:
        st.error(f"Error generating signals: {str(e)}")
        return {
            'rsi_signal': 'ERROR',
            'ma_signal': 'ERROR',
            'bb_signal': 'ERROR', 
            'macd_signal': 'ERROR',
            'current_price': 0,
            'recommendation': 'HOLD'
        }

# Thêm vào cuối file nếu chưa có
if __name__ == "__main__":
    show_technical_dashboard()
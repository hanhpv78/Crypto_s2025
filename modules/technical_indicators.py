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

if __name__ == "__main__":
    show_technical_dashboard()
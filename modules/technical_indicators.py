import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

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
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Calculate moving averages
        sma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
        
        # Calculate Bollinger Bands
        bb_middle = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        bb_upper = (bb_middle + (bb_std * 2)).iloc[-1]
        bb_lower = (bb_middle - (bb_std * 2)).iloc[-1]
        
        # Generate signals
        rsi_signal = 'BUY' if current_rsi < 30 else 'SELL' if current_rsi > 70 else 'NEUTRAL'
        ma_signal = 'BUY' if current_price > sma_20 > sma_50 else 'SELL' if current_price < sma_20 < sma_50 else 'NEUTRAL'
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
            'rsi_value': current_rsi,
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
        
        # Calculate indicators
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
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


if __name__ == "__main__":
    show_technical_dashboard()
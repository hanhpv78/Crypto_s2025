import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta

class TechnicalIndicators:
    def __init__(self):
        self.indicators_cache = {}
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band,
            'bandwidth': (upper_band - lower_band) / sma * 100
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k_percent': k_percent,
            'd_percent': d_percent
        }
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def get_technical_signals(self, symbol: str, period: str = "6mo") -> Dict:
        """Get comprehensive technical analysis signals"""
        try:
            # Fetch data
            ticker = f"{symbol}-USD"
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                return {}
            
            # Calculate all indicators
            rsi = self.calculate_rsi(df['Close'])
            macd_data = self.calculate_macd(df['Close'])
            bb_data = self.calculate_bollinger_bands(df['Close'])
            stoch_data = self.calculate_stochastic(df['High'], df['Low'], df['Close'])
            
            # Current values
            current_price = df['Close'].iloc[-1]
            current_rsi = rsi.iloc[-1]
            current_macd = macd_data['macd'].iloc[-1]
            current_signal = macd_data['signal'].iloc[-1]
            
            # Generate signals
            signals = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': df.index[-1],
                'rsi': {
                    'value': current_rsi,
                    'signal': 'OVERSOLD' if current_rsi < 30 else 'OVERBOUGHT' if current_rsi > 70 else 'NEUTRAL',
                    'strength': 'STRONG' if current_rsi < 20 or current_rsi > 80 else 'MODERATE' if current_rsi < 40 or current_rsi > 60 else 'WEAK'
                },
                'macd': {
                    'macd': current_macd,
                    'signal': current_signal,
                    'histogram': macd_data['histogram'].iloc[-1],
                    'trend': 'BULLISH' if current_macd > current_signal else 'BEARISH',
                    'crossover': self._detect_macd_crossover(macd_data['macd'], macd_data['signal'])
                },
                'bollinger': {
                    'position': self._get_bb_position(current_price, bb_data),
                    'squeeze': bb_data['bandwidth'].iloc[-1] < bb_data['bandwidth'].rolling(20).mean().iloc[-1]
                },
                'stochastic': {
                    'k': stoch_data['k_percent'].iloc[-1],
                    'd': stoch_data['d_percent'].iloc[-1],
                    'signal': 'OVERSOLD' if stoch_data['k_percent'].iloc[-1] < 20 else 'OVERBOUGHT' if stoch_data['k_percent'].iloc[-1] > 80 else 'NEUTRAL'
                },
                'overall_signal': self._calculate_overall_signal(current_rsi, current_macd, current_signal, stoch_data)
            }
            
            return signals
            
        except Exception as e:
            st.error(f"Error calculating indicators for {symbol}: {str(e)}")
            return {}
    
    def _detect_macd_crossover(self, macd: pd.Series, signal: pd.Series) -> str:
        """Detect MACD crossover signals"""
        if len(macd) < 2:
            return "NO_DATA"
        
        current_diff = macd.iloc[-1] - signal.iloc[-1]
        previous_diff = macd.iloc[-2] - signal.iloc[-2]
        
        if previous_diff <= 0 and current_diff > 0:
            return "BULLISH_CROSSOVER"
        elif previous_diff >= 0 and current_diff < 0:
            return "BEARISH_CROSSOVER"
        else:
            return "NO_CROSSOVER"
    
    def _get_bb_position(self, price: float, bb_data: Dict) -> str:
        """Get position relative to Bollinger Bands"""
        upper = bb_data['upper'].iloc[-1]
        lower = bb_data['lower'].iloc[-1]
        middle = bb_data['middle'].iloc[-1]
        
        if price > upper:
            return "ABOVE_UPPER"
        elif price < lower:
            return "BELOW_LOWER"
        elif price > middle:
            return "UPPER_HALF"
        else:
            return "LOWER_HALF"
    
    def _calculate_overall_signal(self, rsi: float, macd: float, signal: float, stoch_data: Dict) -> str:
        """Calculate overall trading signal"""
        bullish_signals = 0
        bearish_signals = 0
        
        # RSI signals
        if rsi < 30:
            bullish_signals += 1
        elif rsi > 70:
            bearish_signals += 1
        
        # MACD signals
        if macd > signal:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # Stochastic signals
        if stoch_data['k_percent'].iloc[-1] < 20:
            bullish_signals += 1
        elif stoch_data['k_percent'].iloc[-1] > 80:
            bearish_signals += 1
        
        if bullish_signals > bearish_signals:
            return "BUY"
        elif bearish_signals > bullish_signals:
            return "SELL"
        else:
            return "HOLD"
    
    def create_technical_chart(self, symbol: str, period: str = "6mo") -> go.Figure:
        """Create comprehensive technical analysis chart"""
        try:
            ticker = f"{symbol}-USD"
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                return go.Figure()
            
            # Calculate indicators
            rsi = self.calculate_rsi(df['Close'])
            macd_data = self.calculate_macd(df['Close'])
            bb_data = self.calculate_bollinger_bands(df['Close'])
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=[f'{symbol} Price & Bollinger Bands', 'RSI', 'MACD'],
                row_heights=[0.6, 0.2, 0.2]
            )
            
            # Price and Bollinger Bands
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name=symbol
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index, y=bb_data['upper'],
                line=dict(color='red', width=1),
                name='BB Upper'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index, y=bb_data['middle'],
                line=dict(color='blue', width=1),
                name='BB Middle'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index, y=bb_data['lower'],
                line=dict(color='red', width=1),
                name='BB Lower',
                fill='tonexty'
            ), row=1, col=1)
            
            # RSI
            fig.add_trace(go.Scatter(
                x=df.index, y=rsi,
                line=dict(color='purple', width=2),
                name='RSI'
            ), row=2, col=1)
            
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            # MACD
            fig.add_trace(go.Scatter(
                x=df.index, y=macd_data['macd'],
                line=dict(color='blue', width=2),
                name='MACD'
            ), row=3, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index, y=macd_data['signal'],
                line=dict(color='red', width=2),
                name='Signal'
            ), row=3, col=1)
            
            fig.add_trace(go.Bar(
                x=df.index, y=macd_data['histogram'],
                name='Histogram',
                marker_color='gray'
            ), row=3, col=1)
            
            fig.update_layout(
                title=f"{symbol} Technical Analysis",
                height=800,
                showlegend=True,
                template="plotly_dark"
            )
            
            fig.update_xaxes(rangeslider_visible=False)
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating chart for {symbol}: {str(e)}")
            return go.Figure()

# Streamlit interface for Technical Indicators
def show_technical_analysis():
    st.header("📊 Technical Analysis Dashboard")
    
    # Initialize indicators
    indicators = TechnicalIndicators()
    
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
            signals = indicators.get_technical_signals(coin, timeframe)
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
                chart = indicators.create_technical_chart(analysis_coin, timeframe)
                st.plotly_chart(chart, use_container_width=True)
            
            # Detailed signals
            signals = indicators.get_technical_signals(analysis_coin, timeframe)
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
    show_technical_analysis()
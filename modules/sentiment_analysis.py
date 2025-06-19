import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import time

class SentimentAnalyzer:
    def __init__(self):
        self.db_path = "sentiment_data.db"
        self.fear_greed_api = "https://api.alternative.me/fng/"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for sentiment data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Fear & Greed Index table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fear_greed_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value INTEGER NOT NULL,
                value_classification TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Social sentiment table (manual entries or future API integration)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_sentiment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                platform TEXT NOT NULL, -- Twitter, Reddit, etc.
                sentiment_score REAL NOT NULL, -- -1 to 1
                mention_count INTEGER DEFAULT 0,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                neutral_count INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # News sentiment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_sentiment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT,
                sentiment_score REAL NOT NULL,
                sentiment_label TEXT NOT NULL,
                published_date TEXT NOT NULL,
                source TEXT,
                symbols TEXT, -- JSON string of related symbols
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_fear_greed_index(self, days: int = 30) -> Dict:
        """Fetch Fear & Greed Index data"""
        try:
            url = f"{self.fear_greed_api}?limit={days}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                st.error(f"❌ Failed to fetch Fear & Greed Index: {response.status_code}")
                return {}
                
        except Exception as e:
            st.error(f"❌ Error fetching Fear & Greed Index: {str(e)}")
            return {}
    
    def save_fear_greed_data(self, data: Dict):
        """Save Fear & Greed Index data to database"""
        try:
            if 'data' not in data:
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for entry in data['data']:
                # Check if entry already exists
                cursor.execute(
                    'SELECT id FROM fear_greed_index WHERE timestamp = ?',
                    (entry['timestamp'],)
                )
                
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO fear_greed_index (value, value_classification, timestamp)
                        VALUES (?, ?, ?)
                    ''', (
                        int(entry['value']),
                        entry['value_classification'],
                        entry['timestamp']
                    ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error saving Fear & Greed data: {str(e)}")
    
    def get_fear_greed_history(self, days: int = 30) -> pd.DataFrame:
        """Get Fear & Greed Index history from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # First try to get from database
            df = pd.read_sql_query('''
                SELECT * FROM fear_greed_index 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', conn, params=(days,))
            
            conn.close()
            
            if df.empty or len(df) < days:
                # Fetch fresh data if database is empty or incomplete
                fresh_data = self.fetch_fear_greed_index(days)
                if fresh_data:
                    self.save_fear_greed_data(fresh_data)
                    
                    # Try again from database
                    conn = sqlite3.connect(self.db_path)
                    df = pd.read_sql_query('''
                        SELECT * FROM fear_greed_index 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', conn, params=(days,))
                    conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['timestamp'], unit='s')
                df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            st.error(f"❌ Error getting Fear & Greed history: {str(e)}")
            return pd.DataFrame()
    
    def analyze_text_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text (simplified version)"""
        # This is a simplified sentiment analysis
        # In production, you'd use VADER, TextBlob, or API services
        
        positive_words = [
            'bullish', 'moon', 'pump', 'rally', 'breakout', 'surge', 'rocket',
            'gains', 'profit', 'buy', 'bullrun', 'golden', 'breakout', 'support',
            'resistance', 'uptend', 'accumulate', 'hodl', 'diamond', 'hands'
        ]
        
        negative_words = [
            'bearish', 'dump', 'crash', 'fall', 'drop', 'sell', 'loss',
            'decline', 'correction', 'fear', 'panic', 'weak', 'breakdown',
            'downtrend', 'resistance', 'support', 'liquidation', 'fud'
        ]
        
        neutral_words = [
            'stable', 'sideways', 'consolidation', 'range', 'wait', 'watch',
            'analysis', 'technical', 'fundamental', 'market', 'trading'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        neutral_count = sum(1 for word in neutral_words if word in text_lower)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            sentiment_score = 0
            sentiment_label = "Neutral"
        else:
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
            
            if sentiment_score > 0.1:
                sentiment_label = "Positive"
            elif sentiment_score < -0.1:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"
        
        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'confidence': min(total_sentiment_words / 10, 1.0)  # Confidence based on word count
        }
    
    def add_manual_sentiment(self, symbol: str, platform: str, sentiment_text: str) -> bool:
        """Add manual sentiment analysis"""
        try:
            sentiment_result = self.analyze_text_sentiment(sentiment_text)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO social_sentiment 
                (symbol, platform, sentiment_score, positive_count, negative_count, neutral_count, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                platform,
                sentiment_result['sentiment_score'],
                sentiment_result['positive_count'],
                sentiment_result['negative_count'],
                sentiment_result['neutral_count'],
                datetime.now().strftime('%Y-%m-%d')
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error adding sentiment: {str(e)}")
            return False
    
    def get_sentiment_summary(self, symbol: str = None, days: int = 7) -> Dict:
        """Get sentiment summary for a symbol or overall market"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get social sentiment
            if symbol:
                social_df = pd.read_sql_query('''
                    SELECT * FROM social_sentiment 
                    WHERE symbol = ? AND date >= date('now', '-{} days')
                    ORDER BY date DESC
                '''.format(days), conn, params=(symbol,))
            else:
                social_df = pd.read_sql_query('''
                    SELECT * FROM social_sentiment 
                    WHERE date >= date('now', '-{} days')
                    ORDER BY date DESC
                '''.format(days), conn)
            
            # Get Fear & Greed Index
            fg_df = self.get_fear_greed_history(days)
            
            conn.close()
            
            # Calculate averages
            avg_social_sentiment = social_df['sentiment_score'].mean() if not social_df.empty else 0
            current_fear_greed = fg_df['value'].iloc[-1] if not fg_df.empty else 50
            
            return {
                'avg_social_sentiment': avg_social_sentiment,
                'current_fear_greed': current_fear_greed,
                'social_data_points': len(social_df),
                'fear_greed_data_points': len(fg_df),
                'social_df': social_df,
                'fear_greed_df': fg_df
            }
            
        except Exception as e:
            st.error(f"❌ Error getting sentiment summary: {str(e)}")
            return {}
    
    def create_fear_greed_chart(self, days: int = 30) -> go.Figure:
        """Create Fear & Greed Index chart"""
        df = self.get_fear_greed_history(days)
        
        if df.empty:
            return go.Figure()
        
        # Define color mapping
        def get_color(value):
            if value <= 25:
                return '#FF4444'  # Extreme Fear - Red
            elif value <= 45:
                return '#FF8800'  # Fear - Orange
            elif value <= 55:
                return '#FFDD00'  # Neutral - Yellow
            elif value <= 75:
                return '#88DD00'  # Greed - Light Green
            else:
                return '#00CC44'  # Extreme Greed - Green
        
        colors = [get_color(val) for val in df['value']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['value'],
            mode='lines+markers',
            name='Fear & Greed Index',
            line=dict(color='white', width=2),
            marker=dict(color=colors, size=8),
            text=df['value_classification'],
            hovertemplate='<b>%{text}</b><br>Value: %{y}<br>Date: %{x}<extra></extra>'
        ))
        
        # Add horizontal lines for zones
        fig.add_hline(y=25, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_hline(y=45, line_dash="dash", line_color="orange", opacity=0.5)
        fig.add_hline(y=55, line_dash="dash", line_color="yellow", opacity=0.5)
        fig.add_hline(y=75, line_dash="dash", line_color="lightgreen", opacity=0.5)
        
        # Add zone annotations
        fig.add_annotation(x=df['date'].iloc[-1], y=12, text="Extreme Fear", 
                          showarrow=False, font=dict(color="red", size=10))
        fig.add_annotation(x=df['date'].iloc[-1], y=35, text="Fear", 
                          showarrow=False, font=dict(color="orange", size=10))
        fig.add_annotation(x=df['date'].iloc[-1], y=50, text="Neutral", 
                          showarrow=False, font=dict(color="yellow", size=10))
        fig.add_annotation(x=df['date'].iloc[-1], y=65, text="Greed", 
                          showarrow=False, font=dict(color="lightgreen", size=10))
        fig.add_annotation(x=df['date'].iloc[-1], y=88, text="Extreme Greed", 
                          showarrow=False, font=dict(color="green", size=10))
        
        fig.update_layout(
            title="Crypto Fear & Greed Index",
            xaxis_title="Date",
            yaxis_title="Fear & Greed Index",
            yaxis=dict(range=[0, 100]),
            template="plotly_dark",
            height=500
        )
        
        return fig
    
    def create_sentiment_gauge(self, value: float, title: str) -> go.Figure:
        """Create sentiment gauge chart"""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "white"},
                'steps': [
                    {'range': [0, 25], 'color': "#FF4444"},
                    {'range': [25, 45], 'color': "#FF8800"},
                    {'range': [45, 55], 'color': "#FFDD00"},
                    {'range': [55, 75], 'color': "#88DD00"},
                    {'range': [75, 100], 'color': "#00CC44"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_dark",
            height=300
        )
        
        return fig

# Streamlit interface for Sentiment Analysis
def show_sentiment_dashboard():
    st.header("🧠 Market Sentiment Analysis")
    
    sentiment_analyzer = SentimentAnalyzer()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "😨 Fear & Greed", "💬 Social Sentiment", "📰 News Analysis"])
    
    with tab1:
        st.subheader("🎯 Market Sentiment Overview")
        
        # Get overall sentiment summary
        summary = sentiment_analyzer.get_sentiment_summary(days=7)
        
        if summary:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Current Fear & Greed Index
                current_fg = summary.get('current_fear_greed', 50)
                fg_classification = (
                    "Extreme Fear" if current_fg <= 25 else
                    "Fear" if current_fg <= 45 else
                    "Neutral" if current_fg <= 55 else
                    "Greed" if current_fg <= 75 else
                    "Extreme Greed"
                )
                
                st.metric(
                    "Fear & Greed Index",
                    f"{current_fg}/100",
                    fg_classification
                )
                
                # Gauge chart for Fear & Greed
                fg_gauge = sentiment_analyzer.create_sentiment_gauge(current_fg, "Fear & Greed")
                st.plotly_chart(fg_gauge, use_container_width=True)
            
            with col2:
                # Social sentiment average
                social_sentiment = summary.get('avg_social_sentiment', 0)
                social_percentage = ((social_sentiment + 1) / 2) * 100  # Convert -1 to 1 scale to 0-100
                
                social_label = (
                    "Very Negative" if social_percentage <= 20 else
                    "Negative" if social_percentage <= 40 else
                    "Neutral" if social_percentage <= 60 else
                    "Positive" if social_percentage <= 80 else
                    "Very Positive"
                )
                
                st.metric(
                    "Social Sentiment",
                    f"{social_percentage:.0f}/100",
                    social_label
                )
                
                # Gauge chart for Social Sentiment
                social_gauge = sentiment_analyzer.create_sentiment_gauge(social_percentage, "Social Sentiment")
                st.plotly_chart(social_gauge, use_container_width=True)
            
            with col3:
                # Combined sentiment score
                combined_score = (current_fg + social_percentage) / 2
                
                combined_label = (
                    "Very Bearish" if combined_score <= 25 else
                    "Bearish" if combined_score <= 45 else
                    "Neutral" if combined_score <= 55 else
                    "Bullish" if combined_score <= 75 else
                    "Very Bullish"
                )
                
                st.metric(
                    "Combined Sentiment",
                    f"{combined_score:.0f}/100",
                    combined_label
                )
                
                # Gauge chart for Combined Sentiment
                combined_gauge = sentiment_analyzer.create_sentiment_gauge(combined_score, "Combined Sentiment")
                st.plotly_chart(combined_gauge, use_container_width=True)
            
            # Sentiment interpretation
            st.subheader("🔍 Sentiment Interpretation")
            
            with st.container():
                if combined_score <= 25:
                    st.error("🐻 **Very Bearish**: Market sentiment is extremely negative. This could indicate a buying opportunity for contrarian investors.")
                elif combined_score <= 45:
                    st.warning("📉 **Bearish**: Market sentiment is negative. Caution is advised, but opportunities may arise.")
                elif combined_score <= 55:
                    st.info("😐 **Neutral**: Market sentiment is balanced. No strong directional bias.")
                elif combined_score <= 75:
                    st.success("📈 **Bullish**: Market sentiment is positive. Good environment for crypto investments.")
                else:
                    st.error("🚨 **Very Bullish**: Market sentiment is extremely positive. Be cautious of potential market tops.")
        
        else:
            st.info("📝 No sentiment data available. Check the other tabs to add data.")
    
    with tab2:
        st.subheader("😨 Crypto Fear & Greed Index")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            days = st.slider("Days to show", 7, 365, 30)
            
            # Fear & Greed Index chart
            fg_chart = sentiment_analyzer.create_fear_greed_chart(days)
            st.plotly_chart(fg_chart, use_container_width=True)
        
        with col2:
            st.markdown("### 📖 Fear & Greed Index Guide")
            
            st.markdown("""
            **Index Values:**
            - **0-25**: 🔴 Extreme Fear
            - **26-45**: 🟠 Fear  
            - **46-55**: 🟡 Neutral
            - **56-75**: 🟢 Greed
            - **76-100**: 🔴 Extreme Greed
            
            **Interpretation:**
            - **Extreme Fear**: Potential buying opportunity
            - **Fear**: Market oversold, consider accumulating
            - **Neutral**: Balanced market conditions
            - **Greed**: Market getting expensive, be cautious
            - **Extreme Greed**: Potential selling opportunity
            """)
        
        # Refresh Fear & Greed data
        if st.button("🔄 Refresh Fear & Greed Data"):
            with st.spinner("Fetching latest Fear & Greed Index..."):
                fresh_data = sentiment_analyzer.fetch_fear_greed_index(30)
                if fresh_data:
                    sentiment_analyzer.save_fear_greed_data(fresh_data)
                    st.success("✅ Fear & Greed Index updated!")
                    st.rerun()
        
        # Historical data table
        fg_df = sentiment_analyzer.get_fear_greed_history(days)
        if not fg_df.empty:
            st.subheader("📋 Historical Data")
            display_df = fg_df[['date', 'value', 'value_classification']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df = display_df.rename(columns={
                'date': 'Date',
                'value': 'Index Value',
                'value_classification': 'Classification'
            })
            st.dataframe(display_df.head(10), use_container_width=True)
    
    with tab3:
        st.subheader("💬 Social Sentiment Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ➕ Add Sentiment Data")
            
            symbol = st.selectbox(
                "Cryptocurrency",
                ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI', 'Overall Market']
            )
            
            platform = st.selectbox(
                "Platform",
                ['Twitter', 'Reddit', 'Discord', 'Telegram', 'YouTube', 'News', 'Other']
            )
            
            sentiment_text = st.text_area(
                "Sentiment Text/Keywords",
                placeholder="Enter text, keywords, or general sentiment observations...",
                help="Enter text that represents the general sentiment. Use keywords like 'bullish', 'bearish', 'moon', 'dump', etc."
            )
            
            if st.button("📊 Analyze & Add Sentiment"):
                if sentiment_text.strip():
                    if sentiment_analyzer.add_manual_sentiment(symbol, platform, sentiment_text):
                        st.success("✅ Sentiment analysis added!")
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter some text to analyze.")
        
        with col2:
            st.markdown("#### 🎯 Sentiment Keywords Guide")
            
            with st.expander("🟢 Positive Keywords"):
                st.markdown("""
                - bullish, moon, pump, rally, breakout
                - surge, rocket, gains, profit, buy
                - bullrun, golden, support, uptend
                - accumulate, hodl, diamond hands
                """)
            
            with st.expander("🔴 Negative Keywords"):
                st.markdown("""
                - bearish, dump, crash, fall, drop
                - sell, loss, decline, correction
                - fear, panic, weak, breakdown
                - downtrend, liquidation, fud
                """)
            
            with st.expander("🟡 Neutral Keywords"):
                st.markdown("""
                - stable, sideways, consolidation
                - range, wait, watch, analysis
                - technical, fundamental, market
                """)
        
        # Display recent sentiment data
        summary = sentiment_analyzer.get_sentiment_summary(days=30)
        if summary and not summary.get('social_df', pd.DataFrame()).empty:
            st.subheader("📈 Recent Sentiment Data")
            
            social_df = summary['social_df']
            
            # Sentiment by symbol chart
            if len(social_df) > 0:
                symbol_sentiment = social_df.groupby('symbol')['sentiment_score'].mean().reset_index()
                
                fig = px.bar(
                    symbol_sentiment,
                    x='symbol',
                    y='sentiment_score',
                    title="Average Sentiment by Cryptocurrency",
                    color='sentiment_score',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    color_continuous_midpoint=0
                )
                
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                # Recent entries table
                display_social = social_df.head(10).copy()
                display_social['sentiment_score'] = display_social['sentiment_score'].apply(lambda x: f"{x:.3f}")
                display_social = display_social[['date', 'symbol', 'platform', 'sentiment_score', 'positive_count', 'negative_count']]
                display_social = display_social.rename(columns={
                    'date': 'Date',
                    'symbol': 'Symbol',
                    'platform': 'Platform',
                    'sentiment_score': 'Sentiment Score',
                    'positive_count': 'Positive',
                    'negative_count': 'Negative'
                })
                
                st.dataframe(display_social, use_container_width=True)
        else:
            st.info("📝 No social sentiment data yet. Add some sentiment analysis above!")
    
    with tab4:
        st.subheader("📰 News Sentiment Analysis")
        
        st.info("🚧 News sentiment analysis feature is under development. You can manually analyze news sentiment using the social sentiment tool in the previous tab.")
        
        # Placeholder for future news sentiment features
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔮 Coming Soon Features:")
            st.markdown("""
            - 📰 Automated news scraping
            - 🤖 AI-powered sentiment analysis
            - 📊 News impact correlation
            - 🔔 Real-time news alerts
            - 📈 Sentiment vs price correlation
            """)
        
        with col2:
            st.markdown("#### 💡 Manual News Analysis")
            st.markdown("""
            For now, you can:
            1. Read crypto news from major sources
            2. Summarize the general sentiment
            3. Add it via the Social Sentiment tab
            4. Use 'News' as the platform
            5. Include key sentiment words
            """)
            
            if st.button("📰 Go to Social Sentiment"):
                st.rerun()

if __name__ == "__main__":
    show_sentiment_dashboard()
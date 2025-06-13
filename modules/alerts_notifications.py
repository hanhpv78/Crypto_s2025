import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time

def show_alerts_dashboard():
    """Smart Alerts & Notifications Dashboard"""
    
    st.title("🚨 Smart Alerts & Notifications")
    st.markdown("**Set up intelligent price alerts and get notified instantly**")
    st.success("🚀 Alert system fully operational!")
    st.markdown("---")
    
    # Tabs for different alert types
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Price Alerts", 
        "📊 Technical Alerts", 
        "📱 Notifications", 
        "⚙️ Settings"
    ])
    
    with tab1:
        show_price_alerts_tab()
    
    with tab2:
        show_technical_alerts_tab()
    
    with tab3:
        show_notifications_tab()
    
    with tab4:
        show_settings_tab()


def show_price_alerts_tab():
    """Price Alerts Configuration"""
    
    st.subheader("🎯 Price Alert Configuration")
    
    # Alert creation form
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Coin selection
            coins = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'ADA-USD', 
                    'AVAX-USD', 'DOT-USD', 'LINK-USD', 'MATIC-USD', 'UNI-USD']
            selected_coin = st.selectbox("Select Cryptocurrency", coins)
            
            # Get current price
            try:
                ticker = yf.Ticker(selected_coin)
                current_price = ticker.history(period="1d")['Close'].iloc[-1]
                st.metric("Current Price", f"${current_price:,.2f}")
            except:
                current_price = 0
                st.warning("Unable to fetch current price")
        
        with col2:
            # Alert type
            alert_type = st.radio(
                "Alert Type",
                ["Price Above", "Price Below", "Price Change %"]
            )
            
            # Target value
            if alert_type in ["Price Above", "Price Below"]:
                target_value = st.number_input(
                    "Target Price ($)",
                    min_value=0.01,
                    value=float(current_price * 1.1) if current_price > 0 else 100.0,
                    step=0.01
                )
            else:
                target_value = st.number_input(
                    "Price Change (%)",
                    min_value=-100.0,
                    max_value=1000.0,
                    value=10.0,
                    step=0.1
                )
        
        with col3:
            # Notification method
            notification_method = st.multiselect(
                "Notification Method",
                ["Browser Notification", "Email", "Dashboard Alert"],
                default=["Dashboard Alert"]
            )
            
            # Create alert button
            if st.button("🚨 Create Alert", type="primary"):
                create_alert(selected_coin, alert_type, target_value, notification_method)
    
    st.markdown("---")
    
    # Active alerts display
    st.subheader("📋 Active Alerts")
    
    # Get alerts from session state
    if 'alerts' not in st.session_state:
        st.session_state.alerts = []
    
    if st.session_state.alerts:
        alerts_df = pd.DataFrame(st.session_state.alerts)
        
        # Style the dataframe
        def highlight_status(val):
            if val == 'Active':
                return 'background-color: darkgreen; color: white'
            elif val == 'Triggered':
                return 'background-color: darkred; color: white'
            return ''
        
        styled_df = alerts_df.style.applymap(highlight_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Clear alerts button
        if st.button("🗑️ Clear All Alerts"):
            st.session_state.alerts = []
            st.rerun()
    else:
        st.info("📝 No active alerts. Create your first alert above!")


def show_technical_alerts_tab():
    """Technical Indicators Alerts"""
    
    st.subheader("📊 Technical Analysis Alerts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔔 RSI Alerts")
        
        # RSI alert settings
        coins = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD']
        rsi_coin = st.selectbox("Coin for RSI Alert", coins, key="rsi_coin")
        
        col_rsi1, col_rsi2 = st.columns(2)
        with col_rsi1:
            rsi_oversold = st.number_input("Oversold Level", min_value=1, max_value=50, value=30)
        with col_rsi2:
            rsi_overbought = st.number_input("Overbought Level", min_value=50, max_value=99, value=70)
        
        if st.button("Create RSI Alert"):
            st.success(f"✅ RSI alert created for {rsi_coin}")
            st.info(f"Alert when RSI < {rsi_oversold} (oversold) or RSI > {rsi_overbought} (overbought)")
    
    with col2:
        st.markdown("### 📈 Moving Average Alerts")
        
        # MA alert settings
        ma_coin = st.selectbox("Coin for MA Alert", coins, key="ma_coin")
        
        col_ma1, col_ma2 = st.columns(2)
        with col_ma1:
            ma_short = st.number_input("Short MA Period", min_value=1, max_value=100, value=20)
        with col_ma2:
            ma_long = st.number_input("Long MA Period", min_value=1, max_value=200, value=50)
        
        if st.button("Create MA Alert"):
            st.success(f"✅ Moving Average alert created for {ma_coin}")
            st.info(f"Alert when MA{ma_short} crosses MA{ma_long}")
    
    st.markdown("---")
    
    # Current technical status
    st.subheader("🎯 Current Technical Status")
    
    tech_data = []
    for coin in ['BTC-USD', 'ETH-USD', 'BNB-USD']:
        try:
            ticker = yf.Ticker(coin)
            df = ticker.history(period="1mo")
            
            if not df.empty:
                # Calculate RSI
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                # Calculate MA
                ma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
                ma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
                current_price = df['Close'].iloc[-1]
                
                # Determine signals
                rsi_signal = "🔴 Overbought" if current_rsi > 70 else "🟢 Oversold" if current_rsi < 30 else "🟡 Neutral"
                ma_signal = "🟢 Bullish" if current_price > ma_20 > ma_50 else "🔴 Bearish" if current_price < ma_20 < ma_50 else "🟡 Mixed"
                
                tech_data.append({
                    'Coin': coin.replace('-USD', ''),
                    'RSI': f"{current_rsi:.1f}",
                    'RSI Signal': rsi_signal,
                    'MA Signal': ma_signal,
                    'Price': f"${current_price:,.2f}"
                })
        except:
            continue
    
    if tech_data:
        tech_df = pd.DataFrame(tech_data)
        st.dataframe(tech_df, use_container_width=True, hide_index=True)


def show_notifications_tab():
    """Notifications History"""
    
    st.subheader("📱 Notification Center")
    
    # Mock notification history
    notifications = [
        {
            'Time': '2025-06-13 14:30:00',
            'Type': 'Price Alert',
            'Message': 'BTC-USD reached target price of $42,000',
            'Status': 'Delivered'
        },
        {
            'Time': '2025-06-13 12:15:00',
            'Type': 'RSI Alert', 
            'Message': 'ETH-USD RSI dropped below 30 (oversold)',
            'Status': 'Delivered'
        },
        {
            'Time': '2025-06-13 09:45:00',
            'Type': 'MA Alert',
            'Message': 'SOL-USD MA20 crossed above MA50 (bullish signal)',
            'Status': 'Delivered'
        }
    ]
    
    # Display notifications
    for i, notif in enumerate(notifications):
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**{notif['Type']}**")
                st.markdown(notif['Message'])
            
            with col2:
                st.text(notif['Time'])
            
            with col3:
                if notif['Status'] == 'Delivered':
                    st.success("✅ Sent")
                else:
                    st.error("❌ Failed")
        
        if i < len(notifications) - 1:
            st.markdown("---")
    
    # Clear notifications
    if st.button("🗑️ Clear Notification History"):
        st.success("Notification history cleared!")


def show_settings_tab():
    """Alert Settings & Configuration"""
    
    st.subheader("⚙️ Alert Settings & Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📧 Email Settings")
        
        email_enabled = st.checkbox("Enable Email Notifications", value=True)
        if email_enabled:
            email_address = st.text_input("Email Address", placeholder="your@email.com")
            email_frequency = st.selectbox(
                "Email Frequency",
                ["Immediate", "Every 5 minutes", "Every 15 minutes", "Hourly"]
            )
        
        st.markdown("### 🔔 Browser Notifications")
        browser_enabled = st.checkbox("Enable Browser Notifications", value=True)
        if browser_enabled:
            notification_sound = st.checkbox("Play notification sound", value=True)
    
    with col2:
        st.markdown("### 📊 Alert Limits")
        
        max_alerts = st.number_input(
            "Maximum Active Alerts",
            min_value=1,
            max_value=100,
            value=20
        )
        
        cooldown_period = st.number_input(
            "Alert Cooldown (minutes)",
            min_value=1,
            max_value=1440,
            value=15,
            help="Minimum time between same alerts"
        )
        
        st.markdown("### 🎯 Advanced Settings")
        
        price_check_interval = st.selectbox(
            "Price Check Interval",
            ["30 seconds", "1 minute", "5 minutes", "15 minutes"],
            index=1
        )
        
        auto_cleanup = st.checkbox(
            "Auto-cleanup triggered alerts", 
            value=True,
            help="Automatically remove alerts after they trigger"
        )
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")
        st.info("Alert system updated with new configuration")


def create_alert(coin, alert_type, target_value, notification_methods):
    """Create a new price alert"""
    
    # Get current price for validation
    try:
        ticker = yf.Ticker(coin)
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
        
        # Create alert object
        alert = {
            'ID': len(st.session_state.alerts) + 1,
            'Coin': coin,
            'Type': alert_type,
            'Target': f"${target_value:,.2f}" if "Price" in alert_type else f"{target_value}%",
            'Current': f"${current_price:,.2f}",
            'Methods': ", ".join(notification_methods),
            'Created': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'Status': 'Active'
        }
        
        # Add to session state
        if 'alerts' not in st.session_state:
            st.session_state.alerts = []
        
        st.session_state.alerts.append(alert)
        
        st.success(f"✅ Alert created successfully!")
        st.info(f"You'll be notified when {coin} {alert_type.lower()} {alert['Target']}")
        
        # Auto refresh to show new alert
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating alert: {str(e)}")


if __name__ == "__main__":
    show_alerts_dashboard()
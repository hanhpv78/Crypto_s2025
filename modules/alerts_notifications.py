import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time

# Remove heavy imports that might cause issues
# import requests (already in main app)

def show_alerts_dashboard():
    """Lightweight Alerts Dashboard"""
    st.title("🚨 Smart Alerts & Notifications")
    st.info("🚀 Alert system fully operational!")
    
    alerts_manager = AlertsManager()
    
    # Settings tab
    tab1, tab2, tab3, tab4 = st.tabs(["📧 Email Settings", "➕ Create Alerts", "📋 Active Alerts", "📜 Alert History"])
    
    with tab1:
        st.subheader("⚙️ Email Notification Settings")
        
        settings = alerts_manager.get_user_settings()
        
        with st.container():
            st.markdown("**📧 Email Configuration**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("📩 Email Address", value=settings.get('email', ''))
                smtp_username = st.text_input("👤 SMTP Username", value=settings.get('smtp_username', ''), 
                                            help="Usually the same as your email address")
                smtp_password = st.text_input("🔐 SMTP Password", type="password", value=settings.get('smtp_password', ''),
                                            help="Use App Password for Gmail (not your regular password)")
            
            with col2:
                smtp_server = st.selectbox("📡 SMTP Server", 
                                         options=['smtp.gmail.com', 'smtp.yahoo.com', 'smtp-mail.outlook.com', 'smtp.aol.com'],
                                         index=0 if settings.get('smtp_server') == 'smtp.gmail.com' else 0)
                smtp_port = st.number_input("🔌 SMTP Port", value=settings.get('smtp_port', 587), min_value=1, max_value=9999)
                notifications_enabled = st.checkbox("✉️ Enable Email Notifications", value=settings.get('notifications_enabled', True))
        
        # Gmail setup instructions
        with st.expander("📋 Gmail Setup Instructions"):
            st.markdown("""
            **For Gmail users:**
            1. Enable 2-Factor Authentication on your Google account
            2. Go to Google Account settings > Security > App passwords
            3. Generate an App Password for "Mail"
            4. Use this App Password (not your regular password) in the SMTP Password field
            
            **Settings for Gmail:**
            - SMTP Server: smtp.gmail.com
            - SMTP Port: 587
            - Username: your full email address
            - Password: the App Password you generated
            """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Email Settings", type="primary"):
                new_settings = {
                    'email': email,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'smtp_username': smtp_username or email,  # Use email as username if not specified
                    'smtp_password': smtp_password,
                    'notifications_enabled': notifications_enabled
                }
                
                if alerts_manager.save_user_settings(new_settings):
                    st.success("✅ Email settings saved successfully!")
        
        with col2:
            if st.button("🧪 Test Email Settings"):
                if email and smtp_password:
                    test_config = {
                        'email': email,
                        'smtp_server': smtp_server,
                        'smtp_port': smtp_port,
                        'smtp_username': smtp_username or email,
                        'smtp_password': smtp_password
                    }
                    
                    with st.spinner("Sending test email..."):
                        if alerts_manager.test_email_settings(test_config):
                            st.success("✅ Test email sent successfully! Check your inbox.")
                        else:
                            st.error("❌ Failed to send test email. Check your settings.")
                else:
                    st.warning("⚠️ Please fill in email and password fields first.")
    
    with tab2:
        st.subheader("➕ Create New Alert")
        
        alert_type = st.selectbox("Alert Type", [
            "Price Alert", 
            "RSI Alert", 
            "Volume Alert", 
            "24h Change Alert",
            "7d Change Alert",
            "30d Change Alert"
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.selectbox(
                "Cryptocurrency", 
                ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI', 'LTC', 'ICP', 'ETC', 'XLM', 'VET']
            )
        
        if alert_type == "Price Alert":
            with col2:
                condition = st.selectbox("Condition", ["ABOVE", "BELOW"])
            
            threshold = st.number_input("Price Threshold ($)", min_value=0.0001, value=1.0, step=0.1, format="%.4f")
            message = st.text_input("Custom Message (optional)")
            
            if st.button("🚨 Create Price Alert"):
                alerts_manager.create_price_alert(symbol, condition, threshold, message)
        
        elif alert_type == "RSI Alert":
            with col2:
                condition = st.selectbox("Condition", ["ABOVE", "BELOW"])
            
            threshold = st.slider("RSI Threshold", min_value=0, max_value=100, 
                                value=70 if condition == "ABOVE" else 30)
            
            st.info(f"💡 RSI > 70 = Overbought, RSI < 30 = Oversold")
            
            if st.button("🚨 Create RSI Alert"):
                alerts_manager.create_rsi_alert(symbol, condition, threshold)
        
        elif alert_type == "Volume Alert":
            threshold = st.slider("Volume Spike Threshold (%)", min_value=50, max_value=500, value=200)
            st.info(f"💡 Alert when volume is {threshold}% above average")
            
            if st.button("🚨 Create Volume Alert"):
                alerts_manager.create_volume_alert(symbol, threshold)
        
        elif alert_type.endswith("Change Alert"):
            timeframe = alert_type.split()[0].lower()  # Extract 24h, 7d, 30d
            
            with col2:
                direction = st.selectbox("Direction", ["ABOVE", "BELOW"])
            
            threshold = st.slider(f"{timeframe.upper()} Change Threshold (%)", 
                                min_value=5, max_value=100, value=20)
            
            st.info(f"💡 Alert when {timeframe} change is {'>' if direction == 'ABOVE' else '<'} {threshold}%")
            
            if st.button(f"🚨 Create {timeframe.upper()} Change Alert"):
                alerts_manager.create_percentage_change_alert(symbol, timeframe, threshold, direction)
    
    with tab3:
        st.subheader("📋 Active Alerts")
        
        alerts_df = alerts_manager.get_active_alerts()
        
        if not alerts_df.empty:
            # Summary
            st.metric("Total Active Alerts", len(alerts_df))
            
            # Display alerts in cards
            for idx, alert in alerts_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        # Alert icon based on type
                        icon = "💰" if alert['alert_type'] == 'PRICE' else "📊" if alert['alert_type'] == 'RSI' else "📈"
                        st.markdown(f"**{icon} {alert['symbol']} - {alert['alert_type']}**")
                        st.write(f"📋 {alert['message']}")
                    
                    with col2:
                        st.write("**Condition:**")
                        st.write(f"{alert['condition_type']} {alert['threshold_value']}")
                    
                    with col3:
                        st.write("**Created:**")
                        st.write(f"{alert['created_at'][:16]}")
                        st.write("🟢 **Status:** Active")
                    
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_{alert['id']}"):
                            if alerts_manager.delete_alert(alert['id']):
                                st.success("Alert deleted!")
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("📝 No active alerts. Create some alerts to monitor your cryptocurrencies!")
    
    with tab4:
        st.subheader("📜 Alert History")
        
        triggered_df = alerts_manager.get_triggered_alerts()
        
        if not triggered_df.empty:
            st.metric("Total Triggered Alerts", len(triggered_df))
            
            # Display triggered alerts
            for idx, alert in triggered_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        status_icon = "✅" if alert['email_sent'] else "⏳"
                        st.markdown(f"**{status_icon} {alert['symbol']} - {alert['alert_type']}**")
                        st.write(f"📋 {alert['message']}")
                    
                    with col2:
                        st.write("**Triggered Value:**")
                        st.write(f"{alert['current_value']}")
                        st.write(f"(Threshold: {alert['threshold_value']})")
                    
                    with col3:
                        st.write("**Triggered:**")
                        st.write(f"{alert['triggered_at'][:16] if alert['triggered_at'] else 'N/A'}")
                        email_status = "📧 Sent" if alert['email_sent'] else "📧 Pending"
                        st.write(f"{email_status}")
                    
                    with col4:
                        if st.button("🔄 Reactivate", key=f"reactivate_{alert['id']}"):
                            if alerts_manager.reactivate_alert(alert['id']):
                                st.success("Alert reactivated!")
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("📝 No triggered alerts yet.")

if __name__ == "__main__":
    show_alerts_dashboard()
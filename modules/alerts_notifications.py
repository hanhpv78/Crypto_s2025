import smtplib
import streamlit as st
import pandas as pd
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Optional
import threading
import time

class AlertsManager:
    def __init__(self):
        self.db_path = "alerts.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                threshold_value REAL,
                current_value REAL,
                message TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triggered_at TIMESTAMP,
                email_sent BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                smtp_server TEXT,
                smtp_port INTEGER,
                smtp_username TEXT,
                smtp_password TEXT,
                notifications_enabled BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_price_alert(self, symbol: str, condition: str, threshold: float, message: str = None) -> bool:
        """Create price alert (above/below threshold)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            alert_message = message or f"{symbol} price alert: {condition} ${threshold:,.2f}"
            
            cursor.execute('''
                INSERT INTO alerts (symbol, alert_type, condition_type, threshold_value, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, 'PRICE', condition, threshold, alert_message))
            
            conn.commit()
            conn.close()
            
            st.success(f"✅ Alert created: {symbol} {condition} ${threshold:,.2f}")
            return True
            
        except Exception as e:
            st.error(f"❌ Error creating alert: {str(e)}")
            return False
    
    def create_rsi_alert(self, symbol: str, condition: str, threshold: float) -> bool:
        """Create RSI alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            message = f"{symbol} RSI alert: {condition} {threshold}"
            
            cursor.execute('''
                INSERT INTO alerts (symbol, alert_type, condition_type, threshold_value, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, 'RSI', condition, threshold, message))
            
            conn.commit()
            conn.close()
            
            st.success(f"✅ RSI Alert created: {symbol} {condition} {threshold}")
            return True
            
        except Exception as e:
            st.error(f"❌ Error creating RSI alert: {str(e)}")
            return False
    
    def create_volume_alert(self, symbol: str, threshold_percentage: float) -> bool:
        """Create volume spike alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            message = f"{symbol} volume spike: >{threshold_percentage}% above average"
            
            cursor.execute('''
                INSERT INTO alerts (symbol, alert_type, condition_type, threshold_value, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, 'VOLUME', 'SPIKE', threshold_percentage, message))
            
            conn.commit()
            conn.close()
            
            st.success(f"✅ Volume Alert created: {symbol} volume spike >{threshold_percentage}%")
            return True
            
        except Exception as e:
            st.error(f"❌ Error creating volume alert: {str(e)}")
            return False
    
    def create_percentage_change_alert(self, symbol: str, timeframe: str, threshold_percentage: float, direction: str) -> bool:
        """Create percentage change alert (24h, 7d, 30d)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            message = f"{symbol} {timeframe} change: {direction} {threshold_percentage}%"
            
            cursor.execute('''
                INSERT INTO alerts (symbol, alert_type, condition_type, threshold_value, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, f'CHANGE_{timeframe}', direction, threshold_percentage, message))
            
            conn.commit()
            conn.close()
            
            st.success(f"✅ {timeframe} Change Alert created: {symbol} {direction} {threshold_percentage}%")
            return True
            
        except Exception as e:
            st.error(f"❌ Error creating change alert: {str(e)}")
            return False
    
    def get_active_alerts(self) -> pd.DataFrame:
        """Get all active alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM alerts 
                WHERE is_active = 1 
                ORDER BY created_at DESC
            ''', conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"❌ Error getting alerts: {str(e)}")
            return pd.DataFrame()
    
    def get_triggered_alerts(self) -> pd.DataFrame:
        """Get all triggered alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM alerts 
                WHERE triggered_at IS NOT NULL 
                ORDER BY triggered_at DESC
                LIMIT 50
            ''', conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"❌ Error getting triggered alerts: {str(e)}")
            return pd.DataFrame()
    
    def check_alerts(self, current_data: Dict) -> List[Dict]:
        """Check if any alerts should be triggered"""
        triggered_alerts = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get active alerts
            cursor.execute('SELECT * FROM alerts WHERE is_active = 1')
            alerts = cursor.fetchall()
            
            for alert in alerts:
                alert_id, symbol, alert_type, condition_type, threshold_value, _, message, _, created_at, triggered_at, email_sent = alert
                
                if symbol not in current_data:
                    continue
                
                coin_data = current_data[symbol]
                should_trigger = False
                current_value = None
                
                # Check price alerts
                if alert_type == 'PRICE':
                    current_value = coin_data.get('price', 0)
                    if condition_type == 'ABOVE' and current_value > threshold_value:
                        should_trigger = True
                    elif condition_type == 'BELOW' and current_value < threshold_value:
                        should_trigger = True
                
                # Check RSI alerts
                elif alert_type == 'RSI':
                    rsi_value = coin_data.get('rsi', 50)  # Default neutral RSI
                    current_value = rsi_value
                    if condition_type == 'ABOVE' and rsi_value > threshold_value:
                        should_trigger = True
                    elif condition_type == 'BELOW' and rsi_value < threshold_value:
                        should_trigger = True
                
                # Check volume alerts
                elif alert_type == 'VOLUME':
                    volume_change = coin_data.get('volume_change_24h', 0)
                    current_value = volume_change
                    if condition_type == 'SPIKE' and volume_change > threshold_value:
                        should_trigger = True
                
                # Check percentage change alerts
                elif alert_type.startswith('CHANGE_'):
                    timeframe = alert_type.split('_')[1]
                    change_key = f'change_{timeframe}'
                    change_value = coin_data.get(change_key, 0)
                    current_value = change_value
                    
                    if condition_type == 'ABOVE' and change_value > threshold_value:
                        should_trigger = True
                    elif condition_type == 'BELOW' and change_value < -threshold_value:
                        should_trigger = True
                
                if should_trigger:
                    # Update alert as triggered
                    cursor.execute('''
                        UPDATE alerts 
                        SET triggered_at = ?, current_value = ?, is_active = 0
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), current_value, alert_id))
                    
                    triggered_alerts.append({
                        'id': alert_id,
                        'symbol': symbol,
                        'alert_type': alert_type,
                        'condition_type': condition_type,
                        'threshold_value': threshold_value,
                        'current_value': current_value,
                        'message': message
                    })
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error checking alerts: {str(e)}")
        
        return triggered_alerts
    
    def send_email_alert(self, alert: Dict, email_config: Dict) -> bool:
        """Send email notification"""
        try:
            if not email_config.get('email') or not email_config.get('smtp_password'):
                return False
            
            msg = MimeMultipart()
            msg['From'] = email_config['smtp_username']
            msg['To'] = email_config['email']
            msg['Subject'] = f"🚨 Crypto Alert: {alert['symbol']} - {alert['alert_type']}"
            
            # Create HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #FF6B6B;">🚨 Crypto Alert Triggered!</h2>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>Alert Details:</h3>
                        <p><strong>Symbol:</strong> {alert['symbol']}</p>
                        <p><strong>Type:</strong> {alert['alert_type']}</p>
                        <p><strong>Condition:</strong> {alert['condition_type']}</p>
                        <p><strong>Threshold:</strong> {alert['threshold_value']}</p>
                        <p><strong>Current Value:</strong> {alert['current_value']}</p>
                    </div>
                    
                    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Message:</strong> {alert['message']}</p>
                    </div>
                    
                    <p><small>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                    
                    <hr>
                    <p><em>Best regards,<br>Tier 1 Crypto Dashboard</em></p>
                </body>
            </html>
            """
            
            msg.attach(MimeText(html_body, 'html'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['smtp_username'], email_config['smtp_password'])
            text = msg.as_string()
            server.sendmail(email_config['smtp_username'], email_config['email'], text)
            server.quit()
            
            # Mark email as sent
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE alerts SET email_sent = 1 WHERE id = ?', (alert['id'],))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error sending email: {str(e)}")
            return False
    
    def test_email_settings(self, email_config: Dict) -> bool:
        """Test email configuration"""
        try:
            msg = MimeMultipart()
            msg['From'] = email_config['smtp_username']
            msg['To'] = email_config['email']
            msg['Subject'] = "🧪 Crypto Dashboard - Email Test"
            
            body = """
            <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #4CAF50;">✅ Email Test Successful!</h2>
                    <p>Your email notification settings are working correctly.</p>
                    <p>You will now receive alerts when your cryptocurrency conditions are met.</p>
                    <hr>
                    <p><em>Tier 1 Crypto Dashboard</em></p>
                </body>
            </html>
            """
            
            msg.attach(MimeText(body, 'html'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['smtp_username'], email_config['smtp_password'])
            text = msg.as_string()
            server.sendmail(email_config['smtp_username'], email_config['email'], text)
            server.quit()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Email test failed: {str(e)}")
            return False
    
    def save_user_settings(self, settings: Dict) -> bool:
        """Save user notification settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete existing settings
            cursor.execute('DELETE FROM user_settings')
            
            # Insert new settings
            cursor.execute('''
                INSERT INTO user_settings 
                (email, smtp_server, smtp_port, smtp_username, smtp_password, notifications_enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                settings.get('email', ''),
                settings.get('smtp_server', 'smtp.gmail.com'),
                settings.get('smtp_port', 587),
                settings.get('smtp_username', ''),
                settings.get('smtp_password', ''),
                settings.get('notifications_enabled', True)
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error saving settings: {str(e)}")
            return False
    
    def get_user_settings(self) -> Dict:
        """Get user notification settings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM user_settings LIMIT 1')
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return {
                    'email': result[1] or '',
                    'smtp_server': result[2] or 'smtp.gmail.com',
                    'smtp_port': result[3] or 587,
                    'smtp_username': result[4] or '',
                    'smtp_password': result[5] or '',
                    'notifications_enabled': bool(result[6])
                }
            else:
                return {}
                
        except Exception as e:
            st.error(f"❌ Error getting settings: {str(e)}")
            return {}
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error deleting alert: {str(e)}")
            return False
    
    def reactivate_alert(self, alert_id: int) -> bool:
        """Reactivate a triggered alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET is_active = 1, triggered_at = NULL, email_sent = 0 
                WHERE id = ?
            ''', (alert_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error reactivating alert: {str(e)}")
            return False

# Streamlit interface for Alerts
def show_alerts_dashboard():
    st.header("🚨 Alerts & Email Notifications")
    
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
import streamlit as st
import os
from datetime import datetime

# Thử import SendGrid, nếu không có thì dùng mock
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("⚠️ SendGrid not available, using mock notifications")

def get_sendgrid_api_key():
    """Lấy SendGrid API key từ Streamlit secrets hoặc environment"""
    try:
        # Thử lấy từ Streamlit secrets trước
        if hasattr(st, 'secrets') and 'SENDGRID_API_KEY' in st.secrets:
            return st.secrets["SENDGRID_API_KEY"]
        else:
            # Fallback to environment variable
            return os.getenv("SENDGRID_API_KEY")
    except:
        return None

def get_from_email():
    """Lấy from email từ secrets hoặc default"""
    try:
        if hasattr(st, 'secrets') and 'FROM_EMAIL' in st.secrets:
            return st.secrets["FROM_EMAIL"]
        else:
            return os.getenv("FROM_EMAIL", "hanhpv.vt@gmail.com")
    except:
        return "hanhpv.vt@gmail.com"

def send_email(to_email, subject, content):
    """Gửi email với fallback to mock"""
    if not SENDGRID_AVAILABLE:
        print(f"📧 [MOCK EMAIL] To: {to_email}")
        print(f"📧 [MOCK EMAIL] Subject: {subject}")
        print(f"📧 [MOCK EMAIL] Sent at: {datetime.now()}")
        return True
    
    api_key = get_sendgrid_api_key()
    if not api_key:
        print("⚠️ SendGrid API key not configured, using mock email")
        print(f"📧 [MOCK EMAIL] To: {to_email}")
        print(f"📧 [MOCK EMAIL] Subject: {subject}")
        return True
    
    message = Mail(
        from_email=get_from_email(),
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"✅ Email sent: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

def create_email_template(coin_name, current_price, target_price, alert_type, gain_loss=None):
    """Tạo email template đẹp hơn"""
    
    color = "#4CAF50" if alert_type == "buy" else "#f44336"
    icon = "📈" if alert_type == "buy" else "📉"
    action = "BUY" if alert_type == "buy" else "SELL"
    
    template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, {color}, #2196F3); color: white; padding: 30px; text-align: center; }}
            .content {{ padding: 30px; }}
            .price-box {{ background-color: #f9f9f9; border-left: 4px solid {color}; padding: 20px; margin: 20px 0; }}
            .btn {{ display: inline-block; background-color: {color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            .footer {{ background-color: #f1f1f1; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{icon} {action} ALERT</h1>
                <h2>{coin_name}</h2>
            </div>
            <div class="content">
                <div class="price-box">
                    <h3>Current Price: ${current_price:.6f}</h3>
                    <p>Target Price: ${target_price:.6f}</p>
                    {f'<p>Potential Gain/Loss: {gain_loss}</p>' if gain_loss else ''}
                </div>
                <p>Your {coin_name} has {'dropped below' if alert_type == 'buy' else 'risen above'} your target price!</p>
                <p><strong>Recommendation:</strong> Consider {'buying' if alert_type == 'buy' else 'selling'} now.</p>
            </div>
            <div class="footer">
                <p>Crypto Portfolio Alert System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return template

def check_price_and_notify(setting, current_price):
    """Check notification với fallback cho cloud"""
    try:
        coin_id = setting["Coin ID"]
        coin_name = setting["Coin Name"]
        
        # Xử lý prices
        try:
            desired_buy_price = float(setting.get("Desired Buy Price", 0) or 0)
            desired_sell_price = float(setting.get("Desired Sell Price", 0) or 0)
            current_price = float(current_price)
        except (ValueError, TypeError) as e:
            print(f"⚠️ Invalid price data for {coin_id}: {e}")
            return
        
        email = setting.get("Email", "")
        if not email:
            print(f"⚠️ No email configured for {coin_id}")
            return
        
        # Check buy condition
        if desired_buy_price > 0 and current_price <= desired_buy_price:
            content = create_email_template(coin_name, current_price, desired_buy_price, "buy")
            send_email(email, f"🚨 {coin_name} - BUY OPPORTUNITY", content)
            print(f"✅ Sent BUY alert for {coin_name}")
        
        # Check sell condition
        if desired_sell_price > 0 and current_price >= desired_sell_price:
            content = create_email_template(coin_name, current_price, desired_sell_price, "sell")
            send_email(email, f"🚨 {coin_name} - SELL OPPORTUNITY", content)
            print(f"✅ Sent SELL alert for {coin_name}")
            
    except Exception as e:
        print(f"⚠️ Notification error: {e}")

# Compatibility functions cho data_access.py
def send_notification(email, subject, message):
    return send_email(email, subject, message)

def check_price_alerts(portfolio, notification_settings):
    alerts = []
    for setting in notification_settings:
        coin_id = setting.get("Coin ID", "")
        for coin in portfolio:
            if coin.get("Coin ID", "") == coin_id:
                check_price_and_notify(setting, coin.get("Current Price", 0))
                break
    return alerts
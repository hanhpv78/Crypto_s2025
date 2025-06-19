"""
Step 2 modules for Crypto Investment Platform
"""

__version__ = "2.0.0"
__author__ = "anhpd"

# Module status
MODULES = {
    'technical_indicators': 'Technical Analysis & Indicators',
    'alerts_notifications': 'Smart Alerts & Email Notifications', 
    'portfolio_tracker': 'Portfolio Management & P&L Tracking',
    'backtest_strategy': 'Strategy Backtesting Engine',
    'sentiment_analysis': 'Market Sentiment Analysis'
}

def get_available_modules():
    """Get list of available modules"""
    available = []
    
    for module_name in MODULES.keys():
        try:
            __import__(f'modules.{module_name}')
            available.append(module_name)
        except ImportError:
            pass
    
    return available

def get_module_status():
    """Get status of all modules"""
    status = {}
    
    for module_name, description in MODULES.items():
        try:
            __import__(f'modules.{module_name}')
            status[module_name] = {
                'available': True,
                'description': description
            }
        except ImportError:
            status[module_name] = {
                'available': False,
                'description': description
            }
    
    return status
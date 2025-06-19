import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional, Tuple
import json

class PortfolioTracker:
    def __init__(self):
        self.db_path = "portfolio.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for portfolio tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio holdings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_buy_price REAL NOT NULL,
                total_invested REAL NOT NULL,
                first_purchase_date TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL, -- BUY, SELL
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_amount REAL NOT NULL,
                fees REAL DEFAULT 0,
                exchange TEXT,
                notes TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio snapshots for historical tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_value REAL NOT NULL,
                total_invested REAL NOT NULL,
                total_pnl REAL NOT NULL,
                total_pnl_percentage REAL NOT NULL,
                snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                holdings_data TEXT -- JSON string of holdings
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_transaction(self, symbol: str, transaction_type: str, quantity: float, 
                       price: float, fees: float = 0, exchange: str = "", 
                       notes: str = "", transaction_date: datetime = None) -> bool:
        """Add a new transaction and update holdings"""
        try:
            if transaction_date is None:
                transaction_date = datetime.now()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate total amount
            total_amount = quantity * price + fees
            
            # Add transaction record
            cursor.execute('''
                INSERT INTO transactions 
                (symbol, transaction_type, quantity, price, total_amount, fees, exchange, notes, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, transaction_type, quantity, price, total_amount, fees, exchange, notes, transaction_date))
            
            # Update holdings
            self._update_holdings(cursor, symbol, transaction_type, quantity, price, fees)
            
            conn.commit()
            conn.close()
            
            st.success(f"✅ {transaction_type} transaction added: {quantity} {symbol} at ${price}")
            return True
            
        except Exception as e:
            st.error(f"❌ Error adding transaction: {str(e)}")
            return False
    
    def _update_holdings(self, cursor, symbol: str, transaction_type: str, 
                        quantity: float, price: float, fees: float):
        """Update holdings table based on transaction"""
        
        # Get current holding
        cursor.execute('SELECT * FROM holdings WHERE symbol = ?', (symbol,))
        existing = cursor.fetchone()
        
        if transaction_type == 'BUY':
            if existing:
                # Update existing holding
                current_qty = existing[2]
                current_avg_price = existing[3]
                current_invested = existing[4]
                
                new_qty = current_qty + quantity
                new_invested = current_invested + (quantity * price) + fees
                new_avg_price = new_invested / new_qty
                
                cursor.execute('''
                    UPDATE holdings 
                    SET quantity = ?, avg_buy_price = ?, total_invested = ?, last_updated = ?
                    WHERE symbol = ?
                ''', (new_qty, new_avg_price, new_invested, datetime.now(), symbol))
                
            else:
                # Create new holding
                total_invested = (quantity * price) + fees
                cursor.execute('''
                    INSERT INTO holdings 
                    (symbol, quantity, avg_buy_price, total_invested, first_purchase_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (symbol, quantity, price, total_invested, datetime.now()))
        
        elif transaction_type == 'SELL':
            if existing:
                current_qty = existing[2]
                current_invested = existing[4]
                
                if quantity >= current_qty:
                    # Sell all - remove holding
                    cursor.execute('DELETE FROM holdings WHERE symbol = ?', (symbol,))
                else:
                    # Partial sell
                    new_qty = current_qty - quantity
                    # Proportionally reduce total invested
                    new_invested = current_invested * (new_qty / current_qty)
                    
                    cursor.execute('''
                        UPDATE holdings 
                        SET quantity = ?, total_invested = ?, last_updated = ?
                        WHERE symbol = ?
                    ''', (new_qty, new_invested, datetime.now(), symbol))
    
    def get_current_holdings(self) -> pd.DataFrame:
        """Get current portfolio holdings with live prices"""
        try:
            conn = sqlite3.connect(self.db_path)
            holdings_df = pd.read_sql_query('SELECT * FROM holdings', conn)
            conn.close()
            
            if holdings_df.empty:
                return pd.DataFrame()
            
            # Get current prices
            portfolio_data = []
            total_value = 0
            total_invested = 0
            
            for _, holding in holdings_df.iterrows():
                symbol = holding['symbol']
                quantity = holding['quantity']
                avg_buy_price = holding['avg_buy_price']
                invested = holding['total_invested']
                
                # Get current price
                current_price = self._get_current_price(symbol)
                
                if current_price:
                    current_value = quantity * current_price
                    pnl = current_value - invested
                    pnl_percentage = (pnl / invested) * 100 if invested > 0 else 0
                    
                    portfolio_data.append({
                        'Symbol': symbol,
                        'Quantity': quantity,
                        'Avg Buy Price': avg_buy_price,
                        'Current Price': current_price,
                        'Invested': invested,
                        'Current Value': current_value,
                        'PnL': pnl,
                        'PnL %': pnl_percentage,
                        'Weight %': 0  # Will calculate after getting all values
                    })
                    
                    total_value += current_value
                    total_invested += invested
            
            if portfolio_data:
                # Calculate weights
                for item in portfolio_data:
                    item['Weight %'] = (item['Current Value'] / total_value) * 100
                
                return pd.DataFrame(portfolio_data)
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"❌ Error getting holdings: {str(e)}")
            return pd.DataFrame()
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for a cryptocurrency"""
        try:
            ticker = f"{symbol}-USD"
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")
            
            if not data.empty:
                return float(data['Close'].iloc[-1])
            return 0
            
        except Exception as e:
            st.error(f"❌ Error getting price for {symbol}: {str(e)}")
            return 0
    
    def get_portfolio_summary(self) -> Dict:
        """Get overall portfolio summary"""
        holdings_df = self.get_current_holdings()
        
        if holdings_df.empty:
            return {
                'total_value': 0,
                'total_invested': 0,
                'total_pnl': 0,
                'total_pnl_percentage': 0,
                'num_holdings': 0
            }
        
        total_value = holdings_df['Current Value'].sum()
        total_invested = holdings_df['Invested'].sum()
        total_pnl = holdings_df['PnL'].sum()
        total_pnl_percentage = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
        
        return {
            'total_value': total_value,
            'total_invested': total_invested,
            'total_pnl': total_pnl,
            'total_pnl_percentage': total_pnl_percentage,
            'num_holdings': len(holdings_df)
        }
    
    def get_transaction_history(self, limit: int = 50) -> pd.DataFrame:
        """Get transaction history"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM transactions 
                ORDER BY transaction_date DESC 
                LIMIT ?
            ''', conn, params=(limit,))
            conn.close()
            return df
        except Exception as e:
            st.error(f"❌ Error getting transactions: {str(e)}")
            return pd.DataFrame()
    
    def create_portfolio_chart(self) -> go.Figure:
        """Create portfolio allocation pie chart"""
        holdings_df = self.get_current_holdings()
        
        if holdings_df.empty:
            return go.Figure()
        
        fig = go.Figure(data=[go.Pie(
            labels=holdings_df['Symbol'],
            values=holdings_df['Current Value'],
            hole=0.3,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title="Portfolio Allocation",
            template="plotly_dark",
            showlegend=True
        )
        
        return fig
    
    def create_pnl_chart(self) -> go.Figure:
        """Create PnL chart"""
        holdings_df = self.get_current_holdings()
        
        if holdings_df.empty:
            return go.Figure()
        
        # Separate gains and losses
        gains = holdings_df[holdings_df['PnL'] >= 0]
        losses = holdings_df[holdings_df['PnL'] < 0]
        
        fig = go.Figure()
        
        if not gains.empty:
            fig.add_trace(go.Bar(
                name='Gains',
                x=gains['Symbol'],
                y=gains['PnL'],
                marker_color='green',
                text=gains['PnL %'].round(2).astype(str) + '%',
                textposition='outside'
            ))
        
        if not losses.empty:
            fig.add_trace(go.Bar(
                name='Losses',
                x=losses['Symbol'],
                y=losses['PnL'],
                marker_color='red',
                text=losses['PnL %'].round(2).astype(str) + '%',
                textposition='outside'
            ))
        
        fig.update_layout(
            title="Profit & Loss by Asset",
            xaxis_title="Cryptocurrency",
            yaxis_title="PnL ($)",
            template="plotly_dark",
            barmode='group'
        )
        
        return fig
    
    def save_portfolio_snapshot(self):
        """Save current portfolio state for historical tracking"""
        try:
            summary = self.get_portfolio_summary()
            holdings_df = self.get_current_holdings()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert holdings to JSON
            holdings_json = holdings_df.to_json() if not holdings_df.empty else "{}"
            
            cursor.execute('''
                INSERT INTO portfolio_snapshots 
                (total_value, total_invested, total_pnl, total_pnl_percentage, holdings_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                summary['total_value'],
                summary['total_invested'], 
                summary['total_pnl'],
                summary['total_pnl_percentage'],
                holdings_json
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"❌ Error saving snapshot: {str(e)}")
    
    def get_portfolio_performance_history(self) -> pd.DataFrame:
        """Get historical portfolio performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT snapshot_date, total_value, total_invested, total_pnl, total_pnl_percentage
                FROM portfolio_snapshots 
                ORDER BY snapshot_date
            ''', conn)
            conn.close()
            
            if not df.empty:
                df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
            
            return df
        except Exception as e:
            st.error(f"❌ Error getting performance history: {str(e)}")
            return pd.DataFrame()
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction and recalculate holdings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get transaction details before deleting
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
            transaction = cursor.fetchone()
            
            if not transaction:
                return False
            
            # Delete transaction
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            
            # Recalculate holdings for this symbol
            symbol = transaction[1]
            self._recalculate_holdings_for_symbol(cursor, symbol)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error deleting transaction: {str(e)}")
            return False
    
    def _recalculate_holdings_for_symbol(self, cursor, symbol: str):
        """Recalculate holdings for a specific symbol based on all transactions"""
        # Delete current holding
        cursor.execute('DELETE FROM holdings WHERE symbol = ?', (symbol,))
        
        # Get all transactions for this symbol
        cursor.execute('''
            SELECT transaction_type, quantity, price, fees, transaction_date 
            FROM transactions 
            WHERE symbol = ? 
            ORDER BY transaction_date
        ''', (symbol,))
        
        transactions = cursor.fetchall()
        
        total_quantity = 0
        total_invested = 0
        first_purchase = None
        
        for tx_type, quantity, price, fees, tx_date in transactions:
            if tx_type == 'BUY':
                total_quantity += quantity
                total_invested += (quantity * price) + fees
                if first_purchase is None:
                    first_purchase = tx_date
            elif tx_type == 'SELL':
                if total_quantity > 0:
                    # Proportionally reduce invested amount
                    sold_ratio = min(quantity / total_quantity, 1.0)
                    total_invested *= (1 - sold_ratio)
                    total_quantity -= quantity
                    total_quantity = max(0, total_quantity)  # Prevent negative
        
        # Insert new holding if there's still quantity
        if total_quantity > 0 and total_invested > 0:
            avg_price = total_invested / total_quantity
            cursor.execute('''
                INSERT INTO holdings 
                (symbol, quantity, avg_buy_price, total_invested, first_purchase_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, total_quantity, avg_price, total_invested, first_purchase))

# Streamlit interface for Portfolio Tracking
def show_portfolio_dashboard():
    st.header("💼 Portfolio Tracker")
    
    portfolio = PortfolioTracker()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "➕ Add Transaction", "📈 Performance", "📋 Transactions"])
    
    with tab1:
        # Portfolio Summary
        summary = portfolio.get_portfolio_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Portfolio Value", 
                f"${summary['total_value']:,.2f}",
                help="Current market value of all holdings"
            )
        
        with col2:
            st.metric(
                "Total Invested", 
                f"${summary['total_invested']:,.2f}",
                help="Total amount invested (including fees)"
            )
        
        with col3:
            pnl_color = "normal" if summary['total_pnl'] == 0 else ("inverse" if summary['total_pnl'] < 0 else "normal")
            st.metric(
                "Total P&L", 
                f"${summary['total_pnl']:,.2f}",
                f"{summary['total_pnl_percentage']:+.2f}%"
            )
        
        with col4:
            st.metric(
                "Holdings", 
                summary['num_holdings'],
                help="Number of different cryptocurrencies"
            )
        
        # Portfolio Charts
        if summary['num_holdings'] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                allocation_chart = portfolio.create_portfolio_chart()
                st.plotly_chart(allocation_chart, use_container_width=True)
            
            with col2:
                pnl_chart = portfolio.create_pnl_chart()
                st.plotly_chart(pnl_chart, use_container_width=True)
            
            # Holdings Table
            st.subheader("💎 Current Holdings")
            holdings_df = portfolio.get_current_holdings()
            
            if not holdings_df.empty:
                # Format the dataframe for display
                display_df = holdings_df.copy()
                display_df['Avg Buy Price'] = display_df['Avg Buy Price'].apply(lambda x: f"${x:,.4f}")
                display_df['Current Price'] = display_df['Current Price'].apply(lambda x: f"${x:,.4f}")
                display_df['Invested'] = display_df['Invested'].apply(lambda x: f"${x:,.2f}")
                display_df['Current Value'] = display_df['Current Value'].apply(lambda x: f"${x:,.2f}")
                display_df['PnL'] = display_df['PnL'].apply(lambda x: f"${x:,.2f}")
                display_df['PnL %'] = display_df['PnL %'].apply(lambda x: f"{x:+.2f}%")
                display_df['Weight %'] = display_df['Weight %'].apply(lambda x: f"{x:.1f}%")
                display_df['Quantity'] = display_df['Quantity'].apply(lambda x: f"{x:,.6f}")
                
                st.dataframe(display_df, use_container_width=True)
                
                # Save snapshot button
                if st.button("📸 Save Portfolio Snapshot"):
                    portfolio.save_portfolio_snapshot()
                    st.success("✅ Portfolio snapshot saved!")
        else:
            st.info("📝 No holdings yet. Add your first transaction to get started!")
    
    with tab2:
        st.subheader("➕ Add New Transaction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.selectbox(
                "Cryptocurrency",
                ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI', 'LTC', 'ICP', 'ETC', 'XLM', 'VET', 'ALGO', 'ATOM', 'XTZ']
            )
            
            transaction_type = st.selectbox("Transaction Type", ["BUY", "SELL"])
            
            quantity = st.number_input("Quantity", min_value=0.000001, value=1.0, step=0.1, format="%.6f")
        
        with col2:
            price = st.number_input("Price per unit ($)", min_value=0.0001, value=1.0, step=0.01, format="%.4f")
            
            fees = st.number_input("Fees ($)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            
            exchange = st.text_input("Exchange (optional)", placeholder="e.g., Binance, Coinbase")
        
        transaction_date = st.date_input("Transaction Date", value=datetime.now().date())
        notes = st.text_area("Notes (optional)", placeholder="Any additional notes about this transaction")
        
        # Transaction summary
        total_amount = quantity * price + fees
        st.write(f"**Total Amount:** ${total_amount:,.2f} {'(Cost)' if transaction_type == 'BUY' else '(Revenue)'}")
        
        if st.button(f"➕ Add {transaction_type} Transaction", type="primary"):
            if portfolio.add_transaction(
                symbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                fees=fees,
                exchange=exchange,
                notes=notes,
                transaction_date=datetime.combine(transaction_date, datetime.min.time())
            ):
                st.rerun()
    
    with tab3:
        st.subheader("📈 Portfolio Performance History")
        
        performance_df = portfolio.get_portfolio_performance_history()
        
        if not performance_df.empty:
            # Performance chart
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                subplot_titles=['Portfolio Value Over Time', 'P&L Percentage'],
                vertical_spacing=0.1
            )
            
            # Portfolio value
            fig.add_trace(
                go.Scatter(
                    x=performance_df['snapshot_date'],
                    y=performance_df['total_value'],
                    mode='lines+markers',
                    name='Portfolio Value',
                    line=dict(color='#00CC96', width=2)
                ), row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=performance_df['snapshot_date'],
                    y=performance_df['total_invested'],
                    mode='lines',
                    name='Total Invested',
                    line=dict(color='#FFA15A', width=2, dash='dash')
                ), row=1, col=1
            )
            
            # P&L percentage
            fig.add_trace(
                go.Scatter(
                    x=performance_df['snapshot_date'],
                    y=performance_df['total_pnl_percentage'],
                    mode='lines+markers',
                    name='P&L %',
                    line=dict(color='#FF6692', width=2),
                    fill='tonexty'
                ), row=2, col=1
            )
            
            fig.update_layout(
                height=600,
                template="plotly_dark",
                title="Portfolio Performance Timeline"
            )
            
            fig.update_yaxes(title_text="Value ($)", row=1, col=1)
            fig.update_yaxes(title_text="P&L (%)", row=2, col=1)
            fig.update_xaxes(title_text="Date", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance metrics
            if len(performance_df) > 1:
                first_value = performance_df['total_value'].iloc[0]
                last_value = performance_df['total_value'].iloc[-1]
                total_return = ((last_value - first_value) / first_value) * 100 if first_value > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Return", f"{total_return:+.2f}%")
                
                with col2:
                    best_pnl = performance_df['total_pnl_percentage'].max()
                    st.metric("Best Performance", f"{best_pnl:+.2f}%")
                
                with col3:
                    worst_pnl = performance_df['total_pnl_percentage'].min()
                    st.metric("Worst Performance", f"{worst_pnl:+.2f}%")
        else:
            st.info("📝 No performance history yet. Save some portfolio snapshots to track performance over time.")
    
    with tab4:
        st.subheader("📋 Transaction History")
        
        transactions_df = portfolio.get_transaction_history()
        
        if not transactions_df.empty:
            # Format transactions for display
            display_transactions = transactions_df.copy()
            display_transactions['total_amount'] = display_transactions['total_amount'].apply(lambda x: f"${x:,.2f}")
            display_transactions['price'] = display_transactions['price'].apply(lambda x: f"${x:,.4f}")
            display_transactions['fees'] = display_transactions['fees'].apply(lambda x: f"${x:,.2f}")
            display_transactions['quantity'] = display_transactions['quantity'].apply(lambda x: f"{x:,.6f}")
            display_transactions['transaction_date'] = pd.to_datetime(display_transactions['transaction_date']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Rename columns for display
            display_transactions = display_transactions.rename(columns={
                'symbol': 'Symbol',
                'transaction_type': 'Type',
                'quantity': 'Quantity',
                'price': 'Price',
                'total_amount': 'Total Amount',
                'fees': 'Fees',
                'exchange': 'Exchange',
                'notes': 'Notes',
                'transaction_date': 'Date'
            })
            
            # Select columns to display
            columns_to_show = ['Date', 'Symbol', 'Type', 'Quantity', 'Price', 'Total Amount', 'Fees', 'Exchange']
            st.dataframe(display_transactions[columns_to_show], use_container_width=True)
            
            # Transaction deletion (optional advanced feature)
            with st.expander("🗑️ Delete Transaction"):
                st.warning("⚠️ Deleting transactions will recalculate your holdings. Use with caution!")
                
                transaction_options = []
                for _, tx in transactions_df.iterrows():
                    tx_desc = f"{tx['transaction_date'][:16]} - {tx['transaction_type']} {tx['quantity']:.6f} {tx['symbol']} at ${tx['price']:.4f}"
                    transaction_options.append((tx['id'], tx_desc))
                
                if transaction_options:
                    selected_tx = st.selectbox(
                        "Select transaction to delete",
                        options=[opt[0] for opt in transaction_options],
                        format_func=lambda x: next(opt[1] for opt in transaction_options if opt[0] == x)
                    )
                    
                    if st.button("🗑️ Delete Selected Transaction", type="secondary"):
                        if portfolio.delete_transaction(selected_tx):
                            st.success("✅ Transaction deleted and holdings recalculated!")
                            st.rerun()
        else:
            st.info("📝 No transactions yet. Add your first transaction to get started!")

if __name__ == "__main__":
    show_portfolio_dashboard()
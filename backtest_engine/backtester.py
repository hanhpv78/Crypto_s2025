import pandas as pd

class BacktestEngine:
    def __init__(self, df, signals, initial_balance=10000):
        """
        df: DataFrame giá và chỉ báo
        signals: Series tín hiệu (1: mua, 0: không làm gì, -1: bán)
        initial_balance: số dư ban đầu
        """
        self.df = df
        self.signals = signals
        self.initial_balance = initial_balance

    def run(self):
        # Giả lập backtest đơn giản: chỉ tính lợi nhuận khi mua/bán theo tín hiệu
        balance = self.initial_balance
        position = 0  # 0: không nắm giữ, 1: đang nắm giữ
        entry_price = 0
        for i in range(len(self.df)):
            signal = self.signals.iloc[i]
            price = self.df['Close'].iloc[i]
            if signal == 1 and position == 0:
                position = 1
                entry_price = price
            elif signal == -1 and position == 1:
                balance += (price - entry_price)
                position = 0
        # Nếu còn vị thế cuối kỳ, chốt giá cuối cùng
        if position == 1:
            balance += (self.df['Close'].iloc[-1] - entry_price)
        profit = balance - self.initial_balance
        return {"profit": profit}

    def default_backtest_func(self, df_ind, params):
        sma_col = f"SMA_{params['SMA']}"
        if sma_col in df_ind.columns:
            # Đảm bảo cùng index
            close = df_ind["Close"].loc[df_ind[sma_col].index]
            signals = (df_ind[sma_col] > close).astype(int)
        else:
            signals = pd.Series(0, index=df_ind.index)
        bt = BacktestEngine(df_ind, signals)
        result = bt.run()
        return result.get(self.metric, 0)
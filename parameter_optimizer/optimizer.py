import itertools
import random
import pandas as pd
from indicators_engine.indicators_engine import IndicatorsEngine
from backtest_engine.backtester import BacktestEngine

class ParameterOptimizer:
    def __init__(self, indicators, param_ranges, data, backtest_func=None, metric="profit"):
        """
        indicators: list tên chỉ báo, ví dụ ["SMA", "RSI"]
        param_ranges: dict, ví dụ {"SMA": [10, 20, 50], "RSI": [7, 14, 21]}
        data: DataFrame giá
        backtest_func: hàm backtest nhận df_ind, trả về metric (nếu muốn custom)
        metric: tên chỉ số hiệu suất để tối ưu ("profit", "winrate", ...)
        """
        self.indicators = indicators
        self.param_ranges = param_ranges
        self.data = data
        self.backtest_func = backtest_func or self.default_backtest_func
        self.metric = metric

    def default_backtest_func(self, df_ind, params):
        import pandas as pd

        print("\n==== DEBUG default_backtest_func ====")
        print("df_ind.columns:", df_ind.columns)
        print("df_ind.shape:", df_ind.shape)
        print("params:", params)

        # Tìm cột Close và cột chỉ báo phù hợp trong MultiIndex
        close_col = None
        for col in df_ind.columns:
            if isinstance(col, tuple) and col[0] == "Close":
                close_col = col
                break
            elif col == "Close":
                close_col = col
                break
        print("close_col:", close_col)

        ind_col = None
        if "SMA" in params:
            ind_col = (f"SMA_{params['SMA']}", "")
        elif "EMA" in params:
            ind_col = (f"EMA_{params['EMA']}", "")
        # Thêm các chỉ báo khác nếu cần
        print("ind_col:", ind_col)

        # Kiểm tra sự tồn tại của các cột
        if close_col not in df_ind.columns:
            print(f"ERROR: close_col {close_col} not in df_ind.columns")
            print("df_ind.columns:", df_ind.columns)
            return 0
        if ind_col not in df_ind.columns:
            print(f"ERROR: ind_col {ind_col} not in df_ind.columns")
            print("df_ind.columns:", df_ind.columns)
            return 0

        # Lấy các dòng hợp lệ
        valid = df_ind[[ind_col, close_col]].dropna()
        print("valid.shape:", valid.shape)
        print("valid.head():\n", valid.head())

        # So sánh và tạo tín hiệu
        try:
            signals = (valid[ind_col] > valid[close_col]).astype(int)
        except Exception as e:
            print("ERROR khi so sánh signals:", e)
            print("valid[ind_col] type:", type(valid[ind_col]), "shape:", getattr(valid[ind_col], "shape", None))
            print("valid[close_col] type:", type(valid[close_col]), "shape:", getattr(valid[close_col], "shape", None))
            return 0

        signals_full = pd.Series(0, index=df_ind.index)
        signals_full.loc[signals.index] = signals

        from backtest_engine.backtester import BacktestEngine
        bt = BacktestEngine(df_ind, signals_full)
        result = bt.run()
        score = result.get(self.metric, 0)
        if isinstance(score, pd.Series):
            score = score.iloc[0]
        return score

    def grid_search(self):
        keys = list(self.param_ranges.keys())
        values = [self.param_ranges[k] for k in keys]
        best_score = None
        best_params = None

        for param_set in itertools.product(*values):
            params = dict(zip(keys, param_set))
            # Tính toán chỉ báo với tham số hiện tại
            engine = IndicatorsEngine(self.data)
            for ind in self.indicators:
                if ind == "SMA":
                    engine.sma(window=params["SMA"])
                if ind == "EMA":
                    engine.ema(window=params["EMA"])
                if ind == "MACD":
                    engine.macd(window_fast=params.get("MACD_fast", 12), window_slow=params.get("MACD_slow", 26))
                if ind == "RSI":
                    engine.rsi(window=params["RSI"])
                if ind == "Bollinger Bands":
                    engine.bollinger_bands(window=params["BB"])
                if ind == "ATR":
                    engine.atr(window=params["ATR"])
                if ind == "CCI":
                    engine.cci(window=params["CCI"])
                if ind == "Stochastic":
                    engine.stochastic(window=params["Stochastic"])
                if ind == "ADX":
                    engine.adx(window=params["ADX"])
                if ind == "Williams %R":
                    engine.williams_r(lbp=params["WilliamsR"])
            df_ind = engine.get_df()
            score = self.backtest_func(df_ind, params)
            if (best_score is None) or (score > best_score):
                best_score = score
                best_params = params
        return best_params, best_score

    def random_search(self, n_iter=50):
        keys = list(self.param_ranges.keys())
        best_score = None
        best_params = None
        for _ in range(n_iter):
            params = {k: random.choice(self.param_ranges[k]) for k in keys}
            engine = IndicatorsEngine(self.data)
            for ind in self.indicators:
                if ind == "SMA":
                    engine.sma(window=params["SMA"])
                if ind == "EMA":
                    engine.ema(window=params["EMA"])
                if ind == "MACD":
                    engine.macd(window_fast=params.get("MACD_fast", 12), window_slow=params.get("MACD_slow", 26))
                if ind == "RSI":
                    engine.rsi(window=params["RSI"])
                if ind == "Bollinger Bands":
                    engine.bollinger_bands(window=params["BB"])
                if ind == "ATR":
                    engine.atr(window=params["ATR"])
                if ind == "CCI":
                    engine.cci(window=params["CCI"])
                if ind == "Stochastic":
                    engine.stochastic(window=params["Stochastic"])
                if ind == "ADX":
                    engine.adx(window=params["ADX"])
                if ind == "Williams %R":
                    engine.williams_r(lbp=params["WilliamsR"])
            df_ind = engine.get_df()
            score = self.backtest_func(df_ind, params)
            if (best_score is None) or (score > best_score):
                best_score = score
                best_params = params
        return best_params, best_score
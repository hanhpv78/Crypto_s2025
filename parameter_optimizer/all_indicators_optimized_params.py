import yfinance as yf
import pandas as pd
from indicators_engine.indicators_engine import IndicatorsEngine
from parameter_optimizer.optimizer import ParameterOptimizer

# 1. Định nghĩa danh sách coin
coins = {
    'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'BNB': 'BNB-USD',
    'SOL': 'SOL-USD', 'ADA': 'ADA-USD', 'AVAX': 'AVAX-USD',
    'DOT': 'DOT-USD', 'LINK': 'LINK-USD', 'MATIC': 'MATIC-USD',
    'UNI': 'UNI-USD', 'LTC': 'LTC-USD'
}

symbols = list(coins.values())

# 2. Tải dữ liệu cho tất cả coin
df = yf.download(symbols, period="1y", interval="1d")

# 3. Tách và ép cột đơn cho từng coin
coin_dfs = {}
for name, symbol in coins.items():
    df_coin = df.xs(symbol, axis=1, level=1)
    df_coin.columns = [col if isinstance(col, str) else col[0] for col in df_coin.columns]
    coin_dfs[name] = df_coin

# 4. Hàm tìm cột an toàn cho mọi trường hợp
def find_col(df, col_name):
    for col in df.columns:
        if isinstance(col, tuple):
            if col[0] == col_name:
                return col
        elif isinstance(col, str):
            if col == col_name:
                return col
    return None

# 5. Hàm backtest_func cho ParameterOptimizer (dùng cho mọi indicator)
def default_backtest_func(df_ind, params, metric="profit"):
    close_col = find_col(df_ind, "Close")

    ind_col = None
    for key in ["SMA", "EMA", "RSI", "CCI", "ATR", "ADX", "WilliamsR"]:
        if key in params:
            ind_col = find_col(df_ind, f"{key}_{params[key]}")
            if ind_col is not None:
                break
    if "BB" in params and ind_col is None:
        ind_col = find_col(df_ind, f"BB_Mavg_{params['BB']}")
        if ind_col is None:
            ind_col = find_col(df_ind, f"BB_{params['BB']}")
    if "Stochastic" in params and ind_col is None:
        ind_col = find_col(df_ind, f"STOCH_K_{params['Stochastic']}")
        if ind_col is None:
            ind_col = find_col(df_ind, f"STOCH_D_{params['Stochastic']}")
    if "MACD_fast" in params and "MACD_slow" in params and ind_col is None:
        ind_col = find_col(df_ind, f"MACD_{params['MACD_fast']}_{params['MACD_slow']}")

    if ind_col not in df_ind.columns or close_col not in df_ind.columns:
        print(f"ERROR: {ind_col=} or {close_col=} not in df_ind.columns")
        print("df_ind.columns:", df_ind.columns)
        return 0

    valid = df_ind[[ind_col, close_col]].dropna()
    signals = (valid[ind_col] > valid[close_col]).astype(int)
    signals_full = pd.Series(0, index=df_ind.index)
    signals_full.loc[signals.index] = signals

    from backtest_engine.backtester import BacktestEngine
    bt = BacktestEngine(df_ind, signals_full)
    result = bt.run()
    score = result.get(metric, 0)
    if isinstance(score, pd.Series):
        score = score.iloc[0]
    return score

# 6. Tối ưu cho từng coin (ví dụ: tối ưu RSI)
results = []
for coin, df_coin in coin_dfs.items():
    print(f"\n--- Tối ưu cho {coin} ---")
    engine = IndicatorsEngine(df_coin)
    engine.rsi(window=14)  # Tính sẵn chỉ báo, có thể thêm các chỉ báo khác nếu muốn
    df_ind = engine.get_df()
    param_ranges = {"RSI": range(5, 21)}
    optimizer = ParameterOptimizer(
        indicators=["RSI"],
        param_ranges=param_ranges,
        data=df_ind,
        backtest_func=lambda df, params: default_backtest_func(df, params, metric="profit"),
        metric="profit"
    )
    best_params, best_score = optimizer.grid_search()  # hoặc optimizer.optimize() tùy bạn định nghĩa
    print(f"{coin}: Best params: {best_params}, Score: {best_score}")
    results.append({"coin": coin, "best_params": best_params, "best_score": best_score})

# 7. Lưu kết quả nếu muốn
pd.DataFrame(results).to_csv("all_indicators_optimized_params.csv", index=False)
print("Đã lưu kết quả tối ưu vào all_indicators_optimized_params.csv")
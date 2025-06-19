import yfinance as yf
from parameter_optimizer.optimizer import ParameterOptimizer
import pandas as pd

# 1. Tải dữ liệu thực tế
df = yf.download("BTC-USD", period="1y", interval="1d").dropna()

# 2. Định nghĩa các chỉ báo và dải tham số cần tối ưu
indicators_param_ranges = {
    "SMA": {"SMA": [5, 10, 20, 50, 100]},
    "EMA": {"EMA": [5, 10, 20, 50, 100]},
    "RSI": {"RSI": [7, 14, 21]},
    "MACD": {"MACD_fast": [7, 12], "MACD_slow": [21, 26]},
    "Bollinger Bands": {"BB": [10, 20, 50]},
    "ATR": {"ATR": [7, 14, 21]},
    "CCI": {"CCI": [7, 14, 21]},
    "Stochastic": {"Stochastic": [7, 14, 21]},
    "ADX": {"ADX": [7, 14, 21]},
    "Williams %R": {"WilliamsR": [7, 14, 21]}
}

results = {}

for ind, param_ranges in indicators_param_ranges.items():
    print(f"Tối ưu {ind} ...")
    optimizer = ParameterOptimizer(
        indicators=[ind],
        param_ranges=param_ranges,
        data=df
    )
    best_params_grid, best_score_grid = optimizer.grid_search()
    best_params_rand, best_score_rand = optimizer.random_search(n_iter=50)
    results[ind] = {
        "grid": {"best_params": best_params_grid, "best_score": best_score_grid},
        "random": {"best_params": best_params_rand, "best_score": best_score_rand}
    }
    print(f"  [Grid]   Best params: {best_params_grid}, Best score: {best_score_grid}")
    print(f"  [Random] Best params: {best_params_rand}, Best score: {best_score_rand}")

print("\nTổng hợp kết quả tối ưu:")
for ind, res in results.items():
    print(f"{ind}:")
    print(f"  Grid   : {res['grid']['best_params']} | Score: {res['grid']['best_score']}")
    print(f"  Random : {res['random']['best_params']} | Score: {res['random']['best_score']}")

# Sau khi đã có biến `results` như ở trên
rows = []
for ind, res in results.items():
    rows.append({
        "Indicator": ind,
        "Grid_Params": res['grid']['best_params'],
        "Grid_Score": res['grid']['best_score'],
        "Random_Params": res['random']['best_params'],
        "Random_Score": res['random']['best_score']
    })
df_result = pd.DataFrame(rows)
df_result.to_csv("optimized_indicator_params.csv", index=False)
print("Đã lưu kết quả tối ưu vào optimized_indicator_params.csv")
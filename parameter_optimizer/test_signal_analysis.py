import pandas as pd
from indicators_engine.indicators_engine import IndicatorsEngine

# Giả sử bạn đã có best_params cho SMA
best_sma_window = results["SMA"]["grid"]["best_params"]["SMA"]

# Tính SMA với tham số tối ưu
engine = IndicatorsEngine(df)
engine.sma(window=best_sma_window)
df_ind = engine.get_df()

# Sinh tín hiệu: mua khi Close > SMA, bán khi Close < SMA, hold khi bằng nhau
df_ind["Signal"] = 0
df_ind.loc[df_ind["Close"] > df_ind[f"SMA_{best_sma_window}"], "Signal"] = 1   # Mua
df_ind.loc[df_ind["Close"] < df_ind[f"SMA_{best_sma_window}"], "Signal"] = -1  # Bán

# Lọc ra các thời điểm có tín hiệu
signals_df = df_ind[df_ind["Signal"] != 0][["Close", f"SMA_{best_sma_window}", "Signal"]]
signals_df["Action"] = signals_df["Signal"].map({1: "Mua", -1: "Bán"})

print("\nCác thời điểm mua/bán theo SMA tối ưu:")
print(signals_df.tail(10))  # In 10 tín hiệu gần nhất

# Nếu muốn phân tích cho các chỉ báo khác, chỉ cần thay logic sinh tín hiệu tương ứng.
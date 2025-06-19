import pandas as pd
from parameter_optimizer.optimizer import ParameterOptimizer

# Giả lập dữ liệu giá (bạn nên thay bằng dữ liệu thực tế)
data = pd.DataFrame({
    "Open": [1,2,3,4,5,6,7,8,9,10],
    "High": [2,3,4,5,6,7,8,9,10,11],
    "Low": [0,1,2,3,4,5,6,7,8,9],
    "Close": [1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5],
    "Volume": [100,110,120,130,140,150,160,170,180,190]
})

optimizer = ParameterOptimizer(
    indicators=["SMA", "RSI"],
    param_ranges={"SMA": [2, 3, 4], "RSI": [2, 3, 4]},
    data=data
)

best_params, best_score = optimizer.grid_search()
print("Best params:", best_params)
print("Best score:", best_score)

# Hoặc test random search
best_params, best_score = optimizer.random_search(n_iter=10)
print("Best params (random):", best_params)
print("Best score (random):", best_score)
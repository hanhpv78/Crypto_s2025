from parameter_optimizer.optimizer import ParameterOptimizer

optimizer = ParameterOptimizer(
    indicators=["SMA", "RSI"],
    param_ranges={"SMA": [10, 20, 50], "RSI": [7, 14, 21]},
    data=df
)
best_params, best_score = optimizer.grid_search()
print("Best params:", best_params)
print("Best score:", best_score)

# Hoặc dùng random search:
best_params, best_score = optimizer.random_search(n_iter=100)
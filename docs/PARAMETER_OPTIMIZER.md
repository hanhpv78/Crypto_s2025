---

### **PARAMETER_OPTIMIZER.md**

```markdown
# Hướng dẫn sử dụng Parameter Optimizer

## 1. Mục đích
- Tối ưu tham số cho từng chỉ báo hoặc nhiều chỉ báo cùng lúc.
- Đầu vào: danh sách chỉ báo, dải tham số, dữ liệu giá.
- Đầu ra: bộ tham số tối ưu theo tiêu chí (accuracy, lợi nhuận backtest...).

## 2. Cách sử dụng

### Khởi tạo
```python
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
```

### Tối ưu tham số
```python
best_params = optimizer.optimize(
    method="grid_search",  # hoặc "random_search", "genetic_algorithm"
    scoring="profit"       # hoặc "accuracy", "sharpe", ...
)
```
Kết quả
Trả về bộ tham số tối ưu cho từng chỉ báo.
Có thể lưu lại để dùng cho backtest hoặc AI.
3. Thêm thuật toán tối ưu mới
Thêm hàm mới vào class ParameterOptimizer (ví dụ: genetic algorithm, bayesian...)
4. Tham số đầu vào
indicators: danh sách chỉ báo cần tối ưu
param_ranges: dải tham số cho từng chỉ báo
data: DataFrame giá
5. Kết quả trả về
Bộ tham số tối ưu, giá trị metric tối ưu.
6. Lưu ý
Có thể tích hợp với Backtest Engine để đánh giá hiệu suất.
7. Lưu ý
Có thể mở rộng thêm thuật toán tối ưu mới.
Tách biệt logic tối ưu khỏi logic backtest và AI.

###########################################################################
Dưới đây là hướng dẫn chi tiết để bạn phát triển Parameter Optimizer hỗ trợ các thuật toán:
Grid Search, Random Search, Genetic Algorithm, Bayesian Optimization
và tối ưu tham số cho các chỉ báo kỹ thuật đã có (SMA, EMA, MACD, RSI, Bollinger Bands, ATR, CCI, Stochastic, ADX, Williams %R)
kết hợp với backtesting trên dữ liệu lịch sử và thực tế.

1. Cấu trúc module gợi ý
parameter_optimizer/
├── __init__.py
├── optimizer.py
├── genetic_algorithm.py
├── bayesian_optimizer.py
└── utils.py

2. Ý tưởng tổng quát
Grid Search: Duyệt hết mọi tổ hợp tham số.
Random Search: Lấy ngẫu nhiên tổ hợp tham số trong không gian tham số.
Genetic Algorithm: Chọn lọc, lai ghép, đột biến các bộ tham số tốt nhất qua nhiều thế hệ.
Bayesian Optimization: Dùng mô hình xác suất để chọn tham số tiếp theo dựa trên kết quả trước đó (có thể dùng thư viện như scikit-optimize).
Tất cả đều cần:

Hàm sinh chỉ báo với tham số động (đã có ở Indicators Engine).
Hàm backtest trả về metric tối ưu (lợi nhuận, winrate, drawdown...).
```
6. Gợi ý cho Genetic Algorithm và Bayesian Optimization
Genetic Algorithm:
Bạn có thể dùng thư viện như DEAP hoặc tự code đơn giản (chọn, lai ghép, đột biến, chọn lọc).
Bayesian Optimization:
Có thể dùng scikit-optimize (skopt) hoặc bayesian-optimization.
7. Tích hợp dữ liệu thực và dữ liệu lịch sử
Bạn chỉ cần truyền DataFrame dữ liệu thực/tổng hợp vào data khi khởi tạo optimizer.
Có thể chạy tối ưu trên nhiều tập dữ liệu khác nhau để kiểm tra tính ổn định của tham số.


---

### **BACKTEST_ENGINE.md**

```markdown
# Hướng dẫn sử dụng Backtest Engine

## 1. Mục đích
- Đánh giá hiệu suất của bộ tham số chỉ báo trên dữ liệu lịch sử.
- Đầu vào: tín hiệu từ chỉ báo, tham số tối ưu.
- Đầu ra: các chỉ số hiệu suất (lợi nhuận, drawdown, winrate...).

## 2. Cách sử dụng

### Khởi tạo
```python
from backtest_engine.backtester import BacktestEngine

backtester = BacktestEngine(df, signals, params)
results = backtester.run(strategy="crossover", initial_balance=10000)
```
Kết quả
Trả về DataFrame kết quả giao dịch, các chỉ số hiệu suất.
Có thể trực quan hóa hoặc lưu lại.
3. Thêm chiến lược mới
Thêm hàm mới vào class BacktestEngine (ví dụ: long/short, trailing stop...)
4. Tham số đầu vào
data: DataFrame giá
signals: Series tín hiệu (1: mua, -1: bán, 0: giữ)
initial_balance: số dư ban đầu
5. Kết quả trả về
Hiệu suất: lợi nhuận, drawdown, winrate, equity curve...
6. Lưu ý
Có thể dùng cho nhiều chiến lược khác nhau.

7. Lưu ý
Có thể mở rộng cho nhiều chiến lược khác nhau.
Đảm bảo module độc lập, dễ tái sử dụng.
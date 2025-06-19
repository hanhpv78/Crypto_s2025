# Hướng dẫn sử dụng Indicators Engine

## 1. Mục đích
- Tính toán các chỉ báo kỹ thuật (SMA, EMA, MACD, RSI, Bollinger Bands, ATR, CCI, Stochastic, ADX, Williams %R, ...).
- Nhận tham số động, dễ mở rộng, dễ tích hợp vào các module khác.

## 2. Cách sử dụng

### Khởi tạo
```python
from indicators_engine.indicators_engine import IndicatorsEngine

engine = IndicatorsEngine(df)  # df là DataFrame giá (Open, High, Low, Close, Volume)
```

### Tính toán các chỉ báo kỹ thuật
```python
engine.sma(window=20)
engine.ema(window=50)
engine.macd(window_fast=12, window_slow=26)
engine.rsi(window=14)
engine.bollinger_bands(window=20)
# ... các chỉ báo khác
df_ind = engine.get_df()
```

---
3. Thêm chỉ báo mới
Thêm hàm mới vào class IndicatorsEngine.
Đảm bảo trả về Series 1 chiều, nhận tham số động.
4. Lưu ý
Dữ liệu đầu vào phải có đủ cột: Open, High, Low, Close, Volume.
Có thể tích hợp module này vào các bước tối ưu, backtest, AI.
4. Tham số đầu vào
DataFrame giá (các cột: Open, High, Low, Close, Volume)
Tham số động cho từng chỉ báo (window, fast, slow...)
5. Kết quả trả về
DataFrame với các cột chỉ báo tương ứng.
6. Ví dụ mở rộng
Có thể dùng module này cho backtest, tối ưu tham số, AI...

---

### **docs/HISTORY_LOGGER.md**

```markdown
# Hướng dẫn sử dụng History Logger

## 1. Chức năng
- Lưu lại kết quả tối ưu, backtest, khuyến nghị AI.
- Có thể dùng file, database hoặc cloud storage.

## 2. Cách sử dụng

```python
from history_logger.logger import HistoryLogger

logger = HistoryLogger(storage="file", path="history/")
logger.save_optimization(params, score)
logger.save_backtest(result)
logger.save_ai_recommendation(model, metrics)

3. Thêm backend lưu trữ mới
Thêm hàm/class cho database, cloud...
4. Tham số đầu vào
params: tham số tối ưu
result: kết quả backtest
model, metrics: mô hình AI và chỉ số đánh giá
5. Kết quả trả về
File hoặc bản ghi lưu trữ lịch sử
6. Lưu ý
Dễ dàng mở rộng cho các loại storage khác.
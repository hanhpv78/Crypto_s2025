---

### **AI_MODEL_SELECTOR.md**

```markdown
# Hướng dẫn sử dụng AI Model Selector

## 1. Mục đích
- Chọn và huấn luyện các thuật toán AI khác nhau (Random Forest, XGBoost, v.v.).
- Đầu vào: dữ liệu chỉ báo với tham số tối ưu.
- Đầu ra: mô hình dự báo tín hiệu mua/bán/nắm giữ.

## 2. Cách sử dụng

### Khởi tạo
```python
from ai_model_selector.model_selector import AIModelSelector

selector = AIModelSelector(df_features, df_labels)
```

### Huấn luyện mô hình
```python
model, metrics = selector.train(
    model_type="RandomForest",  # hoặc "XGBoost", "SVM", ...
    params={"n_estimators": 100}
)
```

### Dự đoán
```python
predictions = selector.predict(new_data)
```
````
3. Thêm thuật toán AI mới
Thêm class/model mới vào module.
4. Tham số đầu vào
models: danh sách thuật toán AI
X_train, y_train: dữ liệu huấn luyện
5. Kết quả trả về
Mô hình tốt nhất, các chỉ số đánh giá (accuracy, f1, ...)
6. Lưu ý
Có thể tích hợp với History Logger để lưu kết quả.

7. Lưu ý
Có thể mở rộng thêm thuật toán AI mới.
Hỗ trợ đánh giá, so sánh nhiều mô hình.


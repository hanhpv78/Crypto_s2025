# 🚀 Crypto Investment Platform

Nền tảng đầu tư Crypto đa chức năng, hỗ trợ phân tích kỹ thuật, tối ưu tham số, backtest chiến lược, lựa chọn mô hình AI và lưu lịch sử khuyến nghị.


######################################################################################
# Cấu trúc thư mục dự án


CryptoInvestmentPlatform/
│

Step1: 
    #xây dựng UI người dùng, 
    # Lấy tất cả các coin có vốn hóa > 500M USD và giao dịch 1 ngày tối thiểu 1M

Step 2: xây dựng các chỉ số và tìm tham số tối ưu cho các chỉ số,... 

├── streamlit_app/                      # Step 1: Giao diện người dùng (UI)
│   ├── streamlit_indicators_demo.py    # App Streamlit: nhập mã coin, chọn chỉ báo, vẽ biểu đồ
│   └── ...                             # Các file UI khác (nếu có)
│
├── indicators_engine/                  # Step 2.1: Module tính toán chỉ báo kỹ thuật
│   ├── __init__.py
│   ├── indicators_engine.py            # Class/fn cho SMA, EMA, MACD, RSI... (tham số động)
│   └── ...                             # Thêm chỉ báo mới tại đây
│
├── parameter_optimizer/                # Step 2.2: Module tối ưu tham số chỉ báo
│   ├── __init__.py
│   ├── optimizer.py                    # Hàm/class tối ưu tham số cho 1 hoặc nhiều chỉ báo
│   └── ...                             # Các thuật toán tối ưu (GridSearch, GA, ... nếu có)
│
├── backtest_engine/                    # Step 2.3: Module backtest hiệu suất
│   ├── __init__.py
│   ├── backtester.py                   # Hàm/class backtest, nhận tín hiệu & tham số, trả về hiệu suất
│   └── ...                             # Các chiến lược backtest khác nhau (nếu có)
│
├── ai_model_selector/                  # Step 2.4: Module chọn & huấn luyện AI
│   ├── __init__.py
│   ├── model_selector.py               # Hàm/class chọn, huấn luyện, đánh giá mô hình AI
│   └── ...                             # Các thuật toán AI (Random Forest, XGBoost, ... nếu có)
│
├── history_logger/                     # Step 2.5: Module lưu lịch sử tối ưu & khuyến nghị
│   ├── __init__.py
│   ├── logger.py                       # Hàm/class lưu kết quả tối ưu, backtest, AI, khuyến nghị
│   └── ...                             # Kết nối file/db/cloud (nếu có)
│
├── data/                               # Thư mục dữ liệu (nếu cần)
│   └── ...                             # File dữ liệu mẫu, kết quả backtest, v.v.
│
├── docs/                               # Tài liệu hướng dẫn, mô tả module
│   ├── README.md                       # Tổng quan dự án, hướng dẫn sử dụng
│   ├── INDICATORS_ENGINE.md            # Hướng dẫn sử dụng Indicators Engine
│   ├── PARAMETER_OPTIMIZER.md          # Hướng dẫn sử dụng Parameter Optimizer
│   ├── BACKTEST_ENGINE.md              # Hướng dẫn sử dụng Backtest Engine
│   ├── AI_MODEL_SELECTOR.md            # Hướng dẫn sử dụng AI Model Selector
│   ├── HISTORY_LOGGER.md               # Hướng dẫn sử dụng History Logger
│   └── ...                             # Các tài liệu chi tiết khác
│
└── requirements.txt                    # Danh sách thư viện Python cần cài đặt


############################################################################################
## 📅 Tiến độ dự án

| Step | Module                | Trạng thái      | Ngày bắt đầu | Ngày kết thúc | Mô tả ngắn gọn |
|------|-----------------------|-----------------|--------------|---------------|---------------|
| 1    | Giao diện Streamlit   | **Hoàn thành**  | 2025-06-13   | 2025-06-17    | Giao diện nhập coin, chọn chỉ báo, nhập tham số động, add nhiều chart, tách chỉ báo chính/phụ |
| 2.1  | Indicators Engine     | **Hoàn thành**  | 2025-06-13   | 2025-06-17    | Module tính toán chỉ báo kỹ thuật (SMA, EMA, MACD, RSI, v.v.), mở rộng dễ dàng |
| 2.2  | Parameter Optimizer   | **Đang làm**    | 2025-06-18   | ...           | Module tối ưu tham số cho từng chỉ báo hoặc nhiều chỉ báo cùng lúc |
| 2.3  | Backtest Engine       | **Sẽ triển khai** | ...        | ...           | Module backtest hiệu suất, đánh giá bộ tham số trên dữ liệu lịch sử |
| 2.4  | AI Model Selector     | **Sẽ triển khai** | ...        | ...           | Module chọn, huấn luyện, đánh giá mô hình AI dự báo tín hiệu |
| 2.5  | History Logger        | **Sẽ triển khai** | ...        | ...           | Module lưu lại kết quả tối ưu, backtest, khuyến nghị AI |

---

## 📝 Chi tiết từng Step & Module

### **Step 1: Giao diện Streamlit**
- **Trạng thái:** Hoàn thành (2025-06-13 → 2025-06-17)
- **Chức năng:**  
  - Nhập mã coin, chọn khung thời gian.
  - Chọn chỉ báo kỹ thuật, nhập tham số động.
  - Add nhiều biểu đồ giá, mỗi biểu đồ chọn chỉ báo riêng.
  - Tách chỉ báo chính/phụ trên biểu đồ (subplots).
- **File chính:** `streamlit_app/streamlit_indicators_demo.py`

---

### **Step 2.1: Indicators Engine**
- **Trạng thái:** Hoàn thành (2025-06-13 → 2025-06-17)
- **Chức năng:**  
  - Module tính toán các chỉ báo kỹ thuật (SMA, EMA, MACD, RSI, Bollinger Bands, ATR, CCI, Stochastic, ADX, Williams %R, ...)
  - Mỗi chỉ báo là một hàm/class độc lập, nhận tham số động.
  - Dễ dàng mở rộng, bổ sung chỉ báo mới.
- **File chính:** `indicators_engine/indicators_engine.py`

---

### **Step 2.2: Parameter Optimizer**
- **Trạng thái:** Đang làm (2025-06-18 → ...)
- **Chức năng:**  
  - Tối ưu tham số cho từng chỉ báo hoặc nhiều chỉ báo cùng lúc.
  - Đầu vào: danh sách chỉ báo, dải tham số, dữ liệu giá.
  - Đầu ra: bộ tham số tối ưu theo tiêu chí (accuracy, lợi nhuận backtest...).
  - Tách biệt logic tối ưu khỏi logic AI và backtest.
- **File chính:** `parameter_optimizer/optimizer.py`

---

### **Step 2.3: Backtest Engine**
- **Trạng thái:** Sẽ triển khai
- **Chức năng:**  
  - Module backtest độc lập, nhận tín hiệu từ chỉ báo và tham số tối ưu.
  - Đầu ra: các chỉ số hiệu suất (lợi nhuận, drawdown, winrate...).
  - Có thể dùng lại cho nhiều chiến lược khác nhau.
- **File chính:** `backtest_engine/backtester.py`

---

### **Step 2.4: AI Model Selector**
- **Trạng thái:** Sẽ triển khai
- **Chức năng:**  
  - Chọn và huấn luyện các thuật toán AI khác nhau (Random Forest, XGBoost, v.v.).
  - Đầu vào: dữ liệu chỉ báo với tham số tối ưu.
  - Đầu ra: mô hình dự báo tín hiệu mua/bán/nắm giữ.
- **File chính:** `ai_model_selector/model_selector.py`

---

### **Step 2.5: History Logger**
- **Trạng thái:** Sẽ triển khai
- **Chức năng:**  
  - Lưu lại kết quả tối ưu, hiệu suất backtest, khuyến nghị AI.
  - Có thể dùng file, database hoặc cloud storage.
- **File chính:** `history_logger/logger.py`

---

## 🔧 Hướng dẫn cài đặt & chạy thử

1. **Cài đặt thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

2. **Chạy giao diện Streamlit:**
    ```bash
    python -m streamlit run streamlit_app/streamlit_indicators_demo.py
    ```

3. **Các module khác:**  
   Xem hướng dẫn chi tiết trong thư mục `docs/` hoặc README của từng module.

---

## 📌 Ghi chú phát triển

- Ưu tiên phát triển Indicators Engine và Parameter Optimizer trước, vì đây là nền tảng cho các module sau.
- Khi hoàn thiện từng module, cập nhật trạng thái và ngày bắt đầu/kết thúc vào bảng trên.
- Tài liệu chi tiết, ví dụ sử dụng, hướng dẫn mở rộng sẽ được cập nhật trong thư mục `docs/`.

---

**Mọi thắc mắc, góp ý hoặc yêu cầu mở rộng, vui lòng liên hệ nhóm phát triển!**

---


```
# Crypto_s2025

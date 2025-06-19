import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from technical_indicators.indicators_engine import IndicatorsEngine

st.title("Demo Indicators Engine - Linh động")

symbol = st.text_input("Nhập mã coin (ví dụ: BTC-USD)", "BTC-USD")
period = st.selectbox("Chọn khung thời gian", ["1mo", "3mo", "6mo", "1y"], index=2)

df = yf.download(symbol, period=period, interval="1d")
if df.empty:
    st.warning("Không lấy được dữ liệu.")
    st.stop()

engine = IndicatorsEngine(df)

# 1. Chọn indicator và nhập tham số động
indicator_list = [
    "SMA", "EMA", "RSI", "MACD", "Bollinger Bands", "ATR", "CCI", "Stochastic", "ADX", "Williams %R"
]
selected_indicators = st.multiselect("Chọn chỉ báo kỹ thuật muốn tính toán", indicator_list)

indicator_params = {}
for ind in selected_indicators:
    if ind in ["SMA", "EMA", "RSI", "ATR", "CCI", "ADX", "Williams %R"]:
        params = st.text_input(f"Nhập các window cho {ind} (cách nhau bởi dấu phẩy)", "20", key=f"{ind}_params")
        try:
            windows = [int(x.strip()) for x in params.split(",") if x.strip().isdigit()]
        except:
            windows = []
        indicator_params[ind] = windows
    elif ind == "MACD":
        params = st.text_input("Nhập các bộ (fast-slow) cho MACD, ví dụ: 12-26, 5-35", "12-26", key="MACD_params")
        macd_pairs = []
        for pair in params.split(","):
            try:
                fast, slow = map(int, pair.strip().split("-"))
                macd_pairs.append((fast, slow))
            except:
                pass
        indicator_params[ind] = macd_pairs
    elif ind == "Bollinger Bands":
        params = st.text_input("Nhập các window cho Bollinger Bands (cách nhau bởi dấu phẩy)", "20", key="BB_params")
        try:
            windows = [int(x.strip()) for x in params.split(",") if x.strip().isdigit()]
        except:
            windows = []
        indicator_params[ind] = windows
    elif ind == "Stochastic":
        params = st.text_input("Nhập các window cho Stochastic (cách nhau bởi dấu phẩy)", "14", key="Stoch_params")
        try:
            windows = [int(x.strip()) for x in params.split(",") if x.strip().isdigit()]
        except:
            windows = []
        indicator_params[ind] = windows

# 2. Tính toán các chỉ báo đã chọn với tham số động
for ind, params in indicator_params.items():
    if ind == "SMA":
        for w in params:
            engine.sma(window=w)
    elif ind == "EMA":
        for w in params:
            engine.ema(window=w)
    elif ind == "RSI":
        for w in params:
            engine.rsi(window=w)
    elif ind == "ATR":
        for w in params:
            engine.atr(window=w)
    elif ind == "CCI":
        for w in params:
            engine.cci(window=w)
    elif ind == "ADX":
        for w in params:
            engine.adx(window=w)
    elif ind == "Williams %R":
        for w in params:
            engine.williams_r(lbp=w)
    elif ind == "MACD":
        for fast, slow in params:
            engine.macd(window_fast=fast, window_slow=slow)
    elif ind == "Bollinger Bands":
        for w in params:
            engine.bollinger_bands(window=w)
    elif ind == "Stochastic":
        for w in params:
            engine.stochastic(window=w)

df_ind = engine.get_df()
df_ind.columns = [col[0] if isinstance(col, tuple) else col for col in df_ind.columns]
st.dataframe(df_ind.tail(20))

# 3. Add nhiều biểu đồ giá linh động
if "charts" not in st.session_state:
    st.session_state.charts = [{"name": "Biểu đồ giá 1"}]

if st.button("Add biểu đồ giá mới"):
    st.session_state.charts.append({"name": f"Biểu đồ giá {len(st.session_state.charts)+1}"})

all_cols = [col for col in df_ind.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume']]

for i, chart in enumerate(st.session_state.charts):
    with st.expander(chart["name"], expanded=True):
        indicators = st.multiselect(
            f"Chỉ báo cho {chart['name']}",
            all_cols,
            default=[],
            key=f"indicators_{i}"
        )

        # Phân loại chỉ báo chính/phụ
        main_indicators = [col for col in indicators if col.startswith(("SMA", "EMA", "BB_"))]
        sub_indicators = [col for col in indicators if col not in main_indicators]

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=("Biểu đồ giá", "Chỉ báo phụ")
        )

        # Vẽ giá và chỉ báo chính ở vùng trên
        fig.add_trace(go.Candlestick(
            x=df_ind.index,
            open=df_ind['Open'],
            high=df_ind['High'],
            low=df_ind['Low'],
            close=df_ind['Close'],
            name='Giá'
        ), row=1, col=1)

        for col in main_indicators:
            fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind[col], mode='lines', name=col), row=1, col=1)

        # Vẽ chỉ báo phụ ở vùng dưới
        for col in sub_indicators:
            fig.add_trace(go.Scatter(x=df_ind.index, y=df_ind[col], mode='lines', name=col), row=2, col=1)

        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True, key=f"plotly_chart_{i}")
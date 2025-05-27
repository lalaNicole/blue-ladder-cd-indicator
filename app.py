import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="蓝色梯子 + CD 抄底指标", layout="wide")
st.title("📈 蓝色梯子 + CD 抄底指标图表")

# 用户输入
ticker = st.text_input("请输入股票代码（如：AAPL, TSLA, META）", value="META")
start_date = st.date_input("开始时间", value=pd.to_datetime("2022-01-01"))
end_date = st.date_input("结束时间", value=pd.to_datetime("2024-12-31"))

# 数据下载与缓存
@st.cache_data
def load_data(ticker, start, end):
    return yf.download(ticker, start=start, end=end)

df = load_data(ticker, start_date, end_date)

# 添加均线组
ema_periods = [5, 10, 20, 60, 120]
for period in ema_periods:
    df[f"EMA_{period}"] = df['Close'].ewm(span=period, adjust=False).mean()

# 计算 MACD
df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
df['MACD'] = df['EMA12'] - df['EMA26']
df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# 计算 RSI
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

df['RSI'] = compute_rsi(df['Close'])

# CD 抄底信号
df['CD_Signal'] = (
    (df['RSI'] < 30) &
    (df['MACD'] > df['Signal']) &
    (df['MACD'].shift(1) < df['Signal'].shift(1))
)

# 创建图表
fig = go.Figure()

# 添加 K 线
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'],
    name='K线图'))

# 添加 蓝色梯子：EMA5/10/20
for period in [5, 10, 20]:
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[f"EMA_{period}"],
        mode='lines',
        line=dict(width=1, color='blue'),
        name=f'EMA{period}'))

# 添加 黄色梯子：EMA60/120
for period in [60, 120]:
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[f"EMA_{period}"],
        mode='lines',
        line=dict(width=1, color='orange'),
        name=f'EMA{period}'))

# 添加 CD 抄底点
cd_dates = df[df['CD_Signal']].index
cd_prices = df[df['CD_Signal']]['Close']
fig.add_trace(go.Scatter(
    x=cd_dates,
    y=cd_prices,
    mode='markers',
    marker=dict(size=10, color='red'),
    name='CD抄底信号'))

fig.update_layout(
    title=f"{ticker} 蓝色梯子 + CD 指标图表",
    xaxis_title='时间', yaxis_title='价格',
    template='plotly_dark',
    height=700
)

st.plotly_chart(fig, use_container_width=True)


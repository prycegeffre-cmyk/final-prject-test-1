import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import StringIO

# -----------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------
st.set_page_config(
    page_title="FIN 330 • Global Stock & Portfolio Dashboard",
    layout="wide"
)

# -----------------------------------------------------------
# HEADER
# -----------------------------------------------------------
st.markdown(
    """
    <div style="background: linear-gradient(90deg, #1e40af, #60a5fa); 
                padding: 40px; 
                text-align: center; 
                color: white; 
                border-radius: 12px;">
        <h1 style="font-size: 42px;">🌍 FIN 330 • Global Stock & Portfolio Dashboard</h1>
        <p style="font-size: 20px;">Real Yahoo Finance Data • Full Project • Ready for Submission</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------
# TABS
# -----------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Part 1: Single Stock",
    "📦 Part 2: Portfolio",
    "🔄 Compare Stocks",
    "📄 Full Report"
])

# =====================================================================================
#                                   PART 1 — SINGLE STOCK
# =====================================================================================
with tab1:
    st.header("Part 1: Individual Stock Analysis (Past 6 Months)")
    ticker = st.text_input("Enter Ticker:", "AAPL").upper()

    if st.button("🚀 Analyze Stock", key="p1"):

        data = yf.download(ticker, period="6mo")

        if data.empty:
            st.error("Ticker not found.")
        else:
            # Moving averages
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()

            # RSI
            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss
            data["RSI"] = 100 - (100 / (1 + rs))

            # Volatility
            data["Returns"] = data["Close"].pct_change()
            vol = data["Returns"].std() * np.sqrt(252)

            # Trend
            price = data["Close"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]

            if price > ma20 > ma50:
                trend = "🟢 Strong Uptrend"
                rec = "BUY"
            elif price < ma20 < ma50:
                trend = "🔴 Downtrend"
                rec = "SELL"
            else:
                trend = "🟡 Sideways"
                rec = "HOLD"

            rsi_val = round(data["RSI"].iloc[-1], 2)
            if rsi_val > 70:
                rsi_state = "Overbought"
            elif rsi_val < 30:
                rsi_state = "Oversold"
            else:
                rsi_state = "Neutral"

            # ---------------------- Metrics ----------------------
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", f"${price:.2f}")
            col2.metric("20-day MA", f"${ma20:.2f}")
            col3.metric("50-day MA", f"${ma50:.2f}")
            col4.metric("Trend", trend)

            col5, col6 = st.columns(2)
            col5.metric("RSI (14-day)", rsi_val, rsi_state)
            col6.metric("Volatility", f"{vol*100:.2f}%")

            # ---------------------- Price Chart ----------------------
            st.subheader("📈 Price Chart (with Moving Averages)")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Close"))
            fig.add_trace(go.Scatter(x=data.index, y=data["MA20"], name="MA20"))
            fig.add_trace(go.Scatter(x=data.index, y=data["MA50"], name="MA50"))
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

            # RSI Chart
            st.subheader("📉 RSI Chart")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI"))
            fig2.add_hline(y=70, line_dash="dot")
            fig2.add_hline(y=30, line_dash="dot")
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)

            # Interpretation
            st.subheader("📄 Interpretation")
            st.info(
                f"""
                **Trend:** {trend}  
                **RSI:** {rsi_val} ({rsi_state})  
                **Volatility:** {vol*100:.2f}%  
                **Recommendation:** **{rec}**  
                """
            )

# =====================================================================================
#                               PART 2 — PORTFOLIO VS SPY
# =====================================================================================
with tab2:
    st.header("Part 2: Portfolio Performance vs SPY (1 Year)")

    st.write("Enter 5 stocks and weights (must total 100%).")

    tickers = []
    weights = []

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            t = st.text_input(f"Stock {i+1}", ["AAPL","MSFT","GOOGL","AMZN","NVDA"][i]).upper()
            w = st.number_input(f"Weight {i+1} (%)", 0, 100, [25,20,20,20,15][i])
            tickers.append(t)
            weights.append(w)

    if sum(weights) != 100:
        st.error("Weights must add to 100%.")
    else:
        if st.button("🚀 Analyze Portfolio", key="p2"):
            data = yf.download(tickers + ["SPY"], period="1y")["Close"]

            port_returns = (data[tickers].pct_change() * (np.array(weights)/100)).sum(axis=1)
            spy_returns = data["SPY"].pct_change()

            port_cum = (1 + port_returns).cumprod()
            spy_cum = (1 + spy_returns).cumprod()

            # Metrics
            port_total = (port_cum.iloc[-1] - 1) * 100
            spy_total = (spy_cum.iloc[-1] - 1) * 100
            outperf = port_total - spy_total
            vol = port_returns.std() * np.sqrt(252)
            sharpe = (port_returns.mean()*252) / (vol if vol>0 else 1)

            # Display
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Portfolio Return", f"{port_total:.2f}%")
            col2.metric("SPY Return", f"{spy_total:.2f}%")
            col3.metric("Outperformance", f"{outperf:.2f}%")
            col4.metric("Volatility", f"{vol*100:.2f}%")
            col5.metric("Sharpe Ratio", f"{sharpe:.2f}")

            # Chart
            st.subheader("📈 Portfolio vs SPY — Cumulative Returns")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=port_cum.index, y=port_cum, name="Portfolio"))
            fig.add_trace(go.Scatter(x=spy_cum.index, y=spy_cum, name="SPY"))
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

            # Pie chart
            st.subheader("🥧 Portfolio Allocation")
            fig2 = px.pie(values=weights, names=tickers)
            st.plotly_chart(fig2, use_container_width=True)

            st.info(
                f"""
                Your portfolio returned **{port_total:.2f}%**,  
                SPY returned **{spy_total:.2f}%**,  
                so you **outperformed by {outperf:.2f}%** 🎉  
                """
            )

# =====================================================================================
#                                  PART 3 — STOCK COMPARISON
# =====================================================================================
with tab3:
    st.header("Compare Up to 4 Stocks")

    comp_tickers = st.text_input("Enter up to 4 tickers (comma separated):", "AAPL, MSFT, NVDA, GOOGL").upper().split(",")

    if st.button("🔄 Compare Stocks", key="p3"):
        comp_tickers = [t.strip() for t in comp_tickers[:4]]

        data = yf.download(comp_tickers, period="1y")["Close"]

        # Chart
        st.subheader("📈 Price Comparison Chart")
        fig = go.Figure()
        for col in data.columns:
            fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col))
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

        # Correlation
        st.subheader("🔥 Correlation Heatmap")
        corr = data.pct_change().corr()
        fig2 = px.imshow(corr, text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

# =====================================================================================
#                                  PART 4 — REPORT EXPORT
# =====================================================================================
with tab4:
    st.header("📄 Full Project Report")

    text = """
FIN 330 Final Project Report

Part 1: Single Stock Analysis
✓ Trend
✓ RSI
✓ Moving averages
✓ Volatility
✓ Recommendation

Part 2: Portfolio (5 Stocks)
✓ 1-year performance
✓ SPY benchmark
✓ Cumulative returns
✓ Volatility & Sharpe ratio

Part 3: Comparison Tool
✓ Multi-stock chart
✓ Correlation heatmap
"""

    st.download_button(
        "📥 Download Report",
        data=text,
        file_name="FIN330_Final_Project_Report.txt"
    )

    st.success("Your report is ready for submission!")

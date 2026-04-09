import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="FIN 330 Final Project",
    page_icon="📈",
    layout="wide"
)

st.title("📊 FIN 330 Final Project • Stock Analytics & Portfolio Dashboard")
st.markdown("**Every requirement from the project document is shown step-by-step**")

# ====================== PART 1: INDIVIDUAL STOCK ANALYSIS ======================
with st.expander("🔍 Part 1: Individual Stock Analysis (6 Months)", expanded=True):
    st.subheader("Step 1: Data Collection")
    ticker = st.text_input("Stock Ticker", value="AAPL", max_chars=5).upper().strip()
    
    if st.button("🚀 Run Full Stock Analysis", type="primary", use_container_width=True):
        with st.spinner("Downloading 6 months of daily data..."):
            try:
                data = yf.download(ticker, period="6mo", progress=False)
                if data.empty:
                    st.error("Invalid ticker or no data available.")
                    st.stop()
                
                # Clean data - use only Close price
                close = data['Close'].dropna()
                st.caption("✅ Cleaned daily closing prices (last 5 rows)")
                st.dataframe(close.tail(5), use_container_width=True)
                
                current_price = close.iloc[-1]
                
                # Step 2: Trend Analysis
                st.subheader("Step 2: Trend Analysis")
                ma20 = close.rolling(20).mean().iloc[-1]
                ma50 = close.rolling(50).mean().iloc[-1]
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Current Price", f"${current_price:.2f}")
                col2.metric("20-day MA", f"${ma20:.2f}")
                col3.metric("50-day MA", f"${ma50:.2f}")
                
                if current_price > ma20 > ma50:
                    trend = "Strong Uptrend"
                    color = "🟢"
                elif current_price < ma20 < ma50:
                    trend = "Strong Downtrend"
                    color = "🔴"
                else:
                    trend = "Mixed Trend"
                    color = "🟡"
                col4.metric("Trend", f"{color} {trend}")
                
                # Step 3: RSI
                st.subheader("Step 3: Momentum (RSI)")
                delta = close.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                rsi_signal = "Overbought (Possible Sell)" if rsi > 70 else "Oversold (Possible Buy)" if rsi < 30 else "Neutral"
                st.metric("14-day RSI", f"{rsi:.2f}", rsi_signal)
                
                # Step 4: Volatility
                st.subheader("Step 4: Volatility")
                daily_ret = close.pct_change()
                ann_vol = daily_ret.rolling(20).std().iloc[-1] * np.sqrt(252) * 100
                vol_level = "High (>40%)" if ann_vol > 40 else "Medium (25%-40%)" if ann_vol >= 25 else "Low (<25%)"
                st.metric("20-day Annualized Volatility", f"{ann_vol:.2f}%", vol_level)
                
                # Step 5: Recommendation
                st.subheader("Step 5: Trading Recommendation")
                if trend == "Strong Uptrend" and rsi < 70 and ann_vol < 40:
                    rec = "BUY"
                    expl = "Strong uptrend, neutral RSI, moderate volatility"
                elif rsi > 70 or trend == "Strong Downtrend":
                    rec = "SELL"
                    expl = "Overbought or downtrend detected"
                elif rsi < 30:
                    rec = "BUY"
                    expl = "Oversold conditions"
                else:
                    rec = "HOLD"
                    expl = "Mixed signals - monitor"
                
                if rec == "BUY":
                    st.success(f"✅ **{rec}** — {expl}")
                elif rec == "SELL":
                    st.error(f"❌ **{rec}** — {expl}")
                else:
                    st.warning(f"⏸️ **{rec}** — {expl}")
                
                # Chart
                st.subheader("Price + Moving Averages Chart")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data.index, y=close, name="Close Price", line=dict(color="#60a5fa", width=2)))
                fig.add_trace(go.Scatter(x=data.index, y=close.rolling(20).mean(), name="20-day MA"))
                fig.add_trace(go.Scatter(x=data.index, y=close.rolling(50).mean(), name="50-day MA"))
                fig.update_layout(template="plotly_dark", height=420, legend=dict(orientation="h"))
                st.plotly_chart(fig, use_container_width=True)
                
                # Written Interpretation
                st.subheader("📝 Written Interpretation (Part 1)")
                st.markdown(f"""
                - **Trend observed**: {trend}  
                - **RSI indicated**: {rsi_signal} (value = {rsi:.2f})  
                - **Volatility suggested**: {vol_level} ({ann_vol:.2f}%)  
                - **Final recommendation**: **{rec}** — {expl}
                """)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ====================== PART 2: PORTFOLIO ======================
with st.expander("📦 Part 2: Portfolio Performance Dashboard (1 Year vs SPY)", expanded=False):
    st.subheader("Step 1: Portfolio Setup (5 stocks, weights sum to 100%)")
    
    default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    default_weights = [25.0, 20.0, 20.0, 20.0, 15.0]
    
    df_input = pd.DataFrame({"Ticker": default_tickers, "Weight (%)": default_weights})
    edited_df = st.data_editor(df_input, num_rows="fixed", use_container_width=True, hide_index=True)
    
    weights = edited_df["Weight (%)"].values / 100.0
    tickers = [t.upper().strip() for t in edited_df["Ticker"]]
    
    if st.button("🚀 Analyze Portfolio", type="primary", use_container_width=True):
        if abs(weights.sum() - 1.0) > 0.001:
            st.error("Weights must sum to 100%")
            st.stop()
        
        with st.spinner("Downloading 1-year data for portfolio + SPY..."):
            try:
                prices = yf.download(tickers, period="1y", progress=False)['Adj Close']
                spy = yf.download("SPY", period="1y", progress=False)['Adj Close']
                
                common_idx = prices.index.intersection(spy.index)
                prices = prices.loc[common_idx].dropna()
                spy = spy.loc[common_idx]
                
                stock_rets = prices.pct_change().dropna()
                spy_rets = spy.pct_change().dropna()
                port_daily = (stock_rets * weights).sum(axis=1)
                
                port_cum = (1 + port_daily).cumprod()
                spy_cum = (1 + spy_rets).cumprod()
                
                # Metrics
                port_total = (port_cum.iloc[-1] - 1) * 100
                spy_total = (spy_cum.iloc[-1] - 1) * 100
                outperf = port_total - spy_total
                
                port_vol = port_daily.std() * np.sqrt(252) * 100
                spy_vol = spy_rets.std() * np.sqrt(252) * 100
                
                # Sharpe (above & beyond)
                rf = 0.042  # 4.2% risk-free rate
                port_ann_ret = port_daily.mean() * 252
                port_sharpe = (port_ann_ret - rf) / (port_daily.std() * np.sqrt(252)) if port_daily.std() != 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Portfolio Total Return", f"{port_total:.2f}%")
                col2.metric("SPY Benchmark", f"{spy_total:.2f}%")
                col3.metric("Outperformance", f"{outperf:+.2f}%")
                
                col4, col5 = st.columns(2)
                col4.metric("Portfolio Volatility", f"{port_vol:.2f}%")
                col5.metric("Sharpe Ratio", f"{port_sharpe:.3f}")
                
                # Cumulative chart
                st.subheader("Cumulative Returns vs SPY")
                fig = px.line(pd.DataFrame({"Portfolio": port_cum, "SPY": spy_cum}), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📝 Written Interpretation (Part 2)")
                st.success(f"Portfolio {'outperformed' if outperf > 0 else 'underperformed'} SPY by {outperf:.2f}%")
                st.info(f"Portfolio was {'more' if port_vol > spy_vol else 'less'} risky than SPY.")
                
            except Exception as e:
                st.error(f"Portfolio error: {str(e)}")

st.caption("✅ Fixed & Ready • All project steps are now correctly implemented • Redeploy on Streamlit Cloud")

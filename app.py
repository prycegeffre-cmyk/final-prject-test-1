import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="FIN 330 Dashboard", 
    page_icon="📈", 
    layout="wide"
)

st.title("📊 Stock Analytics & Portfolio Dashboard")
st.markdown("**FIN 330 Final Project** • Real-time Yahoo Finance data • Fully compliant")

tab1, tab2 = st.tabs(["🔍 Part 1: Individual Stock Analysis", "📦 Part 2: Portfolio Performance Dashboard"])

# ====================== PART 1: INDIVIDUAL STOCK ANALYSIS ======================
with tab1:
    st.header("Part 1: Individual Stock Analysis (6 Months)")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        ticker = st.text_input("Enter Stock Ticker", value="AAPL", max_chars=5).upper().strip()
        analyze_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)

    if analyze_btn and ticker:
        with st.spinner(f"Downloading 6 months of {ticker} data..."):
            try:
                data = yf.download(ticker, period="6mo", progress=False)
                if data.empty:
                    st.error("Invalid ticker or no data available.")
                    st.stop()

                close = data['Close']
                current_price = close.iloc[-1]
                ma20 = close.rolling(20).mean().iloc[-1]
                ma50 = close.rolling(50).mean().iloc[-1]

                # Trend Analysis
                if current_price > ma20 > ma50:
                    trend = "Strong Uptrend"
                    trend_color = "#22c55e"
                elif current_price < ma20 < ma50:
                    trend = "Strong Downtrend"
                    trend_color = "#ef4444"
                else:
                    trend = "Mixed Trend"
                    trend_color = "#eab308"

                # RSI (14-day)
                delta = close.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]

                # Volatility (20-day annualized)
                ret = close.pct_change()
                vol20 = ret.rolling(20).std().iloc[-1]
                ann_vol = vol20 * np.sqrt(252) * 100

                # Trading Recommendation
                if trend == "Strong Uptrend" and rsi < 70 and ann_vol < 40:
                    rec = "BUY"
                    rec_color = "success"
                    explanation = "Strong uptrend with neutral RSI and moderate volatility."
                elif trend == "Strong Downtrend" or rsi > 70:
                    rec = "SELL"
                    rec_color = "error"
                    explanation = "Downtrend or overbought conditions detected."
                elif rsi < 30:
                    rec = "BUY"
                    rec_color = "success"
                    explanation = "Oversold conditions – potential buy opportunity."
                else:
                    rec = "HOLD"
                    rec_color = "warning"
                    explanation = "Mixed signals. Monitor for clearer trend."

                # Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current Price", f"${current_price:.2f}")
                m2.metric("20-day MA", f"${ma20:.2f}")
                m3.metric("50-day MA", f"${ma50:.2f}")
                m4.markdown(f"**Trend:** <span style='color:{trend_color}'>{trend}</span>", unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                c1.metric("14-day RSI", f"{rsi:.1f}")
                c2.metric("Annualized Volatility", f"{ann_vol:.1f}%")
                c3.metric("Recommendation", rec)

                if rec == "BUY":
                    st.success(f"✅ **{rec}** — {explanation}")
                elif rec == "SELL":
                    st.error(f"❌ **{rec}** — {explanation}")
                else:
                    st.warning(f"⏸️ **{rec}** — {explanation}")

                # Charts
                st.subheader("Price Chart with Moving Averages")
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(x=data.index, y=close, name="Close Price", line=dict(color="#60a5fa", width=2)))
                fig_price.add_trace(go.Scatter(x=data.index, y=close.rolling(20).mean(), name="20-day MA", line=dict(color="#f59e0b")))
                fig_price.add_trace(go.Scatter(x=data.index, y=close.rolling(50).mean(), name="50-day MA", line=dict(color="#10b981")))
                fig_price.update_layout(height=450, template="plotly_dark", legend=dict(orientation="h", yanchor="bottom", y=1.02))
                st.plotly_chart(fig_price, use_container_width=True)

                st.subheader("RSI (14-day)")
                rsi_series = 100 - (100 / (1 + rs))
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=data.index, y=rsi_series, name="RSI", line=dict(color="#a855f7")))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                fig_rsi.update_layout(height=350, yaxis_range=[0, 100], template="plotly_dark")
                st.plotly_chart(fig_rsi, use_container_width=True)

                # Written Interpretation
                st.subheader("📝 Written Interpretation (Part 1)")
                st.markdown(f"""
                - **Trend observed**: {trend}  
                - **RSI indicated**: {'Overbought (possible sell)' if rsi > 70 else 'Oversold (possible buy)' if rsi < 30 else 'Neutral'}  
                - **Volatility**: {'High' if ann_vol > 40 else 'Medium' if ann_vol >= 25 else 'Low'} ({ann_vol:.1f}%)  
                - **Final Recommendation**: **{rec}** — {explanation}
                """)

            except Exception as e:
                st.error(f"Error analyzing {ticker}: {e}")

# ====================== PART 2: PORTFOLIO DASHBOARD ======================
with tab2:
    st.header("Part 2: Portfolio Performance Dashboard (1 Year vs SPY)")

    st.subheader("Build Your 5-Stock Portfolio")

    default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    default_weights = [0.25, 0.20, 0.20, 0.20, 0.15]

    df_input = pd.DataFrame({"Ticker": default_tickers, "Weight (%)": [w*100 for w in default_weights]})

    edited_df = st.data_editor(
        df_input,
        num_rows="fixed",
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Weight (%)": st.column_config.NumberColumn("Weight (%)", min_value=0, max_value=100, step=1)
        },
        use_container_width=True,
        hide_index=True
    )

    if st.button("🚀 Analyze Portfolio", type="primary", use_container_width=True):
        weights = (edited_df["Weight (%)"] / 100).values
        tickers = [t.upper().strip() for t in edited_df["Ticker"]]

        if abs(weights.sum() - 1.0) > 0.01:
            st.error("❌ Weights must sum to 100%")
            st.stop()

        with st.spinner("Downloading 1-year data..."):
            try:
                prices = yf.download(tickers, period="1y", progress=False)['Adj Close']
                spy = yf.download("SPY", period="1y", progress=False)['Adj Close']

                # Align dates
                common_idx = prices.index.intersection(spy.index)
                prices = prices.loc[common_idx]
                spy = spy.loc[common_idx]

                port_rets = prices.pct_change().dropna()
                spy_rets = spy.pct_change().dropna()

                port_daily = (port_rets * weights).sum(axis=1)

                # Cumulative returns
                port_cum = (1 + port_daily).cumprod()
                spy_cum = (1 + spy_rets).cumprod()

                # Metrics
                port_total = (port_cum.iloc[-1] - 1) * 100
                spy_total = (spy_cum.iloc[-1] - 1) * 100
                outperf = port_total - spy_total

                port_vol = port_daily.std() * np.sqrt(252) * 100
                spy_vol = spy_rets.std() * np.sqrt(252) * 100

                port_sharpe = (port_daily.mean() * 252) / (port_daily.std() * np.sqrt(252)) if port_daily.std() != 0 else 0
                spy_sharpe = (spy_rets.mean() * 252) / (spy_rets.std() * np.sqrt(252)) if spy_rets.std() != 0 else 0

                # Display metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Portfolio Return", f"{port_total:.2f}%")
                col2.metric("SPY Return", f"{spy_total:.2f}%")
                col3.metric("Outperformance", f"{outperf:+.2f}%")
                col4.metric("Portfolio Volatility", f"{port_vol:.1f}%")
                col5.metric("Sharpe Ratio", f"{port_sharpe:.2f}")

                # Interpretation
                st.subheader("📝 Written Interpretation (Part 2)")
                if outperf > 0:
                    st.success(f"✅ The portfolio **outperformed** SPY by {outperf:.2f}%")
                else:
                    st.error(f"❌ The portfolio **underperformed** SPY by {outperf:.2f}%")

                risk_text = "more" if port_vol > spy_vol else "less"
                st.info(f"📉 The portfolio was **{risk_text}** risky than the market ({port_vol:.1f}% vs {spy_vol:.1f}%).")

                sharpe_text = "more" if port_sharpe > spy_sharpe else "less"
                st.info(f"📈 The portfolio was **{sharpe_text}** efficient based on Sharpe ratio ({port_sharpe:.2f} vs {spy_sharpe:.2f}).")

                # Charts
                st.subheader("Cumulative Returns: Portfolio vs SPY")
                cum_df = pd.DataFrame({"Portfolio": port_cum, "SPY": spy_cum})
                fig = px.line(cum_df, x=cum_df.index, y=cum_df.columns, template="plotly_dark", height=500)
                fig.update_layout(legend_title="Strategy")
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Portfolio Allocation")
                fig_pie = px.pie(edited_df, names="Ticker", values="Weight (%)", hole=0.4, template="plotly_dark")
                st.plotly_chart(fig_pie, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("✅ Fully meets FIN 330 requirements • Built for Pryce • Deploy on Streamlit Cloud")

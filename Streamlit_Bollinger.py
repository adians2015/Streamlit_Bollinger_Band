import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="5m Intraday Signal", layout="wide")

st.title("⚡ 5-Minute Intraday Dashboard")
st.caption("Strategy: Price > EMA30 + SMA20 + VWAP")

# ---------------- SESSION STATE ----------------
if "symbols" not in st.session_state:
    st.session_state.symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]

# ---------------- CORE CALCULATION ----------------
def analyze_stock(symbol):
    try:
        # Fetching 5m data. '5d' period ensures we have enough candles for EMA30
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        
        if df.empty or len(df) < 35:
            return None

        # Fix Multi-index columns for yfinance v0.2.x+
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Indicators
        df["EMA30"] = ta.ema(df["Close"], length=30)
        df["MA20"] = ta.sma(df["Close"], length=20)
        # VWAP typically resets daily in intraday charts
        df["VWAP"] = ta.vwap(df["High"], df["Low"], df["Close"], df["Volume"])

        last = df.iloc[-1]
        price = float(last["Close"])
        e30 = float(last["EMA30"])
        m20 = float(last["MA20"])
        vwap = float(last["VWAP"])

        # Signal Logic
        if price > e30 and price > m20 and price > vwap:
            signal, color = "BUY", "green"
        elif price < e30 and price < m20 and price < vwap:
            signal, color = "SELL", "red"
        else:
            signal, color = "NEUTRAL", "gray"

        return {
            "Symbol": symbol,
            "Price": round(price, 2),
            "EMA30": round(e30, 2),
            "MA20": round(m20, 2),
            "VWAP": round(vwap, 2),
            "Signal": signal,
            "Color": color
        }
    except:
        return None

# ---------------- MOBILE UI: METRIC CARDS ----------------
# Force a refresh button for mobile users
if st.button("🔄 Refresh Signals"):
    st.rerun()

results = []
for sym in st.session_state.symbols:
    res = analyze_stock(sym)
    if res:
        results.append(res)

if results:
    # Card view is best for mobile screens
    for item in results:
        with st.container(border=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### {item['Symbol']}")
                st.write(f"**Price:** {item['Price']}")
            with col2:
                # Big Signal Label
                st.markdown(f"<h2 style='text-align:center; color:{item['Color']};'>{item['Signal']}</h2>", unsafe_allow_html=True)
            
            # Indicator breakdown in small text
            st.caption(f"EMA30: {item['EMA30']} | MA20: {item['MA20']} | VWAP: {item['VWAP']}")
else:
    st.error("Could not fetch data. Check your internet or tickers.")
    

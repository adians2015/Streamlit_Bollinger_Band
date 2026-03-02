import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Nifty 100 Intraday", layout="wide")

st.title("⚡ 5m Intraday Signal Dashboard")

# ---------------- SESSION STATE (Storage) ----------------
# This keeps your list active even when the app reruns
if "symbols" not in st.session_state:
    st.session_state.symbols = ["RELIANCE.NS", "TCS.NS"]

# ---------------- USER INPUT SECTION ----------------
with st.sidebar:
    st.header("🔍 Add Stocks")
    st.caption("Use .NS for NSE (e.g., INFIBEAM.NS)")
    
    # Form prevents the app from rerunning on every single keystroke
    with st.form("symbol_form", clear_on_submit=True):
        new_sym = st.text_input("Enter Symbol").upper().strip()
        add_btn = st.form_submit_button("➕ Add to List")
        
    if add_btn and new_sym:
        if new_sym not in st.session_state.symbols:
            st.session_state.symbols.append(new_sym)
            st.success(f"Added {new_sym}")
        else:
            st.warning("Symbol already exists")

    if st.button("🗑️ Clear All Stocks"):
        st.session_state.symbols = []
        st.rerun()

# ---------------- CORE CALCULATION ----------------
def analyze_stock(symbol):
    try:
        # Fetching 5m data for the last 5 days
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        
        if df.empty or len(df) < 35:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Indicator Logic
        df["EMA30"] = ta.ema(df["Close"], length=30)
        df["MA20"] = ta.sma(df["Close"], length=20)
        df["VWAP"] = ta.vwap(df["High"], df["Low"], df["Close"], df["Volume"])

        last = df.iloc[-1]
        price = float(last["Close"])
        e30 = float(last["EMA30"])
        m20 = float(last["MA20"])
        vwap = float(last["VWAP"])

        # Strategy Logic
        if price > e30 and price > m20 and price > vwap:
            sig, col = "BUY", "#00FF00" # Bright Green
        elif price < e30 and price < m20 and price < vwap:
            sig, col = "SELL", "#FF4B4B" # Bright Red
        else:
            sig, col = "NEUTRAL", "#808080" # Gray

        return {
            "Symbol": symbol,
            "Price": round(price, 2),
            "Signal": sig,
            "Color": col,
            "Details": f"EMA30: {round(e30,2)} | MA20: {round(m20,2)} | VWAP: {round(vwap,2)}"
        }
    except:
        return None

# ---------------- DISPLAY DASHBOARD ----------------
if st.button("🔄 Refresh All Signals"):
    st.rerun()

if st.session_state.symbols:
    # Displaying results in mobile-friendly containers
    for sym in st.session_state.symbols:
        data = analyze_stock(sym)
        if data:
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.subheader(data["Symbol"])
                    st.write(f"**Current Price:** ₹{data['Price']}")
                with c2:
                    st.markdown(f"<h3 style='text-align:right; color:{data['Color']};'>{data['Signal']}</h3>", unsafe_allow_html=True)
                st.caption(data["Details"])
        else:
            st.error(f"Could not load {sym}. Check ticker name.")
else:
    st.info("Your watchlist is empty. Add a symbol from the sidebar (e.g., SBIN.NS)")
    

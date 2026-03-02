import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import pytz
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Nifty 5m IST", layout="wide")

st.title("📊 5m Intraday Signal Table (IST)")

# ---------------- SESSION STATE ----------------
if "symbols" not in st.session_state:
    st.session_state.symbols = []

# ---------------- INPUT SECTION ----------------
with st.form("add_stock_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input("Enter Symbol (e.g. RELIANCE, SBIN)", placeholder="Type and hit Enter").upper().strip()
    with col2:
        st.write("##") 
        submit_btn = st.form_submit_button("➕ Add")

if submit_btn and user_input:
    # Auto-append .NS for National Stock Exchange
    clean_ticker = user_input if user_input.endswith(".NS") else f"{user_input}.NS"
    if clean_ticker not in st.session_state.symbols:
        st.session_state.symbols.append(clean_ticker)

# ---------------- CALCULATION LOGIC ----------------
def fetch_data():
    results = []
    # Set Timezone to India
    IST = pytz.timezone('Asia/Kolkata')
    
    for sym in st.session_state.symbols:
        try:
            df = yf.download(sym, period="2d", interval="5m", progress=False)
            if df.empty or len(df) < 35: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Indicators
            df["EMA30"] = ta.ema(df["Close"], length=30)
            df["MA20"] = ta.sma(df["Close"], length=20)
            df["VWAP"] = ta.vwap(df["High"], df["Low"], df["Close"], df["Volume"])

            last = df.iloc[-1]
            price, e30, m20, vwap = last["Close"], last["EMA30"], last["MA20"], last["VWAP"]

            # Strategy Logic
            if price > e30 and price > m20 and price > vwap:
                signal = "🟢 BUY"
            elif price < e30 and price < m20 and price < vwap:
                signal = "🔴 SELL"
            else:
                signal = "⚪ NEUTRAL"

            results.append({
                "Symbol": sym.replace(".NS", ""),
                "Signal": signal,
                "Price": price,
                "VWAP": vwap,
                "EMA30": e30,
                "MA20": m20,
                "Last Update": datetime.now(IST).strftime("%I:%M:%S %p") # IST Format
            })
        except:
            pass
    return results

# ---------------- ACTIONS & DISPLAY ----------------
c1, c2 = st.columns(2)
with c1:
    refresh = st.button("🔄 Refresh Table")
with c2:
    if st.button("🗑️ Clear All"):
        st.session_state.symbols = []
        st.rerun()

if st.session_state.symbols:
    data_list = fetch_data()
    if data_list:
        df_final = pd.DataFrame(data_list)
        
        # Formatting decimals
        numeric_cols = ["Price", "VWAP", "EMA30", "MA20"]
        for col in numeric_cols:
            df_final[col] = df_final[col].map(lambda x: f"{x:.2f}")

        def color_signal(val):
            if "BUY" in val: return 'color: #00CC00; font-weight: bold'
            if "SELL" in val: return 'color: #FF4B4B; font-weight: bold'
            return 'color: #808080'

        st.dataframe(
            df_final.style.map(color_signal, subset=['Signal']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Fetching market data...")
else:
    st.info("Watchlist empty. Add symbols to see IST signals.")
    

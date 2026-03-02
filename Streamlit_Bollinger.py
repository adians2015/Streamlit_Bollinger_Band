import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Nifty 5m Table", layout="wide")

st.title("📊 5m Intraday Signal Table")

# ---------------- SESSION STATE ----------------
if "symbols" not in st.session_state:
    st.session_state.symbols = []

# ---------------- INPUT SECTION (AUTO-CLEAR) ----------------
# Using st.form with clear_on_submit=True clears the box automatically
with st.form("add_stock_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_sym = st.text_input("Enter Ticker", placeholder="e.g. RELIANCE.NS").upper().strip()
    with col2:
        st.write("##") # Spacer
        submit_btn = st.form_submit_button("➕ Add")

if submit_btn and new_sym:
    if new_sym not in st.session_state.symbols:
        st.session_state.symbols.append(new_sym)
    else:
        st.sidebar.warning(f"{new_sym} already in list.")

# ---------------- CALCULATION LOGIC ----------------
def fetch_data():
    results = []
    for sym in st.session_state.symbols:
        try:
            # period="2d" is sufficient for 5m indicators
            df = yf.download(sym, period="2d", interval="5m", progress=False)
            if df.empty or len(df) < 35: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Technical Indicators
            df["EMA30"] = ta.ema(df["Close"], length=30)
            df["MA20"] = ta.sma(df["Close"], length=20)
            df["VWAP"] = ta.vwap(df["High"], df["Low"], df["Close"], df["Volume"])

            last = df.iloc[-1]
            price, e30, m20, vwap = last["Close"], last["EMA30"], last["MA20"], last["VWAP"]

            # Signal Logic
            if price > e30 and price > m20 and price > vwap:
                signal = "🟢 BUY"
            elif price < e30 and price < m20 and price < vwap:
                signal = "🔴 SELL"
            else:
                signal = "⚪ NEUTRAL"

            results.append({
                "Symbol": sym,
                "Signal": signal,
                "Price": price,
                "VWAP": vwap,
                "EMA30": e30,
                "MA20": m20,
                "Time": datetime.now().strftime("%H:%M:%S")
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
        
        # 1. Force two decimal places for all numeric columns
        numeric_cols = ["Price", "VWAP", "EMA30", "MA20"]
        for col in numeric_cols:
            df_final[col] = df_final[col].map(lambda x: f"{x:.2f}")

        # 2. Add color styling to the signal column
        def color_signal(val):
            if "BUY" in val: return 'color: #00CC00; font-weight: bold'
            if "SELL" in val: return 'color: #FF4B4B; font-weight: bold'
            return 'color: #808080'

        st.subheader("📌 Live Watchlist")
        st.dataframe(
            df_final.style.map(color_signal, subset=['Signal']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No data found. Check ticker syntax (e.g. TCS.NS)")
else:
    st.info("Watchlist is empty. Enter a symbol above to start.")
    

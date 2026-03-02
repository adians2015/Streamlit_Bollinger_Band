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

# ---------------- INPUT SECTION ----------------
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        new_sym = st.text_input("Enter Ticker", placeholder="e.g. RELIANCE.NS").upper().strip()
    with col2:
        st.write("##") # Spacer
        add_btn = st.button("➕ Add")

if add_btn and new_sym:
    if new_sym not in st.session_state.symbols:
        st.session_state.symbols.append(new_sym)
    else:
        st.warning("Already in list.")

# ---------------- CALCULATION LOGIC ----------------
def fetch_data():
    results = []
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
                "Price": round(float(price), 2),
                "VWAP": round(float(vwap), 2),
                "EMA30": round(float(e30), 2),
                "MA20": round(float(m20), 2),
                "Time": datetime.now().strftime("%H:%M:%S")
            })
        except:
            pass
    return results

# ---------------- DISPLAY TABLE ----------------
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
        
        # Styling the table for mobile
        def color_signal(val):
            color = 'black'
            if "BUY" in val: color = '#228B22' # Green
            elif "SELL" in val: color = '#DC143C' # Red
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_final.style.applymap(color_signal, subset=['Signal']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Fetching data... Make sure tickers are correct (e.g. SBIN.NS)")
else:
    st.info("Dashboard empty. Add symbols above to begin.")
    

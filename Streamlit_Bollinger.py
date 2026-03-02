import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="5m Intraday Dashboard", layout="wide")

st.title("⚡ 5m Intraday Signal Dashboard")
st.caption("Strategy: Buy if Price > EMA30, MA20, & VWAP | Sell if Price < All")

# ---------------- SESSION STATE ----------------
# Start with an empty list as requested
if "symbols" not in st.session_state:
    st.session_state.symbols = []

# ---------------- INPUT SECTION (ON MAIN SCREEN) ----------------
st.subheader("🔍 Add Stocks to Watch")
with st.form("symbol_form", clear_on_submit=True):
    # Mobile-friendly input: Type ticker and hit 'Add'
    col1, col2 = st.columns([3, 1])
    with col1:
        new_sym = st.text_input("Enter Ticker (e.g., RELIANCE.NS, SBIN.NS)", placeholder="SYMBOL.NS").upper().strip()
    with col2:
        st.write("##") # Alignment spacer
        add_btn = st.form_submit_button("➕ Add")

if add_btn and new_sym:
    if new_sym not in st.session_state.symbols:
        st.session_state.symbols.append(new_sym)
    else:
        st.warning(f"{new_sym} is already in your list.")

# ---------------- ACTION BUTTONS ----------------
c1, c2 = st.columns(2)
with c1:
    if st.button("🔄 Refresh All"):
        st.rerun()
with c2:
    if st.button("🗑️ Clear List"):
        st.session_state.symbols = []
        st.rerun()

st.divider()

# ---------------- CALCULATION FUNCTION ----------------
def get_5m_signal(symbol):
    try:
        # Pulling 5 days of 5m data
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        
        if df.empty or len(df) < 35:
            return "No Data"

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Technical Indicators
        df["EMA30"] = ta.ema(df["Close"], length=30)
        df["MA20"] = ta.sma(df["Close"], length=20)
        df["VWAP"] = ta.vwap(df["High"], df["Low"], df["Close"], df["Volume"])

        last = df.iloc[-1]
        price = float(last["Close"])
        e30 = float(last["EMA30"])
        m20 = float(last["MA20"])
        vwap = float(last["VWAP"])

        # Signal Logic
        if price > e30 and price > m20 and price > vwap:
            return {"sig": "BUY", "col": "#00FF00", "p": round(price, 2), "det": f"VWAP: {round(vwap,2)} | EMA: {round(e30,2)}"}
        elif price < e30 and price < m20 and price < vwap:
            return {"sig": "SELL", "col": "#FF4B4B", "p": round(price, 2), "det": f"VWAP: {round(vwap,2)} | EMA: {round(e30,2)}"}
        else:
            return {"sig": "NEUTRAL", "col": "#808080", "p": round(price, 2), "det": f"VWAP: {round(vwap,2)} | EMA: {round(e30,2)}"}
    except:
        return "Error"

# ---------------- DISPLAY CARDS ----------------
if not st.session_state.symbols:
    st.info("👆 Add a Nifty stock ticker above to see 5m signals.")
else:
    for sym in st.session_state.symbols:
        result = get_5m_signal(sym)
        
        if isinstance(result, dict):
            # Create a clean card for mobile
            with st.container(border=True):
                left, right = st.columns([1, 1])
                with left:
                    st.markdown(f"### {sym}")
                    st.write(f"**Price: ₹{result['p']}**")
                with right:
                    st.markdown(f"<h2 style='text-align:right; color:{result['col']};'>{result['sig']}</h2>", unsafe_allow_html=True)
                st.caption(result['det'])
        else:
            st.error(f"Could not load data for {sym}. Use '.NS' for NSE stocks.")
            

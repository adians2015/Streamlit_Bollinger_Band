import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Bollinger Band Signal Dashboard",
    layout="wide"
)

st.title("📊 Bollinger Band Buy / Sell Signal Dashboard")

st.markdown("""
### Signal Logic
- 🟢 **BUY**  → Close price below Lower Band  
- 🔴 **SELL** → Close price above Upper Band  
- ⚪ **HOLD** → Otherwise  
""")

# ---------------- BOLLINGER SETTINGS (TOP) ----------------
st.subheader("⚙️ Bollinger Band Settings")

col_a, col_b = st.columns(2)

with col_a:
    period = st.number_input(
        "Length (Period)",
        min_value=5,
        max_value=50,
        value=20,
        step=1
    )

with col_b:
    multiplier = st.number_input(
        "Multiplier (Std Dev)",
        min_value=1.0,
        max_value=3.0,
        value=2.0,
        step=0.1
    )

st.divider()

# ---------------- SESSION STATE ----------------
if "symbols" not in st.session_state:
    st.session_state.symbols = []

if "refresh" not in st.session_state:
    st.session_state.refresh = 0  # dummy trigger for refresh

# ---------------- CORE FUNCTION ----------------
def analyze_stock(symbol, period, multiplier):
    try:
        df = yf.download(
            symbol,
            period="6mo",
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna()

        if df.empty or "Close" not in df.columns or len(df) < period:
            return None

        # Bollinger Bands
        df["MA"] = df["Close"].rolling(period).mean()
        df["STD"] = df["Close"].rolling(period).std()
        df["Upper Band"] = df["MA"] + (multiplier * df["STD"])
        df["Lower Band"] = df["MA"] - (multiplier * df["STD"])

        last = df.iloc[-1]

        if pd.isna(last["Upper Band"]) or pd.isna(last["Lower Band"]):
            return None

        # ---------------- SIGNAL LOGIC ----------------
        if last["Close"] > last["Upper Band"]:
            signal = "SELL"
        elif last["Close"] < last["Lower Band"]:
            signal = "BUY"
        else:
            signal = "HOLD"

        return {
            "Symbol": symbol,
            "Close Price": round(float(last["Close"]), 2),
            "Upper Band": round(float(last["Upper Band"]), 2),
            "Lower Band": round(float(last["Lower Band"]), 2),
            "Signal": signal
        }

    except:
        return None

# ---------------- INPUT FORM ----------------
with st.form("add_stock_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])

    with col1:
        stock_symbol = st.text_input(
            "Enter Stock Symbol",
            placeholder="Example: RELIANCE.NS"
        )

    with col2:
        submitted = st.form_submit_button("➕ Add Stock")

# ---------------- ADD STOCK WITH VALIDATION ----------------
if submitted:
    if not stock_symbol:
        st.warning("Please enter a stock symbol.")
    else:
        stock_symbol = stock_symbol.strip().upper()

        if stock_symbol in st.session_state.symbols:
            st.warning("Stock already added.")
        else:
            test_data = analyze_stock(stock_symbol, period, multiplier)
            if test_data is None:
                st.warning("❌ Invalid stock symbol or no data available.")
            else:
                st.session_state.symbols.append(stock_symbol)

# ---------------- DASHBOARD REFRESH BUTTON ----------------
col_r1, col_r2 = st.columns([2, 8])
with col_r1:
    if st.button("🔄 Refresh Dashboard"):
        st.session_state.refresh += 1  # trigger recalculation

# ---------------- DASHBOARD CALCULATION ----------------
results = []

# Trigger refresh
_ = st.session_state.refresh

for sym in st.session_state.symbols:
    data = analyze_stock(sym, period, multiplier)
    if data:
        results.append(data)

# ---------------- DISPLAY DASHBOARD WITH SERIAL NUMBER ----------------
if results:
    df_result = pd.DataFrame(results)

    # Add Serial Number starting from 1
    df_result.insert(0, "S.No", range(1, len(df_result) + 1))

    # Format numeric columns to 2 decimals
    for col in ["Close Price", "Upper Band", "Lower Band"]:
        df_result[col] = df_result[col].map(lambda x: f"{x:.2f}")

    # Highlight signals
    def highlight_signal(val):
        if val == "BUY":
            return "background-color: lightgreen"
        elif val == "SELL":
            return "background-color: lightcoral"
        return ""

    st.subheader("📌 Live Dashboard")
    st.dataframe(
        df_result.style.applymap(highlight_signal, subset=["Signal"]),
        use_container_width=True
    )
else:
    st.info("No valid stocks added yet.")

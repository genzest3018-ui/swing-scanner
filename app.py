import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Swing Scanner", page_icon="📈", layout="centered")

st.title("📈 Swing Trade Scanner")
st.caption("NIFTY 500 + ETFs — Automatic Signal Generator")

capital = st.number_input("💰 Apni Capital Daalo (₹)", min_value=5000, max_value=500000, value=5000, step=1000)

MAX_PRICE = capital * 0.45
RISK = capital * 0.02

nifty500 = {
    "HDFCBANK.NS":"Banking","ICICIBANK.NS":"Banking","SBIN.NS":"Banking",
    "KOTAKBANK.NS":"Banking","AXISBANK.NS":"Banking","BANKBARODA.NS":"Banking",
    "CANBK.NS":"Banking","UNIONBANK.NS":"Banking","PNB.NS":"Banking",
    "IDFCFIRSTB.NS":"Banking","FEDERALBNK.NS":"Banking","RBLBANK.NS":"Banking",
    "BAJFINANCE.NS":"NBFC","CHOLAFIN.NS":"NBFC","MUTHOOTFIN.NS":"NBFC",
    "MANAPPURAM.NS":"NBFC","LICHSGFIN.NS":"NBFC","IRFC.NS":"NBFC",
    "RECLTD.NS":"NBFC","PFC.NS":"NBFC","HUDCO.NS":"NBFC",
    "TCS.NS":"IT","INFY.NS":"IT","WIPRO.NS":"IT","HCLTECH.NS":"IT",
    "TECHM.NS":"IT","MPHASIS.NS":"IT","COFORGE.NS":"IT","PERSISTENT.NS":"IT",
    "SUNPHARMA.NS":"Pharma","DRREDDY.NS":"Pharma","CIPLA.NS":"Pharma",
    "DIVISLAB.NS":"Pharma","AUROPHARMA.NS":"Pharma","LUPIN.NS":"Pharma",
    "BIOCON.NS":"Pharma","ALKEM.NS":"Pharma",
    "NTPC.NS":"Energy","POWERGRID.NS":"Energy","TATAPOWER.NS":"Energy",
    "NHPC.NS":"Energy","SJVN.NS":"Energy","CESC.NS":"Energy","SUZLON.NS":"Energy",
    "RELIANCE.NS":"Oil&Gas","ONGC.NS":"Oil&Gas","IOC.NS":"Oil&Gas",
    "BPCL.NS":"Oil&Gas","GAIL.NS":"Oil&Gas",
    "TATASTEEL.NS":"Metals","JSWSTEEL.NS":"Metals","SAIL.NS":"Metals",
    "HINDALCO.NS":"Metals","VEDL.NS":"Metals","NMDC.NS":"Metals",
    "NALCO.NS":"Metals","HINDZINC.NS":"Metals","JINDALSTEL.NS":"Metals",
    "LT.NS":"Infra","RVNL.NS":"Infra","NBCC.NS":"Infra",
    "RAILTEL.NS":"Infra","BHEL.NS":"Infra","BEL.NS":"Infra","HAL.NS":"Infra",
    "MARUTI.NS":"Auto","TATAMOTORS.NS":"Auto","EICHERMOT.NS":"Auto",
    "HEROMOTOCO.NS":"Auto","MOTHERSON.NS":"Auto","ASHOKLEY.NS":"Auto","TVSMOTOR.NS":"Auto",
    "HINDUNILVR.NS":"FMCG","ITC.NS":"FMCG","NESTLEIND.NS":"FMCG",
    "BRITANNIA.NS":"FMCG","DABUR.NS":"FMCG","MARICO.NS":"FMCG","COLPAL.NS":"FMCG",
    "ZOMATO.NS":"NewAge","IRCTC.NS":"NewAge","NYKAA.NS":"NewAge",
    "BHARTIARTL.NS":"Telecom","IDEA.NS":"Telecom",
    "ULTRACEMCO.NS":"Cement","AMBUJACEM.NS":"Cement","ACC.NS":"Cement",
}

etfs = {
    "NIFTYBEES.NS":"ETF-Nifty50","BANKBEES.NS":"ETF-Banking",
    "ITBEES.NS":"ETF-IT","PHARMABEES.NS":"ETF-Pharma",
    "PSUBNKBEES.NS":"ETF-PSUBank","GOLDBEES.NS":"ETF-Gold",
    "SILVERBEES.NS":"ETF-Silver","INFRABEES.NS":"ETF-Infra",
}

def analyze(symbol, sector, capital):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", auto_adjust=True, progress=False)
        if len(df) < 60:
            return None
        close = df['Close'][symbol]
        volume = df['Volume'][symbol]

        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()
        ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()
        macd = ta.trend.MACD(close)
        bb = ta.volatility.BollingerBands(close)
        vol_avg = volume.rolling(20).mean()

        price = close.iloc[-1]
        if price > MAX_PRICE or price < 10:
            return None

        score = 0
        reasons = []
        rsi_now = rsi.iloc[-1]
        ema20_now = ema20.iloc[-1]
        ema50_now = ema50.iloc[-1]
        macd_now = macd.macd().iloc[-1]
        macd_sig = macd.macd_signal().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        vol_now = volume.iloc[-1]
        vol_avg_now = vol_avg.iloc[-1]

        if 32 < rsi_now < 60: score += 1; reasons.append(f"RSI {rsi_now:.0f}")
        if ema20_now > ema50_now: score += 1; reasons.append("Uptrend")
        if macd_now > macd_sig: score += 1; reasons.append("MACD↑")
        if vol_now > vol_avg_now * 1.2: score += 1; reasons.append("Vol↑")
        if close.iloc[-1] > close.iloc[-3]: score += 1; reasons.append("Momentum")
        if price <= bb_low * 1.02: score += 1; reasons.append("BB Low")

        if score < 4:
            return None

        qty = int(capital / price)
        if qty == 0: return None

        return {
            'Symbol': symbol.replace('.NS',''),
            'Sector': sector,
            'Price': round(price, 1),
            'Score': score,
            'RSI': round(rsi_now, 1),
            'Qty': qty,
            'Invest': round(qty * price),
            'SL': round(price * 0.96, 1),
            'T1': round(price * 1.06, 1),
            'T2': round(price * 1.10, 1),
            'Risk': round(qty * price * 0.04),
            'Why': " | ".join(reasons)
        }
    except:
        return None

if st.button("🔍 Scan Karo", use_container_width=True):
    results = []
    all_symbols = {**etfs, **nifty500}
    progress = st.progress(0)
    status = st.empty()
    total = len(all_symbols)

    for i, (sym, sec) in enumerate(all_symbols.items()):
        status.text(f"Scanning {sym}...")
        r = analyze(sym, sec, capital)
        if r: results.append(r)
        progress.progress((i+1)/total)

    status.text("✅ Scan complete!")
    results = sorted(results, key=lambda x: x['Score'], reverse=True)

    etf_r = [r for r in results if 'ETF' in r['Sector']]
    stk_r = [r for r in results if 'ETF' not in r['Sector']]

    st.markdown("---")
    st.subheader("🏦 ETF Signals — Safest")
    if etf_r:
        for s in etf_r:
            with st.container(border=True):
                st.markdown(f"### ✅ {s['Symbol']} `{s['Sector']}` — Score {s['Score']}/6")
                col1, col2, col3 = st.columns(3)
                col1.metric("Price", f"₹{s['Price']}")
                col2.metric("RSI", s['RSI'])
                col3.metric("Qty", s['Qty'])
                col1.metric("Invest", f"₹{s['Invest']}")
                col2.metric("Stop Loss", f"₹{s['SL']}")
                col3.metric("Risk", f"₹{s['Risk']}")
                st.success(f"T1: ₹{s['T1']} (+6%)   |   T2: ₹{s['T2']} (+10%)")
                st.caption(f"Why: {s['Why']}")
    else:
        st.info("⏳ No ETF signals today")

    st.markdown("---")
    st.subheader("📊 Stock Signals — Sector Wise")
    if stk_r:
        cur_sec = ""
        for s in stk_r:
            if s['Sector'] != cur_sec:
                cur_sec = s['Sector']
                st.markdown(f"#### 📁 {cur_sec}")
            with st.container(border=True):
                st.markdown(f"### ✅ {s['Symbol']} — Score {s['Score']}/6")
                col1, col2, col3 = st.columns(3)
                col1.metric("Price", f"₹{s['Price']}")
                col2.metric("RSI", s['RSI'])
                col3.metric("Qty", s['Qty'])
                col1.metric("Invest", f"₹{s['Invest']}")
                col2.metric("Stop Loss", f"₹{s['SL']}")
                col3.metric("Risk", f"₹{s['Risk']}")
                st.success(f"T1: ₹{s['T1']} (+6%)   |   T2: ₹{s['T2']} (+10%)")
                st.caption(f"Why: {s['Why']}")
    else:
        st.info("⏳ No stock signals today")

    st.markdown("---")
    st.caption(f"Scanned {total} symbols | Capital ₹{capital} | Max Risk/trade ₹{RISK:.0f}")
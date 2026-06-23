import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Swing Scanner", page_icon="📈", layout="wide")

# ── UI STYLING ──
st.markdown("""
<style>
.main { background-color: #0e1117; }
.signal-card { background: #1a1d27; border-radius: 12px; padding: 16px; margin: 8px 0; border-left: 4px solid #00d4aa; }
.etf-card { border-left: 4px solid #ffd700; }
.metric-label { color: #888; font-size: 12px; }
.metric-value { color: #fff; font-size: 18px; font-weight: bold; }
.score-high { color: #00d4aa; font-weight: bold; font-size: 20px; }
.sector-header { color: #ffd700; font-size: 16px; font-weight: bold; margin-top: 16px; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📈 Swing Trade Scanner")
st.markdown("##### NIFTY 500 + ETFs — Yahoo Finance + NSE Data")
st.markdown("---")

# ── INPUTS ──
col1, col2, col3 = st.columns(3)
with col1:
    capital = st.number_input("💰 Capital (₹)", min_value=5000, max_value=1000000, value=5000, step=1000)
with col2:
    timeline = st.selectbox("📅 Timeline", ["3 Days", "1 Week", "2 Weeks"])
with col3:
    min_score = st.selectbox("🎯 Signal Strength", ["Strong (5+/7)", "Medium (4+/7)", "All (3+/7)"])

MAX_PRICE = capital * 0.45

# Timeline settings
if timeline == "3 Days":
    PERIOD, SL, T1, T2 = "1mo", 0.97, 1.04, 1.07
elif timeline == "1 Week":
    PERIOD, SL, T1, T2 = "3mo", 0.96, 1.06, 1.10
else:
    PERIOD, SL, T1, T2 = "6mo", 0.94, 1.08, 1.15

MIN_SCORE = int(min_score.split("(")[1].split("+")[0])

# ── FULL STOCK LIST ──
nifty500 = {
    # Banking
    "HDFCBANK.NS":"Banking","ICICIBANK.NS":"Banking","SBIN.NS":"Banking",
    "KOTAKBANK.NS":"Banking","AXISBANK.NS":"Banking","BANKBARODA.NS":"Banking",
    "CANBK.NS":"Banking","UNIONBANK.NS":"Banking","PNB.NS":"Banking",
    "IDFCFIRSTB.NS":"Banking","FEDERALBNK.NS":"Banking","INDUSINDBK.NS":"Banking",
    "RBLBANK.NS":"Banking","BANDHANBNK.NS":"Banking","KARURVYSYA.NS":"Banking",
    "DCBBANK.NS":"Banking","SOUTHBANK.NS":"Banking","UJJIVANSFB.NS":"Banking",
    "EQUITASBNK.NS":"Banking","ESAFSFB.NS":"Banking",
    # NBFC
    "BAJFINANCE.NS":"NBFC","BAJAJFINSV.NS":"NBFC","CHOLAFIN.NS":"NBFC",
    "MUTHOOTFIN.NS":"NBFC","MANAPPURAM.NS":"NBFC","LICHSGFIN.NS":"NBFC",
    "PNBHOUSING.NS":"NBFC","IRFC.NS":"NBFC","RECLTD.NS":"NBFC",
    "PFC.NS":"NBFC","HUDCO.NS":"NBFC","CANFINHOME.NS":"NBFC",
    "HOMEFIRST.NS":"NBFC","AAVAS.NS":"NBFC","APTUS.NS":"NBFC",
    # IT
    "TCS.NS":"IT","INFY.NS":"IT","WIPRO.NS":"IT","HCLTECH.NS":"IT",
    "TECHM.NS":"IT","MPHASIS.NS":"IT","COFORGE.NS":"IT","PERSISTENT.NS":"IT",
    "OFSS.NS":"IT","LTTS.NS":"IT","KPITTECH.NS":"IT","TATAELXSI.NS":"IT",
    "MASTEK.NS":"IT","HEXAWARE.NS":"IT","CYIENT.NS":"IT","BIRLASOFT.NS":"IT",
    # Pharma
    "SUNPHARMA.NS":"Pharma","DRREDDY.NS":"Pharma","CIPLA.NS":"Pharma",
    "DIVISLAB.NS":"Pharma","AUROPHARMA.NS":"Pharma","LUPIN.NS":"Pharma",
    "BIOCON.NS":"Pharma","ALKEM.NS":"Pharma","IPCALAB.NS":"Pharma",
    "TORNTPHARM.NS":"Pharma","GLENMARK.NS":"Pharma","NATCOPHARM.NS":"Pharma",
    "GRANULES.NS":"Pharma","LAURUSLABS.NS":"Pharma","AJANTPHARM.NS":"Pharma",
    # Energy
    "NTPC.NS":"Energy","POWERGRID.NS":"Energy","TATAPOWER.NS":"Energy",
    "NHPC.NS":"Energy","SJVN.NS":"Energy","CESC.NS":"Energy",
    "SUZLON.NS":"Energy","TORNTPOWER.NS":"Energy","ADANIGREEN.NS":"Energy",
    "ADANIPOWER.NS":"Energy","RPOWER.NS":"Energy","JPPOWER.NS":"Energy",
    "INDIGRID.NS":"Energy","GREENKO.NS":"Energy",
    # Oil & Gas
    "RELIANCE.NS":"Oil&Gas","ONGC.NS":"Oil&Gas","IOC.NS":"Oil&Gas",
    "BPCL.NS":"Oil&Gas","GAIL.NS":"Oil&Gas","OIL.NS":"Oil&Gas",
    "MRPL.NS":"Oil&Gas","PETRONET.NS":"Oil&Gas","HINDPETRO.NS":"Oil&Gas",
    "GUJGASLTD.NS":"Oil&Gas","MGL.NS":"Oil&Gas","IGL.NS":"Oil&Gas",
    # Metals
    "TATASTEEL.NS":"Metals","JSWSTEEL.NS":"Metals","SAIL.NS":"Metals",
    "HINDALCO.NS":"Metals","VEDL.NS":"Metals","NMDC.NS":"Metals",
    "NALCO.NS":"Metals","HINDZINC.NS":"Metals","JINDALSTEL.NS":"Metals",
    "MOIL.NS":"Metals","APLAPOLLO.NS":"Metals","RATNAMANI.NS":"Metals",
    "WELCORP.NS":"Metals","GRAVITA.NS":"Metals",
    # Infra
    "LT.NS":"Infra","RVNL.NS":"Infra","NBCC.NS":"Infra",
    "RAILTEL.NS":"Infra","BHEL.NS":"Infra","BEL.NS":"Infra",
    "HAL.NS":"Infra","IRCON.NS":"Infra","KEC.NS":"Infra",
    "KALPATPOWR.NS":"Infra","ADANIPORTS.NS":"Infra","CONCOR.NS":"Infra",
    "GPPL.NS":"Infra","PRAJ.NS":"Infra","GRINFRA.NS":"Infra",
    # Auto
    "MARUTI.NS":"Auto","TATAMOTORS.NS":"Auto","EICHERMOT.NS":"Auto",
    "HEROMOTOCO.NS":"Auto","BAJAJ-AUTO.NS":"Auto","MOTHERSON.NS":"Auto",
    "BALKRISIND.NS":"Auto","ASHOKLEY.NS":"Auto","TVSMOTOR.NS":"Auto",
    "BOSCHLTD.NS":"Auto","EXIDEIND.NS":"Auto","AMARARAJA.NS":"Auto",
    "SUNDRMFAST.NS":"Auto","CRAFTSMAN.NS":"Auto","TIINDIA.NS":"Auto",
    # FMCG
    "HINDUNILVR.NS":"FMCG","ITC.NS":"FMCG","NESTLEIND.NS":"FMCG",
    "BRITANNIA.NS":"FMCG","DABUR.NS":"FMCG","MARICO.NS":"FMCG",
    "GODREJCP.NS":"FMCG","TATACONSUM.NS":"FMCG","COLPAL.NS":"FMCG",
    "EMAMILTD.NS":"FMCG","VBL.NS":"FMCG","RADICO.NS":"FMCG",
    "UNITDSPR.NS":"FMCG","PGHH.NS":"FMCG",
    # New Age
    "ZOMATO.NS":"NewAge","IRCTC.NS":"NewAge","NYKAA.NS":"NewAge",
    "PAYTM.NS":"NewAge","DELHIVERY.NS":"NewAge","POLICYBZR.NS":"NewAge",
    "EASEMYTRIP.NS":"NewAge","CARTRADE.NS":"NewAge",
    # Telecom
    "BHARTIARTL.NS":"Telecom","IDEA.NS":"Telecom","TTML.NS":"Telecom",
    # Cement
    "ULTRACEMCO.NS":"Cement","SHREECEM.NS":"Cement","AMBUJACEM.NS":"Cement",
    "ACC.NS":"Cement","RAMCOCEM.NS":"Cement","JKCEMENT.NS":"Cement",
    "HEIDELBERG.NS":"Cement","BIRLACORPN.NS":"Cement",
    # Real Estate
    "DLF.NS":"RealEstate","GODREJPROP.NS":"RealEstate","OBEROIRLTY.NS":"RealEstate",
    "PHOENIXLTD.NS":"RealEstate","BRIGADE.NS":"RealEstate","PRESTIGE.NS":"RealEstate",
    "SOBHA.NS":"RealEstate","MAHLIFE.NS":"RealEstate",
    # Chemicals
    "PIDILITIND.NS":"Chemicals","ATUL.NS":"Chemicals","NAVINFLUOR.NS":"Chemicals",
    "CLEAN.NS":"Chemicals","FINEORG.NS":"Chemicals","SUDARSCHEM.NS":"Chemicals",
    "GALAXYSURF.NS":"Chemicals","FLUOROCHEM.NS":"Chemicals",
    # Insurance
    "SBILIFE.NS":"Insurance","HDFCLIFE.NS":"Insurance","ICICIPRULI.NS":"Insurance",
    "LICI.NS":"Insurance","GICRE.NS":"Insurance","NIACL.NS":"Insurance",
    # Consumer Durables
    "HAVELLS.NS":"ConsumerDurables","VOLTAS.NS":"ConsumerDurables",
    "BLUESTARCO.NS":"ConsumerDurables","CROMPTON.NS":"ConsumerDurables",
    "DIXON.NS":"ConsumerDurables","AMBER.NS":"ConsumerDurables",
    "ORIENTELEC.NS":"ConsumerDurables","WHIRLPOOL.NS":"ConsumerDurables",
    # Healthcare
    "APOLLOHOSP.NS":"Healthcare","FORTIS.NS":"Healthcare","MAXHEALTH.NS":"Healthcare",
    "METROPOLIS.NS":"Healthcare","LALPATHLAB.NS":"Healthcare","THYROCARE.NS":"Healthcare",
    # Defence
    "BEML.NS":"Defence","MAZDOCK.NS":"Defence","COCHINSHIP.NS":"Defence",
    "GRSE.NS":"Defence","PARAS.NS":"Defence",
}

etfs = {
    "NIFTYBEES.NS":"ETF-Nifty50","BANKBEES.NS":"ETF-Banking",
    "ITBEES.NS":"ETF-IT","PHARMABEES.NS":"ETF-Pharma",
    "PSUBNKBEES.NS":"ETF-PSUBank","GOLDBEES.NS":"ETF-Gold",
    "SILVERBEES.NS":"ETF-Silver","INFRABEES.NS":"ETF-Infra",
    "JUNIORBEES.NS":"ETF-Junior","CPSE.NS":"ETF-CPSE",
    "MOM50.NS":"ETF-Momentum","LOWVOLIETF.NS":"ETF-LowVol",
}

# ── NSE DELIVERY DATA ──
@st.cache_data(ttl=3600)
def get_nse_delivery(symbol):
    try:
        sym = symbol.replace(".NS", "")
        url = f"https://www.nseindia.com/api/quote-equity?symbol={sym}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com"
        }
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        r = session.get(url, headers=headers, timeout=5)
        data = r.json()
        delivery_pct = data.get("securityWiseDP", {}).get("deliveryToTradedQuantity", None)
        return float(delivery_pct) if delivery_pct else None
    except:
        return None

# ── ANALYZE ──
def analyze(symbol, sector):
    try:
        df = yf.download(symbol, period=PERIOD, interval="1d", auto_adjust=True, progress=False)
        if len(df) < 30:
            return None

        close = df['Close'][symbol]
        volume = df['Volume'][symbol]

        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()
        ema20 = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        ema50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()
        ema200 = ta.trend.EMAIndicator(close, window=200).ema_indicator() if len(df) > 200 else ema50
        macd = ta.trend.MACD(close)
        bb = ta.volatility.BollingerBands(close)
        stoch = ta.momentum.StochasticOscillator(df['High'][symbol], df['Low'][symbol], close)
        vol_avg = volume.rolling(20).mean()

        price = close.iloc[-1]
        if price > MAX_PRICE or price < 5:
            return None

        rsi_now = rsi.iloc[-1]
        ema20_now = ema20.iloc[-1]
        ema50_now = ema50.iloc[-1]
        ema200_now = ema200.iloc[-1]
        macd_now = macd.macd().iloc[-1]
        macd_sig = macd.macd_signal().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        stoch_now = stoch.stoch().iloc[-1]
        vol_now = volume.iloc[-1]
        vol_avg_now = vol_avg.iloc[-1]

        score = 0
        reasons = []

        if 30 < rsi_now < 62: score += 1; reasons.append(f"RSI {rsi_now:.0f}")
        if ema20_now > ema50_now: score += 1; reasons.append("Uptrend ✅")
        if macd_now > macd_sig: score += 1; reasons.append("MACD↑")
        if vol_now > vol_avg_now * 1.2: score += 1; reasons.append("Vol Spike 🔥")
        if close.iloc[-1] > close.iloc[-3]: score += 1; reasons.append("Momentum↑")
        if price <= bb_low * 1.03: score += 1; reasons.append("BB Bounce")
        if stoch_now < 40: score += 1; reasons.append("Stoch Oversold")

        # NSE Delivery bonus
        delivery = None
        if 'ETF' not in sector:
            delivery = get_nse_delivery(symbol)
            if delivery and delivery > 50:
                score += 1
                reasons.append(f"Delivery {delivery:.0f}% 💪")

        if score < MIN_SCORE:
            return None

        qty = int(capital / price)
        if qty == 0: return None

        return {
            'Symbol': symbol.replace('.NS',''),
            'Sector': sector,
            'Price': round(price, 1),
            'Score': score,
            'MaxScore': 8 if 'ETF' not in sector else 7,
            'RSI': round(rsi_now, 1),
            'Qty': qty,
            'Invest': round(qty * price),
            'SL': round(price * SL, 1),
            'T1': round(price * T1, 1),
            'T2': round(price * T2, 1),
            'Risk': round(qty * price * (1-SL)),
            'Reward': round(qty * price * (T2-1)),
            'RR': round((T2-1)/(1-SL), 1),
            'Delivery': f"{delivery:.0f}%" if delivery else "N/A",
            'Why': " | ".join(reasons),
            'Timeline': timeline
        }
    except:
        return None

# ── SCAN BUTTON ──
if st.button("🔍 Scan Karo", use_container_width=True, type="primary"):
    all_symbols = {**etfs, **nifty500}
    results = []

    progress = st.progress(0)
    status = st.empty()
    total = len(all_symbols)

    for i, (sym, sec) in enumerate(all_symbols.items()):
        status.text(f"⏳ Scanning {sym.replace('.NS','')}... ({i+1}/{total})")
        r = analyze(sym, sec)
        if r: results.append(r)
        progress.progress((i+1)/total)

    status.empty()
    progress.empty()

    results = sorted(results, key=lambda x: x['Score'], reverse=True)
    etf_r = [r for r in results if 'ETF' in r['Sector']]
    stk_r = [r for r in results if 'ETF' not in r['Sector']]

    # Summary
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stocks Scanned", total)
    c2.metric("Signals Found", len(results))
    c3.metric("ETF Signals", len(etf_r))
    c4.metric("Stock Signals", len(stk_r))
    st.markdown("---")

    # ETF Results
    if etf_r:
        st.markdown("## 🏦 ETF Signals — Safest Picks")
        for s in etf_r:
            with st.container(border=True):
                h1, h2 = st.columns([3,1])
                h1.markdown(f"### ✅ {s['Symbol']} `{s['Sector']}`")
                h2.markdown(f"<div class='score-high'>Score {s['Score']}/{s['MaxScore']}</div>", unsafe_allow_html=True)
                c1,c2,c3,c4,c5,c6 = st.columns(6)
                c1.metric("Price", f"₹{s['Price']}")
                c2.metric("RSI", s['RSI'])
                c3.metric("Qty", s['Qty'])
                c4.metric("Invest", f"₹{s['Invest']}")
                c5.metric("Stop Loss", f"₹{s['SL']}")
                c6.metric("Risk", f"₹{s['Risk']}")
                st.success(f"🎯 T1: ₹{s['T1']} | T2: ₹{s['T2']} | R:R = 1:{s['RR']} | Hold: {s['Timeline']}")
                st.caption(f"📊 Signals: {s['Why']}")
        st.markdown("---")

    # Stock Results
    if stk_r:
        st.markdown("## 📊 Stock Signals — Sector Wise")
        cur_sec = ""
        for s in stk_r:
            if s['Sector'] != cur_sec:
                cur_sec = s['Sector']
                st.markdown(f"### 📁 {cur_sec}")
            with st.container(border=True):
                h1, h2 = st.columns([3,1])
                h1.markdown(f"**✅ {s['Symbol']}**")
                h2.markdown(f"<div class='score-high'>Score {s['Score']}/{s['MaxScore']}</div>", unsafe_allow_html=True)
                c1,c2,c3,c4,c5,c6 = st.columns(6)
                c1.metric("Price", f"₹{s['Price']}")
                c2.metric("RSI", s['RSI'])
                c3.metric("Qty", s['Qty'])
                c4.metric("Invest", f"₹{s['Invest']}")
                c5.metric("Stop Loss", f"₹{s['SL']}")
                c6.metric("Risk", f"₹{s['Risk']}")
                st.success(f"🎯 T1: ₹{s['T1']} | T2: ₹{s['T2']} | R:R = 1:{s['RR']} | Delivery: {s['Delivery']} | Hold: {s['Timeline']}")
                st.caption(f"📊 Signals: {s['Why']}")

    if not results:
        st.warning("⏳ Aaj koi strong signal nahi. Kal try karo ya Signal Strength kam karo.")

    st.markdown("---")
    st.caption(f"📊 {total} symbols scanned | 💰 Capital ₹{capital} | ⏱️ {timeline} | 🎯 Min Score {MIN_SCORE}/8")
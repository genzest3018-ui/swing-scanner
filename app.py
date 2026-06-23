import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import warnings
import requests
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Swing Scanner Pro", page_icon="📈", layout="centered")

st.title("📈 Swing Trade Scanner Pro")
st.caption("NIFTY 500 + ETFs | News | Mutual Funds | Multi-Timeline")

# ── SIDEBAR ──
with st.sidebar:
    st.header("⚙️ Settings")
    capital = st.number_input("💰 Capital (₹)", min_value=5000, max_value=1000000, value=5000, step=1000)
    timeline = st.selectbox("📅 Trade Timeline", ["3 Days (Short)", "1 Week (Medium)", "2 Weeks (Swing)"])
    risk_level = st.selectbox("🛡️ Risk Level", ["Low (ETF only)", "Medium (Large Cap)", "High (Mid/Small Cap)"])
    st.markdown("---")
    st.caption("Made by Pulkit 🚀")

MAX_PRICE = capital * 0.45

# Timeline based settings
if "3 Days" in timeline:
    PERIOD = "1mo"
    SL_PCT = 0.97
    T1_PCT = 1.04
    T2_PCT = 1.07
    MIN_SCORE = 4
elif "1 Week" in timeline:
    PERIOD = "3mo"
    SL_PCT = 0.96
    T1_PCT = 1.06
    T2_PCT = 1.10
    MIN_SCORE = 4
else:
    PERIOD = "6mo"
    SL_PCT = 0.95
    T1_PCT = 1.08
    T2_PCT = 1.15
    MIN_SCORE = 3

# ── FULL NIFTY 500 ──
nifty500 = {
    # Banking
    "HDFCBANK.NS":"Banking","ICICIBANK.NS":"Banking","SBIN.NS":"Banking",
    "KOTAKBANK.NS":"Banking","AXISBANK.NS":"Banking","BANKBARODA.NS":"Banking",
    "CANBK.NS":"Banking","UNIONBANK.NS":"Banking","PNB.NS":"Banking",
    "IDFCFIRSTB.NS":"Banking","FEDERALBNK.NS":"Banking","INDUSINDBK.NS":"Banking",
    "RBLBANK.NS":"Banking","BANDHANBNK.NS":"Banking","KARURVYSYA.NS":"Banking",
    "DCBBANK.NS":"Banking","SOUTHBANK.NS":"Banking","CSBBANK.NS":"Banking",
    "UJJIVANSFB.NS":"Banking","EQUITASBNK.NS":"Banking",
    # NBFC
    "BAJFINANCE.NS":"NBFC","BAJAJFINSV.NS":"NBFC","CHOLAFIN.NS":"NBFC",
    "MUTHOOTFIN.NS":"NBFC","MANAPPURAM.NS":"NBFC","LICHSGFIN.NS":"NBFC",
    "PNBHOUSING.NS":"NBFC","IRFC.NS":"NBFC","RECLTD.NS":"NBFC",
    "PFC.NS":"NBFC","HUDCO.NS":"NBFC","IIFL.NS":"NBFC",
    "MFSL.NS":"NBFC","CANFINHOME.NS":"NBFC","HOMEFIRST.NS":"NBFC",
    # IT
    "TCS.NS":"IT","INFY.NS":"IT","WIPRO.NS":"IT","HCLTECH.NS":"IT",
    "TECHM.NS":"IT","MPHASIS.NS":"IT","COFORGE.NS":"IT","PERSISTENT.NS":"IT",
    "OFSS.NS":"IT","LTTS.NS":"IT","HEXAWARE.NS":"IT","KPITTECH.NS":"IT",
    "TATAELXSI.NS":"IT","MASTEK.NS":"IT","NIITLTD.NS":"IT",
    # Pharma
    "SUNPHARMA.NS":"Pharma","DRREDDY.NS":"Pharma","CIPLA.NS":"Pharma",
    "DIVISLAB.NS":"Pharma","AUROPHARMA.NS":"Pharma","LUPIN.NS":"Pharma",
    "BIOCON.NS":"Pharma","ALKEM.NS":"Pharma","IPCALAB.NS":"Pharma",
    "TORNTPHARM.NS":"Pharma","GLENMARK.NS":"Pharma","NATCOPHARM.NS":"Pharma",
    "GRANULES.NS":"Pharma","LAURUSLABS.NS":"Pharma","SEQUENT.NS":"Pharma",
    # Energy
    "NTPC.NS":"Energy","POWERGRID.NS":"Energy","TATAPOWER.NS":"Energy",
    "NHPC.NS":"Energy","SJVN.NS":"Energy","CESC.NS":"Energy",
    "SUZLON.NS":"Energy","TORNTPOWER.NS":"Energy","ADANIGREEN.NS":"Energy",
    "ADANIPOWER.NS":"Energy","RPOWER.NS":"Energy","JPPOWER.NS":"Energy",
    "INDIGRID.NS":"Energy","ACME.NS":"Energy",
    # Oil & Gas
    "RELIANCE.NS":"Oil&Gas","ONGC.NS":"Oil&Gas","IOC.NS":"Oil&Gas",
    "BPCL.NS":"Oil&Gas","GAIL.NS":"Oil&Gas","OIL.NS":"Oil&Gas",
    "MRPL.NS":"Oil&Gas","PETRONET.NS":"Oil&Gas","HINDPETRO.NS":"Oil&Gas",
    "GUJGASLTD.NS":"Oil&Gas","MGL.NS":"Oil&Gas","IGL.NS":"Oil&Gas",
    # Metals
    "TATASTEEL.NS":"Metals","JSWSTEEL.NS":"Metals","SAIL.NS":"Metals",
    "HINDALCO.NS":"Metals","VEDL.NS":"Metals","NMDC.NS":"Metals",
    "NALCO.NS":"Metals","HINDZINC.NS":"Metals","JINDALSTEL.NS":"Metals",
    "MOIL.NS":"Metals","RATNAMANI.NS":"Metals","WELCORP.NS":"Metals",
    "APL.NS":"Metals","APLAPOLLO.NS":"Metals",
    # Infra
    "LT.NS":"Infra","RVNL.NS":"Infra","NBCC.NS":"Infra",
    "RAILTEL.NS":"Infra","BHEL.NS":"Infra","BEL.NS":"Infra",
    "HAL.NS":"Infra","IRCON.NS":"Infra","KEC.NS":"Infra",
    "KALPATPOWR.NS":"Infra","PRAJ.NS":"Infra","GRINFRA.NS":"Infra",
    "GPPL.NS":"Infra","ADANIPORTS.NS":"Infra","CONCOR.NS":"Infra",
    # Auto
    "MARUTI.NS":"Auto","TATAMOTORS.NS":"Auto","EICHERMOT.NS":"Auto",
    "HEROMOTOCO.NS":"Auto","BAJAJ-AUTO.NS":"Auto","MOTHERSON.NS":"Auto",
    "BALKRISIND.NS":"Auto","ASHOKLEY.NS":"Auto","TVSMOTOR.NS":"Auto",
    "BOSCHLTD.NS":"Auto","EXIDEIND.NS":"Auto","AMARARAJA.NS":"Auto",
    "SUNDRMFAST.NS":"Auto","MINDAIND.NS":"Auto","CRAFTSMAN.NS":"Auto",
    # FMCG
    "HINDUNILVR.NS":"FMCG","ITC.NS":"FMCG","NESTLEIND.NS":"FMCG",
    "BRITANNIA.NS":"FMCG","DABUR.NS":"FMCG","MARICO.NS":"FMCG",
    "GODREJCP.NS":"FMCG","TATACONSUM.NS":"FMCG","COLPAL.NS":"FMCG",
    "EMAMILTD.NS":"FMCG","BAJAJCON.NS":"FMCG","PGHH.NS":"FMCG",
    "RADICO.NS":"FMCG","VBL.NS":"FMCG","UNITDSPR.NS":"FMCG",
    # New Age
    "ZOMATO.NS":"NewAge","IRCTC.NS":"NewAge","NYKAA.NS":"NewAge",
    "PAYTM.NS":"NewAge","DELHIVERY.NS":"NewAge","CARTRADE.NS":"NewAge",
    "POLICYBZR.NS":"NewAge","EASEMYTRIP.NS":"NewAge",
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
    "FLUOROCHEM.NS":"Chemicals","CLEAN.NS":"Chemicals","FINEORG.NS":"Chemicals",
    "SUDARSCHEM.NS":"Chemicals","GALAXYSURF.NS":"Chemicals",
    # Insurance
    "SBILIFE.NS":"Insurance","HDFCLIFE.NS":"Insurance","ICICIPRULI.NS":"Insurance",
    "LICI.NS":"Insurance","GICRE.NS":"Insurance","NIACL.NS":"Insurance",
    # Consumer Durables
    "HAVELLS.NS":"ConsumerDurables","VOLTAS.NS":"ConsumerDurables",
    "BLUESTARCO.NS":"ConsumerDurables","WHIRLPOOL.NS":"ConsumerDurables",
    "CROMPTON.NS":"ConsumerDurables","ORIENTELEC.NS":"ConsumerDurables",
    "DIXON.NS":"ConsumerDurables","AMBER.NS":"ConsumerDurables",
    # Healthcare
    "APOLLOHOSP.NS":"Healthcare","FORTIS.NS":"Healthcare","MAXHEALTH.NS":"Healthcare",
    "METROPOLIS.NS":"Healthcare","LALPATHLAB.NS":"Healthcare","THYROCARE.NS":"Healthcare",
    # Defence
    "HAL.NS":"Defence","BEL.NS":"Defence","BEML.NS":"Defence",
    "MAZDOCK.NS":"Defence","COCHINSHIP.NS":"Defence","GRSE.NS":"Defence",
}

etfs = {
    "NIFTYBEES.NS":"ETF-Nifty50","BANKBEES.NS":"ETF-Banking",
    "ITBEES.NS":"ETF-IT","PHARMABEES.NS":"ETF-Pharma",
    "PSUBNKBEES.NS":"ETF-PSUBank","GOLDBEES.NS":"ETF-Gold",
    "SILVERBEES.NS":"ETF-Silver","INFRABEES.NS":"ETF-Infra",
    "CPSE.NS":"ETF-CPSE","JUNIORBEES.NS":"ETF-Junior",
    "SETFNIF50.NS":"ETF-Nifty50","MOM50.NS":"ETF-Momentum",
    "LOWVOLIETF.NS":"ETF-LowVol","QUAL30IETF.NS":"ETF-Quality",
}

# Risk filter
def risk_filter(sector):
    if risk_level == "Low (ETF only)":
        return "ETF" in sector
    elif risk_level == "Medium (Large Cap)":
        return sector in ["Banking","IT","FMCG","Pharma","Oil&Gas","Energy","ETF-Nifty50","ETF-Banking","ETF-IT","ETF-Pharma"]
    else:
        return True

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
        macd_now = macd.macd().iloc[-1]
        macd_sig = macd.macd_signal().iloc[-1]
        bb_low = bb.bollinger_lband().iloc[-1]
        stoch_now = stoch.stoch().iloc[-1]
        vol_now = volume.iloc[-1]
        vol_avg_now = vol_avg.iloc[-1]

        score = 0
        reasons = []

        if 30 < rsi_now < 60: score += 1; reasons.append(f"RSI {rsi_now:.0f}")
        if ema20_now > ema50_now: score += 1; reasons.append("Uptrend✅")
        if macd_now > macd_sig: score += 1; reasons.append("MACD↑")
        if vol_now > vol_avg_now * 1.2: score += 1; reasons.append("Vol Spike🔥")
        if close.iloc[-1] > close.iloc[-3]: score += 1; reasons.append("Momentum↑")
        if price <= bb_low * 1.03: score += 1; reasons.append("BB Bounce")
        if stoch_now < 40: score += 1; reasons.append("Stoch Oversold")

        if score < MIN_SCORE:
            return None

        qty = int(capital / price)
        if qty == 0: return None

        return {
            'Symbol': symbol.replace('.NS',''),
            'Sector': sector,
            'Price': round(price, 1),
            'Score': f"{score}/7",
            'ScoreNum': score,
            'RSI': round(rsi_now, 1),
            'Qty': qty,
            'Invest': round(qty * price),
            'SL': round(price * SL_PCT, 1),
            'T1': round(price * T1_PCT, 1),
            'T2': round(price * T2_PCT, 1),
            'Risk': round(qty * price * (1-SL_PCT)),
            'Why': " | ".join(reasons),
            'Timeline': timeline
        }
    except:
        return None

# ── NEWS SENTIMENT ──
def get_news_sentiment():
    sector_news = {
        "Banking": {"sentiment": "🟢 Positive", "reason": "RBI rate pause expected, credit growth strong"},
        "IT": {"sentiment": "🟡 Neutral", "reason": "US slowdown concerns, but rupee depreciation helps"},
        "Pharma": {"sentiment": "🟢 Positive", "reason": "US FDA approvals picking up, domestic demand strong"},
        "Energy": {"sentiment": "🟢 Positive", "reason": "Govt capex push, renewable energy targets"},
        "Oil&Gas": {"sentiment": "🔴 Cautious", "reason": "Crude oil volatile, subsidy concerns"},
        "Metals": {"sentiment": "🟡 Neutral", "reason": "China demand uncertain, domestic infra spending helps"},
        "FMCG": {"sentiment": "🟢 Positive", "reason": "Rural recovery, monsoon positive"},
        "Auto": {"sentiment": "🟢 Positive", "reason": "EV push, strong festive season pipeline"},
        "Infra": {"sentiment": "🟢 Positive", "reason": "Govt infra spending at all time high"},
        "RealEstate": {"sentiment": "🟡 Neutral", "reason": "High rates pressure, but demand stable"},
        "NewAge": {"sentiment": "🔴 Cautious", "reason": "Profitability concerns, high valuations"},
        "Chemicals": {"sentiment": "🟡 Neutral", "reason": "China+1 theme intact but margins under pressure"},
        "Defence": {"sentiment": "🟢 Positive", "reason": "Record defence orders, Make in India push"},
    }
    return sector_news

# ── MUTUAL FUNDS ──
def get_mf_recommendations(risk, cap):
    monthly = int(cap * 0.2)
    if risk == "Low (ETF only)":
        return [
            {"name": "Nifty 50 Index Fund", "type": "Index", "return": "12% avg", "risk": "Low", "monthly": monthly, "why": "Market se saath chalo, steady growth"},
            {"name": "HDFC Balanced Advantage", "type": "Hybrid", "return": "11% avg", "risk": "Low-Med", "monthly": monthly, "why": "Auto rebalancing, less volatility"},
            {"name": "SBI Arbitrage Fund", "type": "Arbitrage", "return": "7-8% avg", "risk": "Very Low", "monthly": monthly, "why": "FD se better, almost zero risk"},
        ]
    elif risk == "Medium (Large Cap)":
        return [
            {"name": "Mirae Asset Large Cap", "type": "Large Cap", "return": "14% avg", "risk": "Medium", "monthly": monthly, "why": "Top 100 companies, solid track record"},
            {"name": "Parag Parikh Flexi Cap", "type": "Flexi Cap", "return": "16% avg", "risk": "Medium", "monthly": monthly, "why": "International + India, best diversification"},
            {"name": "Axis Bluechip Fund", "type": "Large Cap", "return": "13% avg", "risk": "Medium", "monthly": monthly, "why": "Quality stocks, low churn"},
            {"name": "Nifty Next 50 Index", "type": "Index", "return": "15% avg", "risk": "Med-High", "monthly": monthly, "why": "Future large caps at mid cap price"},
        ]
    else:
        return [
            {"name": "Quant Small Cap Fund", "type": "Small Cap", "return": "22% avg", "risk": "High", "monthly": monthly, "why": "High risk high reward, 5yr+ horizon"},
            {"name": "Nippon India Small Cap", "type": "Small Cap", "return": "20% avg", "risk": "High", "monthly": monthly, "why": "Largest small cap AUM, diversified"},
            {"name": "HDFC Mid Cap Opportunities", "type": "Mid Cap", "return": "18% avg", "risk": "Med-High", "monthly": monthly, "why": "Consistent performer, 15yr track record"},
            {"name": "Motilal Oswal Midcap", "type": "Mid Cap", "return": "19% avg", "risk": "Med-High", "monthly": monthly, "why": "Concentrated bets, high conviction"},
        ]

# ── TABS ──
tab1, tab2, tab3 = st.tabs(["📊 Stock Scanner", "📰 News & Sentiment", "💼 Mutual Funds"])

with tab1:
    st.info(f"Timeline: **{timeline}** | Risk: **{risk_level}** | Capital: **₹{capital}**")

    if st.button("🔍 Scan Karo", use_container_width=True):
        results = []
        all_symbols = {**etfs, **nifty500}
        filtered = {k: v for k, v in all_symbols.items() if risk_filter(v)}

        progress = st.progress(0)
        status = st.empty()
        total = len(filtered)

        for i, (sym, sec) in enumerate(filtered.items()):
            status.text(f"Scanning {sym.replace('.NS','')}... ({i+1}/{total})")
            r = analyze(sym, sec)
            if r: results.append(r)
            progress.progress((i+1)/total)

        status.text("✅ Scan complete!")
        results = sorted(results, key=lambda x: x['ScoreNum'], reverse=True)

        etf_r = [r for r in results if 'ETF' in r['Sector']]
        stk_r = [r for r in results if 'ETF' not in r['Sector']]

        if etf_r:
            st.markdown("### 🏦 ETF Signals — Safest")
            for s in etf_r:
                with st.container(border=True):
                    st.markdown(f"**✅ {s['Symbol']}** `{s['Sector']}` — Score **{s['Score']}**")
                    c1,c2,c3 = st.columns(3)
                    c1.metric("Price", f"₹{s['Price']}")
                    c2.metric("RSI", s['RSI'])
                    c3.metric("Qty", s['Qty'])
                    c1.metric("Invest", f"₹{s['Invest']}")
                    c2.metric("Stop Loss", f"₹{s['SL']}")
                    c3.metric("Risk", f"₹{s['Risk']}")
                    st.success(f"🎯 T1: ₹{s['T1']} | T2: ₹{s['T2']} | Hold: {s['Timeline']}")
                    st.caption(f"Why: {s['Why']}")

        if stk_r:
            st.markdown("### 📊 Stock Signals")
            cur_sec = ""
            for s in stk_r:
                if s['Sector'] != cur_sec:
                    cur_sec = s['Sector']
                    st.markdown(f"#### 📁 {cur_sec}")
                with st.container(border=True):
                    st.markdown(f"**✅ {s['Symbol']}** — Score **{s['Score']}**")
                    c1,c2,c3 = st.columns(3)
                    c1.metric("Price", f"₹{s['Price']}")
                    c2.metric("RSI", s['RSI'])
                    c3.metric("Qty", s['Qty'])
                    c1.metric("Invest", f"₹{s['Invest']}")
                    c2.metric("Stop Loss", f"₹{s['SL']}")
                    c3.metric("Risk", f"₹{s['Risk']}")
                    st.success(f"🎯 T1: ₹{s['T1']} | T2: ₹{s['T2']} | Hold: {s['Timeline']}")
                    st.caption(f"Why: {s['Why']}")

        if not results:
            st.warning("⏳ No signals today. Market wait karo.")

        st.caption(f"Scanned {total} symbols | ₹{capital} capital | {timeline}")

with tab2:
    st.markdown("### 📰 Sector News & Sentiment")
    st.caption("Market mood samjho — phir trade karo")
    news = get_news_sentiment()
    for sector, data in news.items():
        with st.container(border=True):
            st.markdown(f"**{sector}** — {data['sentiment']}")
            st.caption(data['reason'])

with tab3:
    st.markdown("### 💼 Mutual Fund Recommendations")
    st.caption(f"Risk Level: {risk_level} | Suggested Monthly SIP: ₹{int(capital*0.2)}")
    mfs = get_mf_recommendations(risk_level, capital)
    for mf in mfs:
        with st.container(border=True):
            c1, c2 = st.columns([3,1])
            c1.markdown(f"**{mf['name']}**")
            c1.caption(mf['why'])
            c2.metric("Avg Return", mf['return'])
            c2.caption(f"Risk: {mf['risk']}")
            st.info(f"💰 Monthly SIP: ₹{mf['monthly']} | Type: {mf['type']}")
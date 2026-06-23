import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Swing Scanner", page_icon="📈", layout="wide")

st.markdown("""
<style>
.main { background-color: #0e1117; }
.conf-high  { color: #00d4aa; font-weight: bold; font-size: 22px; }
.conf-med   { color: #ffd700; font-weight: bold; font-size: 22px; }
.conf-low   { color: #ff8c00; font-weight: bold; font-size: 22px; }
.trend-bull { color: #00d4aa; font-weight: bold; }
.trend-bear { color: #ff4b4b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📈 Swing Trade Scanner")
st.markdown("##### Nifty 200 + ETFs | Yahoo Finance | v4.0")
st.markdown("---")

# ── INPUTS ──
col1, col2 = st.columns(2)
with col1:
    capital = st.number_input("💰 Capital (₹)", min_value=5000, max_value=500000,
                               value=10000, step=1000)
with col2:
    min_score = st.selectbox("🎯 Min Trade Quality", ["Strong (5+/8)", "Medium (4+/8)", "All (3+/8)"])

POSITION_SIZE    = capital * 0.30       # max 30% capital per trade
MAX_PRICE        = POSITION_SIZE        # price ceiling = position size
MIN_SCORE        = int(min_score.split("(")[1].split("+")[0])
MIN_AVG_TURNOVER = 5_00_00_000          # ₹5 crore daily avg turnover (liquidity filter)

# ── AUTO HOLD PERIOD (score-based) ──
def get_hold_params(score):
    if score >= 7:
        return "15–20 days", 0.93, 1.09, 1.16
    elif score >= 5:
        return "10–15 days", 0.95, 1.07, 1.12
    else:
        return "5–10 days",  0.97, 1.04, 1.07

# ── UNIVERSE ──
UNIVERSE = {
    "HDFCBANK.NS":"Banking",   "ICICIBANK.NS":"Banking",  "SBIN.NS":"Banking",
    "KOTAKBANK.NS":"Banking",  "AXISBANK.NS":"Banking",   "BANKBARODA.NS":"Banking",
    "INDUSINDBK.NS":"Banking", "FEDERALBNK.NS":"Banking", "IDFCFIRSTB.NS":"Banking",
    "BANDHANBNK.NS":"Banking",
    "BAJFINANCE.NS":"NBFC",    "BAJAJFINSV.NS":"NBFC",   "CHOLAFIN.NS":"NBFC",
    "MUTHOOTFIN.NS":"NBFC",    "LICHSGFIN.NS":"NBFC",    "IRFC.NS":"NBFC",
    "RECLTD.NS":"NBFC",        "PFC.NS":"NBFC",
    "TCS.NS":"IT",       "INFY.NS":"IT",      "WIPRO.NS":"IT",      "HCLTECH.NS":"IT",
    "TECHM.NS":"IT",     "MPHASIS.NS":"IT",   "COFORGE.NS":"IT",    "PERSISTENT.NS":"IT",
    "LTTS.NS":"IT",      "KPITTECH.NS":"IT",  "TATAELXSI.NS":"IT",
    "SUNPHARMA.NS":"Pharma",   "DRREDDY.NS":"Pharma",    "CIPLA.NS":"Pharma",
    "DIVISLAB.NS":"Pharma",    "AUROPHARMA.NS":"Pharma", "LUPIN.NS":"Pharma",
    "TORNTPHARM.NS":"Pharma",  "ALKEM.NS":"Pharma",
    "NTPC.NS":"Energy",        "POWERGRID.NS":"Energy",  "TATAPOWER.NS":"Energy",
    "NHPC.NS":"Energy",        "SUZLON.NS":"Energy",     "ADANIGREEN.NS":"Energy",
    "ADANIPOWER.NS":"Energy",
    "RELIANCE.NS":"Oil&Gas",   "ONGC.NS":"Oil&Gas",      "IOC.NS":"Oil&Gas",
    "BPCL.NS":"Oil&Gas",       "GAIL.NS":"Oil&Gas",      "IGL.NS":"Oil&Gas",
    "MGL.NS":"Oil&Gas",
    "TATASTEEL.NS":"Metals",   "JSWSTEEL.NS":"Metals",   "HINDALCO.NS":"Metals",
    "VEDL.NS":"Metals",        "SAIL.NS":"Metals",       "NMDC.NS":"Metals",
    "HINDZINC.NS":"Metals",    "JINDALSTEL.NS":"Metals",
    "LT.NS":"Infra",     "RVNL.NS":"Infra",    "BEL.NS":"Infra",
    "HAL.NS":"Infra",    "BHEL.NS":"Infra",    "ADANIPORTS.NS":"Infra",
    "MARUTI.NS":"Auto",        "TATAMOTORS.NS":"Auto",   "EICHERMOT.NS":"Auto",
    "BAJAJ-AUTO.NS":"Auto",    "HEROMOTOCO.NS":"Auto",   "TVSMOTOR.NS":"Auto",
    "MOTHERSON.NS":"Auto",     "BALKRISIND.NS":"Auto",
    "HINDUNILVR.NS":"FMCG",   "ITC.NS":"FMCG",          "NESTLEIND.NS":"FMCG",
    "BRITANNIA.NS":"FMCG",    "DABUR.NS":"FMCG",        "MARICO.NS":"FMCG",
    "TATACONSUM.NS":"FMCG",   "COLPAL.NS":"FMCG",       "VBL.NS":"FMCG",
    "ULTRACEMCO.NS":"Cement",  "SHREECEM.NS":"Cement",   "AMBUJACEM.NS":"Cement",
    "ACC.NS":"Cement",
    "DLF.NS":"RealEstate",     "GODREJPROP.NS":"RealEstate", "OBEROIRLTY.NS":"RealEstate",
    "PHOENIXLTD.NS":"RealEstate",
    "PIDILITIND.NS":"Chemicals", "ATUL.NS":"Chemicals",
    "APOLLOHOSP.NS":"Healthcare", "FORTIS.NS":"Healthcare",
    "MAXHEALTH.NS":"Healthcare",  "LALPATHLAB.NS":"Healthcare",
    "SBILIFE.NS":"Insurance",  "HDFCLIFE.NS":"Insurance", "ICICIPRULI.NS":"Insurance",
    "HAVELLS.NS":"ConsumerDurables", "VOLTAS.NS":"ConsumerDurables",
    "DIXON.NS":"ConsumerDurables",
    "ZOMATO.NS":"NewAge",      "IRCTC.NS":"NewAge",
    "BHARTIARTL.NS":"Telecom",
}

# ETFs grouped by type for separate ranking
ETFS = {
    "NIFTYBEES.NS":"ETF-Equity",   "JUNIORBEES.NS":"ETF-Equity",
    "MOM50.NS":"ETF-Equity",       "INFRABEES.NS":"ETF-Equity",
    "BANKBEES.NS":"ETF-Sector",    "ITBEES.NS":"ETF-Sector",
    "PHARMABEES.NS":"ETF-Sector",  "PSUBNKBEES.NS":"ETF-Sector",
    "GOLDBEES.NS":"ETF-Commodity", "SILVERBEES.NS":"ETF-Commodity",
}

# ── NIFTY CONTEXT ──
@st.cache_data(ttl=3600)
def get_nifty_context():
    """
    Bull = EMA50 > EMA200 AND price > EMA50 (stronger condition than v3).
    Returns (trend, 1m_return).
    """
    try:
        df    = yf.download("^NSEI", period="12mo", interval="1d",
                             auto_adjust=True, progress=False)
        close = df['Close'].squeeze()
        ema50  = ta.trend.EMAIndicator(close, window=50).ema_indicator()
        ema200 = ta.trend.EMAIndicator(close, window=200).ema_indicator()

        price_now  = float(close.iloc[-1])
        ema50_now  = float(ema50.iloc[-1])
        ema200_now = float(ema200.iloc[-1])

        # Both conditions must pass
        is_bull = (ema50_now > ema200_now) and (price_now > ema50_now)
        trend   = "BULL" if is_bull else "BEAR"
        ret1m   = (price_now / float(close.iloc[-22]) - 1) * 100
        return trend, ret1m
    except:
        return "UNKNOWN", 0.0

# ── CORE ANALYSIS ──
def analyze(symbol, sector, nifty_ret_1m):
    try:
        df = yf.download(symbol, period="12mo", interval="1d",
                         auto_adjust=True, progress=False)
        if len(df) < 60:
            return None

        close  = df['Close'].squeeze()
        volume = df['Volume'].squeeze()
        high   = df['High'].squeeze()
        low    = df['Low'].squeeze()

        if close.isnull().all() or len(close.dropna()) < 55:
            return None

        price = float(close.iloc[-1])
        if price > MAX_PRICE or price < 5:
            return None

        # ── LIQUIDITY FILTER: ₹5Cr daily avg turnover ──
        turnover_avg = float((close * volume).rolling(20).mean().iloc[-1])
        if turnover_avg < MIN_AVG_TURNOVER:
            return None

        # ── INDICATORS ──
        rsi    = ta.momentum.RSIIndicator(close, window=14).rsi()
        ema20  = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        ema50  = ta.trend.EMAIndicator(close, window=50).ema_indicator()
        macd_i = ta.trend.MACD(close)
        atr_i  = ta.volatility.AverageTrueRange(high, low, close, window=14)
        vol_avg = volume.rolling(20).mean()

        rsi_now    = float(rsi.iloc[-1])
        ema20_now  = float(ema20.iloc[-1])
        ema50_now  = float(ema50.iloc[-1])
        macd_line  = float(macd_i.macd().iloc[-1])
        macd_sig   = float(macd_i.macd_signal().iloc[-1])
        macd_prev  = float(macd_i.macd().iloc[-2])
        macd_sprev = float(macd_i.macd_signal().iloc[-2])
        atr_now    = float(atr_i.average_true_range().iloc[-1])
        vol_now    = float(volume.iloc[-1])
        vol_avg_n  = float(vol_avg.iloc[-1])

        # ── BREAKOUT LEVELS (fixed logic) ──
        # 50D high is always >= 20D high, so check 50D first
        high50 = float(close.tail(51).iloc[:-1].max())
        high20 = float(close.tail(21).iloc[:-1].max())

        # ── RELATIVE STRENGTH ──
        stock_ret_1m = (float(close.iloc[-1]) / float(close.iloc[-22]) - 1) * 100
        rs_vs_nifty  = stock_ret_1m - nifty_ret_1m

        # ══ SCORING (max 8) ══
        score   = 0
        reasons = []

        # 1. RSI healthy zone
        if 32 < rsi_now < 62:
            score += 1
            reasons.append(f"RSI {rsi_now:.0f}")

        # 2. Uptrend
        if ema20_now > ema50_now:
            score += 1
            reasons.append("Uptrend ✅")

        # 3. MACD
        macd_fresh = (macd_prev < macd_sprev) and (macd_line > macd_sig)
        if macd_fresh:
            score += 2
            reasons.append("MACD Cross 🔥")
        elif macd_line > macd_sig:
            score += 1
            reasons.append("MACD Bullish")

        # 4. Volume spike
        if vol_avg_n > 0 and vol_now > vol_avg_n * 1.25:
            score += 1
            reasons.append(f"Vol {vol_now/vol_avg_n:.1f}x 🔥")

        # 5+6. Breakout — 50D first (bigger), then 20D (smaller)
        #   50D breakout: 2 pts (strongest, major resistance break)
        #   20D breakout: 1 pt (moderate momentum)
        #   This way both can fire independently (no elif)
        if price >= high50 * 0.99:
            score += 2
            reasons.append("50D Breakout 🚀")
        elif price >= high20 * 0.99:
            score += 1
            reasons.append("20D Breakout 📈")

        # 7. Relative Strength vs Nifty
        if rs_vs_nifty > 2:
            score += 1
            reasons.append(f"RS +{rs_vs_nifty:.1f}% 💪")

        score = min(score, 8)

        if score < MIN_SCORE:
            return None

        # ── ATR-BASED STOP LOSS (replaces fixed %) ──
        sl_price = round(price - (1.5 * atr_now), 1)
        sl_price = max(sl_price, price * 0.88)   # floor at -12% for safety

        # Targets: ATR-based too (cleaner risk management)
        t1_price = round(price + (2.0 * atr_now), 1)
        t2_price = round(price + (3.5 * atr_now), 1)
        rr_ratio = round((t2_price - price) / (price - sl_price), 1) if price > sl_price else 0

        hold_label, _, _, _ = get_hold_params(score)  # still use for hold label

        qty = int(POSITION_SIZE / price)
        if qty == 0:
            return None

        invest    = round(qty * price)
        risk_amt  = round(qty * (price - sl_price))
        reward_amt = round(qty * (t2_price - price))
        quality   = round(score / 8 * 100)

        return {
            'Symbol':  symbol.replace('.NS', ''),
            'Sector':  sector,
            'Price':   round(price, 1),
            'Score':   score,
            'Quality': quality,
            'RSI':     round(rsi_now, 1),
            'ATR':     round(atr_now, 1),
            'RS':      round(rs_vs_nifty, 1),
            'Qty':     qty,
            'Invest':  invest,
            'SL':      sl_price,
            'T1':      t1_price,
            'T2':      t2_price,
            'Risk':    risk_amt,
            'Reward':  reward_amt,
            'RR':      rr_ratio,
            'Hold':    hold_label,
            'Why':     " | ".join(reasons),
            'IsETF':   'ETF' in sector,
        }
    except Exception:
        return None

# ── RENDER CARD ──
def render_card(s, rank=None):
    with st.container(border=True):
        h1, h2 = st.columns([3, 1])

        label = f"**#{rank}  {s['Symbol']}**" if rank else f"### {s['Symbol']}"
        h1.markdown(f"{label} `{s['Sector']}`")

        q = s['Quality']
        cls = "conf-high" if q >= 75 else ("conf-med" if q >= 55 else "conf-low")
        h2.markdown(
            f"<div class='{cls}'>{q}%</div>"
            f"<div style='color:#888;font-size:11px'>Trade Quality</div>",
            unsafe_allow_html=True
        )

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Price",       f"₹{s['Price']}")
        c2.metric("RSI",         s['RSI'])
        c3.metric("RS vs Nifty", f"{s['RS']:+.1f}%")
        c4.metric("Invest",      f"₹{s['Invest']}")
        c5.metric("ATR SL",      f"₹{s['SL']}")
        c6.metric("Risk",        f"₹{s['Risk']}")

        st.success(
            f"🎯 T1: ₹{s['T1']} | T2: ₹{s['T2']} | "
            f"R:R = 1:{s['RR']} | ⏳ Hold: {s['Hold']}"
        )
        st.caption(f"📊 {s['Why']}")

# ══════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════
if st.button("🔍 Scan Karo", use_container_width=True, type="primary"):

    with st.spinner("📡 Nifty context check kar raha hoon..."):
        nifty_trend, nifty_ret_1m = get_nifty_context()

    if nifty_trend == "BULL":
        st.markdown(
            "<span class='trend-bull'>🟢 BULL — EMA50 > EMA200 & Price > EMA50. Full scan ON.</span>",
            unsafe_allow_html=True)
    elif nifty_trend == "BEAR":
        st.markdown(
            "<span class='trend-bear'>🔴 BEAR — EMA50 below EMA200 or Price below EMA50. Sirf 6+ quality stocks.</span>",
            unsafe_allow_html=True)
    else:
        st.markdown("⚠️ Nifty data unavailable. Bina trend filter ke chal raha hai.")

    st.markdown("---")

    all_symbols = {**ETFS, **UNIVERSE}
    results, total = [], len(all_symbols)
    progress = st.progress(0)
    status   = st.empty()

    for i, (sym, sec) in enumerate(all_symbols.items()):
        status.text(f"⏳ {sym.replace('.NS','')} ... ({i+1}/{total})")
        r = analyze(sym, sec, nifty_ret_1m)
        if r:
            if nifty_trend == "BEAR" and not r['IsETF'] and r['Score'] < 6:
                pass
            else:
                results.append(r)
        progress.progress((i + 1) / total)

    status.empty()
    progress.empty()

    results = sorted(results, key=lambda x: x['Score'], reverse=True)
    etf_r   = [r for r in results if r['IsETF']]
    stk_r   = [r for r in results if not r['IsETF']][:10]

    # ── SUMMARY ──
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Scanned",       total)
    c2.metric("ETF Signals",   len(etf_r))
    c3.metric("Stock Picks",   len(stk_r))
    c4.metric("Capital/Trade", f"₹{int(POSITION_SIZE):,}")
    c5.metric("Market",        nifty_trend)
    st.markdown("---")

    # ── ETF RESULTS — grouped by category ──
    if etf_r:
        st.markdown("## 🏦 ETF Signals")
        for cat in ["ETF-Equity", "ETF-Sector", "ETF-Commodity"]:
            cat_etfs = [e for e in etf_r if e['Sector'] == cat]
            if cat_etfs:
                label = {"ETF-Equity":"📊 Broad Market", "ETF-Sector":"🏭 Sector",
                         "ETF-Commodity":"🪙 Commodity"}[cat]
                st.markdown(f"**{label}**")
                for s in cat_etfs:
                    render_card(s)
        st.markdown("---")

    # ── STOCK RESULTS ──
    if stk_r:
        st.markdown(f"## 📈 Top {len(stk_r)} Stock Opportunities")
        st.caption("Sorted by Trade Quality. ATR-based SL — volatile stocks get wider stops automatically.")
        for rank, s in enumerate(stk_r, 1):
            render_card(s, rank=rank)

    if not results:
        st.warning("⏳ Koi signal nahi mila. Min Trade Quality kam karo ya kal try karo.")

    st.markdown("---")
    st.caption(
        f"📊 {total} symbols | 💰 ₹{capital} capital | "
        f"📐 ₹{int(POSITION_SIZE):,}/trade | 🎯 Min {MIN_SCORE}/8 | "
        f"🔍 Liquidity ≥ ₹5Cr/day | 📈 Nifty: {nifty_trend}"
    )

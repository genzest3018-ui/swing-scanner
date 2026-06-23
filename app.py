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
st.markdown("##### Nifty 200 + ETFs | Yahoo Finance | v6.0 — Final")
st.markdown("---")

# ── INPUT ──
col1, col2 = st.columns(2)
with col1:
    min_score = st.selectbox("🎯 Min Trade Quality", ["Strong (5+/8)", "Medium (4+/8)", "All (3+/8)"])
with col2:
    st.info("💡 Scanner gives **entry / SL / target**. Capital allocation is your call.", icon="ℹ️")

MIN_SCORE        = int(min_score.split("(")[1].split("+")[0])
MIN_AVG_TURNOVER = 5_00_00_000   # ₹5 Cr liquidity floor
MIN_RS           = 5.0           # stock must outperform Nifty by 5%+
MIN_ATR_PCT      = 2.0           # ATR must be ≥2% of price (no dead stocks)
MIN_RR           = 2.0           # R:R must be ≥ 1:2

def get_hold_label(score):
    if score >= 7: return "15–20 days"
    elif score >= 5: return "10–15 days"
    else: return "5–10 days"

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
    "DLF.NS":"RealEstate",     "GODREJPROP.NS":"RealEstate","OBEROIRLTY.NS":"RealEstate",
    "PHOENIXLTD.NS":"RealEstate",
    "PIDILITIND.NS":"Chemicals","ATUL.NS":"Chemicals",
    "APOLLOHOSP.NS":"Healthcare","FORTIS.NS":"Healthcare",
    "MAXHEALTH.NS":"Healthcare", "LALPATHLAB.NS":"Healthcare",
    "SBILIFE.NS":"Insurance",  "HDFCLIFE.NS":"Insurance", "ICICIPRULI.NS":"Insurance",
    "HAVELLS.NS":"ConsumerDurables","VOLTAS.NS":"ConsumerDurables","DIXON.NS":"ConsumerDurables",
    "ZOMATO.NS":"NewAge",      "IRCTC.NS":"NewAge",
    "BHARTIARTL.NS":"Telecom",
}

ETFS = {
    "NIFTYBEES.NS":"ETF-Equity",   "JUNIORBEES.NS":"ETF-Equity",
    "MOM50.NS":"ETF-Equity",       "INFRABEES.NS":"ETF-Equity",
    "BANKBEES.NS":"ETF-Sector",    "ITBEES.NS":"ETF-Sector",
    "PHARMABEES.NS":"ETF-Sector",  "PSUBNKBEES.NS":"ETF-Sector",
    "GOLDBEES.NS":"ETF-Commodity", "SILVERBEES.NS":"ETF-Commodity",
}

SECTOR_PROXIES = {
    "Banking":"^NSEBANK",  "NBFC":"^NSEBANK",
    "IT":"^CNXIT",         "Pharma":"^CNXPHARMA",
    "Auto":"^CNXAUTO",     "Energy":"^CNXENERGY",
    "Infra":"^CNXINFRA",   "Metals":"^CNXMETAL",
    "FMCG":"^CNXFMCG",    "RealEstate":"^CNXREALTY",
    "Oil&Gas":"^CNXENERGY","Cement":"^NSEI",
    "Chemicals":"^NSEI",   "Healthcare":"^CNXPHARMA",
    "Insurance":"^NSEI",   "ConsumerDurables":"^NSEI",
    "NewAge":"^NSEI",      "Telecom":"^NSEI",
}

# ── MARKET CONTEXT ──
@st.cache_data(ttl=3600)
def get_nifty_context():
    try:
        df    = yf.download("^NSEI", period="12mo", interval="1d",
                             auto_adjust=True, progress=False)
        close = df['Close'].squeeze()
        ema20  = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        ema50  = ta.trend.EMAIndicator(close, window=50).ema_indicator()
        ema200 = ta.trend.EMAIndicator(close, window=200).ema_indicator()
        p   = float(close.iloc[-1])
        e20 = float(ema20.iloc[-1])
        e50 = float(ema50.iloc[-1])
        e200= float(ema200.iloc[-1])
        # Strict: EMA20 > EMA50 > EMA200 (eliminates sideways markets)
        is_bull = (e20 > e50) and (e50 > e200) and (p > e50)
        trend   = "BULL" if is_bull else "BEAR"
        ret1m   = (p / float(close.iloc[-22]) - 1) * 100
        return trend, ret1m
    except:
        return "UNKNOWN", 0.0

@st.cache_data(ttl=3600)
def get_sector_strengths():
    proxies = list(set(SECTOR_PROXIES.values()))
    out = {}
    for px in proxies:
        try:
            df    = yf.download(px, period="2mo", interval="1d",
                                 auto_adjust=True, progress=False)
            close = df['Close'].squeeze()
            out[px] = (float(close.iloc[-1]) / float(close.iloc[-22]) - 1) * 100
        except:
            out[px] = 0.0
    return out

# ── WEIGHTED SCORE SYSTEM ──
# Trend 25 | RS 25 | Volume 20 | Breakout 20 | RSI 10  → total 100
def compute_score(rsi_now, ema20_now, ema50_now, macd_line, macd_sig,
                  macd_prev, macd_sprev, vol_now, vol_avg_n,
                  price, high20, high50, rs_vs_nifty, sector_strong):
    score, reasons = 0, []

    # ── RSI (10 pts) — widened to 40–75
    if 40 < rsi_now < 75:
        score += 1
        reasons.append(f"RSI {rsi_now:.0f}")

    # ── TREND (25 pts → 2 signals, 1pt each here since max=8)
    if ema20_now > ema50_now:
        score += 1
        reasons.append("Uptrend ✅")

    # ── MACD (part of trend, 1pt)
    macd_fresh = (macd_prev < macd_sprev) and (macd_line > macd_sig)
    if macd_fresh:
        score += 1
        reasons.append("MACD Cross 🔥")
    elif macd_line > macd_sig:
        score += 1
        reasons.append("MACD Bullish")

    # ── VOLUME (mandatory filter handled outside; bonus here)
    vol_ratio = vol_now / vol_avg_n if vol_avg_n > 0 else 0
    if vol_ratio >= 1.5:
        score += 1
        reasons.append(f"Vol {vol_ratio:.1f}x 🔥")

    # ── BREAKOUT (20 pts → 50D=2pts, 20D=1pt)
    if price >= high50 * 0.99:
        score += 2
        reasons.append("50D Breakout 🚀")
    elif price >= high20 * 0.99:
        score += 1
        reasons.append("20D Breakout 📈")

    # ── RELATIVE STRENGTH (25 pts → 1pt, threshold raised to 5%)
    if rs_vs_nifty >= MIN_RS:
        score += 1
        reasons.append(f"RS +{rs_vs_nifty:.1f}% 💪")

    # ── SECTOR STRENGTH
    if sector_strong:
        score += 1
        reasons.append("Sector Leader 🏆")

    return min(score, 8), reasons

# ── CORE ANALYSIS ──
def analyze(symbol, sector, nifty_ret_1m, sector_strengths):
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
        if price < 5:
            return None

        # ── HARD FILTERS (return None = stock rejected completely) ──

        # 1. Liquidity
        turnover_avg = float((close * volume).rolling(20).mean().iloc[-1])
        if turnover_avg < MIN_AVG_TURNOVER:
            return None

        # 2. Volume must be present (mandatory for swing)
        vol_avg_n = float(volume.rolling(20).mean().iloc[-1])
        vol_now   = float(volume.iloc[-1])
        if vol_now < vol_avg_n:
            return None

        # 3. ATR ≥ 2% (eliminates dead/flat stocks)
        atr_i   = ta.volatility.AverageTrueRange(high, low, close, window=14)
        atr_now = float(atr_i.average_true_range().iloc[-1])
        atr_pct = (atr_now / price) * 100
        if atr_pct < MIN_ATR_PCT:
            return None

        # ── INDICATORS ──
        rsi    = ta.momentum.RSIIndicator(close, window=14).rsi()
        ema20  = ta.trend.EMAIndicator(close, window=20).ema_indicator()
        ema50  = ta.trend.EMAIndicator(close, window=50).ema_indicator()
        macd_i = ta.trend.MACD(close)

        rsi_now    = float(rsi.iloc[-1])
        ema20_now  = float(ema20.iloc[-1])
        ema50_now  = float(ema50.iloc[-1])
        macd_line  = float(macd_i.macd().iloc[-1])
        macd_sig   = float(macd_i.macd_signal().iloc[-1])
        macd_prev  = float(macd_i.macd().iloc[-2])
        macd_sprev = float(macd_i.macd_signal().iloc[-2])

        # Breakout levels
        high50 = float(close.tail(51).iloc[:-1].max())
        high20 = float(close.tail(21).iloc[:-1].max())

        # 52-week high distance
        high52w = float(close.tail(252).max())
        dist_52w = round((high52w - price) / high52w * 100, 1)  # % below 52W high

        # Relative strength
        stock_ret_1m = (float(close.iloc[-1]) / float(close.iloc[-22]) - 1) * 100
        rs_vs_nifty  = stock_ret_1m - nifty_ret_1m

        # Sector strength
        proxy        = SECTOR_PROXIES.get(sector, "^NSEI")
        sector_ret   = sector_strengths.get(proxy, 0.0)
        sector_strong = sector_ret > nifty_ret_1m

        # Score
        score, reasons = compute_score(
            rsi_now, ema20_now, ema50_now, macd_line, macd_sig,
            macd_prev, macd_sprev, vol_now, vol_avg_n,
            price, high20, high50, rs_vs_nifty, sector_strong
        )

        if score < MIN_SCORE:
            return None

        # ATR-based SL + targets
        sl_price = round(price - (1.5 * atr_now), 1)
        sl_price = max(sl_price, round(price * 0.88, 1))
        t1_price = round(price + (2.0 * atr_now), 1)
        t2_price = round(price + (3.5 * atr_now), 1)
        rr_ratio = round((t2_price - price) / max(price - sl_price, 0.01), 1)

        # 4. R:R filter
        if rr_ratio < MIN_RR:
            return None

        quality    = round(score / 8 * 100)
        rank_score = (score / 8 * 50) + (min(rs_vs_nifty, 20) / 20 * 30) + (min(rr_ratio, 5) / 5 * 20)

        return {
            'Symbol':    symbol.replace('.NS', ''),
            'Sector':    sector,
            'Price':     round(price, 1),
            'Score':     score,
            'Quality':   quality,
            'RSI':       round(rsi_now, 1),
            'ATR':       round(atr_now, 1),
            'ATR_pct':   round(atr_pct, 1),
            'RS':        round(rs_vs_nifty, 1),
            'SectorRS':  round(sector_ret, 1),
            'Dist52W':   dist_52w,
            'SL':        sl_price,
            'T1':        t1_price,
            'T2':        t2_price,
            'Risk_per_share': round(price - sl_price, 1),
            'RR':        rr_ratio,
            'Hold':      get_hold_label(score),
            'Why':       " | ".join(reasons),
            'IsETF':     'ETF' in sector,
            'RankScore': rank_score,
        }
    except Exception:
        return None

# ── RENDER CARD ──
def render_card(s, rank=None):
    with st.container(border=True):
        h1, h2 = st.columns([3, 1])
        label = f"**#{rank}  {s['Symbol']}**" if rank else f"### {s['Symbol']}"
        h1.markdown(f"{label} `{s['Sector']}`")
        q   = s['Quality']
        cls = "conf-high" if q >= 75 else ("conf-med" if q >= 55 else "conf-low")
        h2.markdown(
            f"<div class='{cls}'>{q}%</div>"
            f"<div style='color:#888;font-size:11px'>Trade Quality</div>",
            unsafe_allow_html=True)

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Price",        f"₹{s['Price']}")
        c2.metric("RSI",          s['RSI'])
        c3.metric("RS vs Nifty",  f"{s['RS']:+.1f}%")
        c4.metric("ATR",          f"{s['ATR_pct']:.1f}%")
        c5.metric("52W High Dist",f"-{s['Dist52W']}%")
        c6.metric("Risk/Share",   f"₹{s['Risk_per_share']}")

        st.success(
            f"🎯 Entry: ₹{s['Price']} | SL: ₹{s['SL']} | "
            f"T1: ₹{s['T1']} | T2: ₹{s['T2']} | "
            f"R:R 1:{s['RR']} | ⏳ {s['Hold']}"
        )
        if not s['IsETF']:
            st.caption(f"📊 {s['Why']} | Sector 1M: {s['SectorRS']:+.1f}%")
        else:
            st.caption(f"📊 {s['Why']}")

# ══════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════
if st.button("🔍 Scan Karo", use_container_width=True, type="primary"):

    with st.spinner("📡 Market context fetch kar raha hoon..."):
        nifty_trend, nifty_ret_1m = get_nifty_context()
        sector_strengths           = get_sector_strengths()

    if nifty_trend == "BULL":
        st.markdown(
            "<span class='trend-bull'>🟢 BULL — EMA20 > EMA50 > EMA200. Strong uptrend confirmed.</span>",
            unsafe_allow_html=True)
    elif nifty_trend == "BEAR":
        st.markdown(
            "<span class='trend-bear'>🔴 BEAR / SIDEWAYS — EMA alignment broken. Sirf 6+ quality signals dikhaunga.</span>",
            unsafe_allow_html=True)
    else:
        st.markdown("⚠️ Nifty data unavailable. Bina trend filter ke chal raha hai.")

    # Leading sectors
    sector_display = {
        s: sector_strengths.get(SECTOR_PROXIES[s], 0)
        for s in SECTOR_PROXIES if SECTOR_PROXIES[s] != "^NSEI"
    }
    top_sectors = sorted(sector_display.items(), key=lambda x: x[1], reverse=True)[:5]
    if top_sectors:
        sec_str = "  |  ".join([f"**{s}** {r:+.1f}%" for s, r in top_sectors])
        st.markdown(f"🏆 **Leading Sectors (1M):** {sec_str} *(Nifty: {nifty_ret_1m:+.1f}%)*")

    st.markdown("---")

    all_symbols = {**ETFS, **UNIVERSE}
    results, total = [], len(all_symbols)
    progress = st.progress(0)
    status   = st.empty()

    for i, (sym, sec) in enumerate(all_symbols.items()):
        status.text(f"⏳ {sym.replace('.NS','')} ... ({i+1}/{total})")
        r = analyze(sym, sec, nifty_ret_1m, sector_strengths)
        if r:
            if nifty_trend == "BEAR" and not r['IsETF'] and r['Score'] < 6:
                pass
            else:
                results.append(r)
        progress.progress((i + 1) / total)

    status.empty()
    progress.empty()

    results = sorted(results, key=lambda x: x['RankScore'], reverse=True)
    etf_eq  = [r for r in results if r['Sector'] == 'ETF-Equity']
    etf_sec = [r for r in results if r['Sector'] == 'ETF-Sector']
    etf_com = [r for r in results if r['Sector'] == 'ETF-Commodity']
    stk_r   = [r for r in results if not r['IsETF']][:10]

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scanned",      total)
    c2.metric("ETF Signals",  len(etf_eq) + len(etf_sec) + len(etf_com))
    c3.metric("Stock Picks",  len(stk_r))
    c4.metric("Market",       nifty_trend)
    st.markdown("---")

    # ETF section — 3 separate groups
    etf_found = any([etf_eq, etf_sec, etf_com])
    if etf_found:
        st.markdown("## 🏦 ETF Signals")
        for grp, label in [(etf_eq,"📊 Broad Market ETFs"),
                            (etf_sec,"🏭 Sector ETFs"),
                            (etf_com,"🪙 Commodity ETFs")]:
            if grp:
                st.markdown(f"**{label}**")
                for s in grp:
                    render_card(s)
        st.markdown("---")

    # Stocks
    if stk_r:
        st.markdown(f"## 📈 Top {len(stk_r)} Stock Opportunities")
        st.caption(
            "Ranked: Score 50% + RS vs Nifty 30% + R:R 20% | "
            "Hard filters: Volume↑ · ATR≥2% · R:R≥1:2 · Liquidity≥₹5Cr"
        )
        for rank, s in enumerate(stk_r, 1):
            render_card(s, rank=rank)

    if not results:
        st.warning("⏳ Koi signal nahi mila. Min Trade Quality kam karo ya kal try karo.")

    st.markdown("---")
    st.caption(
        f"📊 {total} symbols scanned | 🎯 Min {MIN_SCORE}/8 | "
        f"📈 Nifty: {nifty_trend} ({nifty_ret_1m:+.1f}% 1M) | "
        f"Filters: Vol↑mandatory · ATR≥2% · RR≥1:2 · Liquidity≥₹5Cr"
    )

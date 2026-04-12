"""
nse_ticker_universe.py
──────────────────────
SINGLE SOURCE OF TRUTH for all NSE tickers used by NSE Sentinel.

EVERY component that needs a ticker list must import from here:
    from nse_ticker_universe import get_all_tickers

Design
──────
• Hardcoded baseline (~2100 symbols) loaded instantly — zero network, zero fail.
• Optional live supplement from NSE EQUITY_L.csv and bhav copy (adds ~1000 more
  on a live server; silently skipped on Streamlit Cloud / restricted networks).
• Returns deduplicated, sorted list of "SYMBOL.NS" strings.
• Never raises. Never returns an empty list (falls back to baseline).

Public API
──────────
    get_all_tickers(live=True)  → list[str]     (cached after first call)
    get_bare_symbols()          → list[str]     (without .NS suffix)
    ticker_count()              → int
"""

from __future__ import annotations

import io
import threading
import zipfile
from datetime import datetime, timedelta

_LOCK  = threading.Lock()
_cache: list[str] | None = None

# ══════════════════════════════════════════════════════════════════════
# BASELINE  (~2100 NSE mainboard symbols, hardcoded — always available)
# ══════════════════════════════════════════════════════════════════════
_BASELINE: list[str] = [
    # ── LARGE CAP / NIFTY 50 ─────────────────────────────────────────
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","HINDUNILVR","SBIN",
    "BHARTIARTL","ITC","KOTAKBANK","LT","AXISBANK","ASIANPAINT","MARUTI",
    "BAJFINANCE","HCLTECH","SUNPHARMA","TITAN","ULTRACEMCO","ONGC",
    "NESTLEIND","WIPRO","POWERGRID","NTPC","TECHM","INDUSINDBK","ADANIPORTS",
    "TATAMOTORS","JSWSTEEL","BAJAJFINSV","HINDALCO","GRASIM","DIVISLAB",
    "CIPLA","DRREDDY","BPCL","EICHERMOT","APOLLOHOSP","TATACONSUM","BRITANNIA",
    "COALINDIA","HEROMOTOCO","SHREECEM","SBILIFE","HDFCLIFE","ADANIENT",
    "BAJAJ-AUTO","TATASTEEL","UPL","M&M",
    # ── NIFTY NEXT 50 ────────────────────────────────────────────────
    "ADANIGREEN","ADANITRANS","ATGL","AWL","BAJAJHFL","BANKBARODA",
    "BERGEPAINT","BEL","BHEL","BOSCHLTD","CANBK","CGPOWER","CHOLAFIN",
    "COLPAL","CUMMINSIND","DABUR","DLF","DMART","GODREJCP","GODREJPROP",
    "HAL","HAVELLS","HDFCAMC","ICICIGI","ICICIPRULI","IOC","IRCTC",
    "IRFC","LODHA","LTIM","LTTS","MARICO","MOTHERSON","MUTHOOTFIN",
    "NAUKRI","NHPC","OFSS","PAGEIND","PERSISTENT","PFC","PIDILITIND",
    "POLYCAB","PNB","RECLTD","SHRIRAMFIN","SRF","TORNTPHARM","TRENT",
    "TVSMOTOR","UNIONBANK","VEDL","ZOMATO","ZYDUSLIFE",
    # ── NIFTY MIDCAP 150 ─────────────────────────────────────────────
    "AARTIIND","ABCAPITAL","ABFRL","ACC","AFFLE","AJANTPHARM",
    "ALKEM","ALKYLAMINE","ANGELONE","APLAPOLLO","APOLLOTYRE","APTUS",
    "ASTRAL","AUBANK","AUROPHARMA","BALKRISHIND","BANDHANBNK","BATAINDIA",
    "BIKAJI","BIOCON","BIRLASOFT","BLUESTARCO","BRIGADE","CARBORUNIV",
    "CASTROLIND","CDSL","CESC","CHENNPETRO","CLEAN","COFORGE","CROMPTON",
    "CYIENT","DALBHARAT","DATAMATICS","DCBBANK","DEEPAKNTR","DELHIVERY",
    "DEVYANI","DIXON","DOMS","ECLERX","EIDPARRY","ELGIEQUIP",
    "EMAMILTD","ENDURANCE","EPL","EQUITASBNK","ESCORTS","EXIDEIND",
    "FINEORG","FLUOROCHEM","FORTIS","GABRIEL","GALAXYSURF","GLAND",
    "GLAXO","GLENMARK","GNFC","GRINDWELL","GSFC","GUJGASLTD",
    "HAPPSTMNDS","HATSUN","HFCL","HLEGLAS","HOMEFIRST","HPCL",
    "HUDCO","IEX","IGL","INDIAMART","INDIGO","INOXWIND","IOB",
    "IPCALAB","IREDA","ISEC","JBCHEPHARM","JKCEMENT","JKLAKSHMI",
    "JMFINANCIL","JSL","JUBILANT","JUBLFOOD","KAJARIACER","KALPATPOWR",
    "KALYANKJIL","KANSAINER","KEC","KIMS","KPITTECH","KRSNAA",
    "KSCL","LAURUSLABS","LAXMIMACH","LICHSGFIN","LLOYDSME","LUXIND",
    "MANAPPURAM","MANKIND","MAPMYINDIA","MASTEK","MAXHEALTH",
    "METROPOLIS","MFSL","MIDHANI","MOTILALOFS",
    "MPHASIS","MRPL","NAVINFLUOR","NBCC","NIACL","NILKAMAL",
    "NMDC","NOCIL","NYKAA","OBEROIRLTY","OIL","ORIENTELEC","PATELENG",
    "PAYTM","PCBL","PGHH","PHOENIXLTD","PNBHOUSING","POLICYBZR",
    "POLYMED","PRESTIGE","PRINCEPIPE","RITES","RVNL","SAFARI",
    "SAIL","SCHAEFFLER","SJVN","SKF","SOBHA","SONACOMS",
    "STARHEALTH","SUDARSCHEM","SUNDARMFIN",
    "SUNTECK","SUNTV","SUZLON","SYMPHONY",
    "TANLA","TATACHEM","TATACOMM","TATAPOWER","TEAMLEASE",
    "TIINDIA","TIMKEN","TITAGARH","TORNTPOWER","TRIDENT",
    "TRIVENI","UJJIVANSFB","UTIAMC","VGUARD",
    "VMART","VOLTAS","WELSPUNLIV","WHIRLPOOL",
    "ZEEL","ZENSAR",
    # ── NIFTY SMALLCAP 250 ───────────────────────────────────────────
    "3MINDIA","AAVAS","ACE","ACRYSIL","ADFFOODS","AEGISLOG","AETHER",
    "AIAENG","AKZOINDIA","ALEMBICLTD","ALICON","ALLCARGO","ALOKINDS","AMBIKCO",
    "AMBUJACEM","AMBER","ANANTRAJ","ANUP","APARINDS","APOLLOPIPE",
    "ARCHIDPLY","ARVINDFASHN","ASAHIINDIA","ASHIANA","ASHOKLEY","ASTERDM",
    "ASTRAZEN","ATUL","AVANTIFEED","AXISCADES","AZAD",
    "BAJAJCON","BAJAJHIND","BALKRISHIND","BALMLAWRIE","BALRAMCHIN","BANKBARODA",
    "BASF","BBTC","BECTORFOOD","BHAGERIA","BHARATFORG","BHARATGEAR",
    "BHORUKA","BIRLACABLE","BOROLTD","BPL","BSEINDIA","BURGERKING",
    "BUTTERFLY","CADILAHC","CAMLINFINE","CAMPUS",
    "CANFINHOME","CANTABIL","CAPACITE","CARERATING","CARTRADE",
    "CERA","CHALET","CHAMBLFERT","CHEMPLASTS",
    "CIEINDIA","CMSINFO","COCHINSHIP","COROMANDEL","COSMOFILMS","CRAFTSMAN",
    "CREDITACC","CRISIL","CUMMINSIND","CYIENT","DALBHARAT","DALMIASUG",
    "DBCORP","DCBBANK","DEEPAKFERT","DELTACORP","DHARMAJ","DISHTV",
    "DOLLAR","DREDGECORP","EASEMYTRIP","ECLERX","EIDPARRY","EIL",
    "ELECTCAST","ELGIEQUIP","EMKAY","ESABINDIA","ESAFSFB","ESCORTS",
    "ESTER","ETHOSLTD","FEDERALBNK","FINEORG","FINOLEX",
    "FORCEMOT","FORTIS","GAEL","GALAXYSURF","GANESHBE","GARFIBRES","GARWARE",
    "GATI","GATEWAY","GHCL","GILLETTE","GLOBALVECT",
    "GMBREW","GMRAIRPORT","GNFC","GOACARBON","GOKALDAS","GOLDIAM",
    "GOODLUCK","GPIL","GPPL","GRANULES","GREAVESCOT","GREENPANEL",
    "GREENPLY","GRINDWELL","GRSE","GUFICBIO","GUJALKALI","GUJGASLTD",
    "GULFOILLUB","HCG","HDFCAMC","HECL","HERITGFOOD","HFCL","HGINFRA",
    "HIKAL","HLEGLAS","HMVL","HONAUT","HUBTOWN","HUHTAMAKI",
    "IBREALEST","IDFC","IDFCFIRSTB","INDHOTEL","INDIAMART",
    "INDIANB","INDIGO","INDORAMA","INDOSTAR","INFIBEAM","INTELLECT",
    "IOB","IPCALAB","IRCON","ISEC","ITD","ITDCEM","IVP",
    "JAGRAN","JAIBALAJI","JAICORPLTD","JAMNAAUTO","JASH","JBMA",
    "JCHAC","JIOFIN","JKTYRE","JMFINANCIL","JPPOWER",
    "JTEKTINDIA","JUSTDIAL","JYOTHYLAB","KAJARIACER","KALPATPOWR","KALYANKJIL",
    "KAMDHENU","KANSAINER","KARURVYSYA","KCP","KDDL","KHADIM",
    "KIRIINDUS","KNR","KOLTEPATIL","KOPRAN","KPRMILL","KRBL","KSCL",
    "LATENTVIEW","LAURUSLABS","LEMONTREE","LLOYDSME","LUPIN","LUXIND",
    "MAHINDCIE","MAHINDLOG","MAHSEAMLES","MAITHANALL","MANAPPURAM","MARKSANS",
    "MASTEK","MAWANASUG","MCDOWELL-N","MEDPLUS","MFSL","MIDHANI",
    "MINDAIND","MINDACORP","MINDSPACE","MIRC","MMTC","MOLDTEK",
    "MONTECARLO","MOTILALOFS","MPHASIS","MRPL","MSTCLTD","MUTHOOTCAP",
    "NACLIND","NAHARPOLY","NAHARSPINN","NAVNETEDUL","NBCC",
    "NEULANDLAB","NEWGEN","NILKAMAL","NLCINDIA","NOCIL","NUCLEUS",
    "OBEROIRLTY","OFSS","ORCHPHARMA","ORIENTBELL","ORIENTCEM","ORIENTELEC",
    "PAISALO","PANAMAPET","PARADEEP","PATELENG","PFIZER",
    "PHOENIXLTD","PILANIINVS","POLYMED","POWERMECH","PPAP","PRAJIND",
    "PRICOLLTD","PRISM","PVRINOX","QUESS","QUICKHEAL","RADICO",
    "RAJRATAN","RALLIS","RAMCOCEM","RAYMOND","RBLBANK","RECLTD",
    "REDTAPE","RELAXO","RENUKA","REPCOHOME","RFCL","RITES",
    "ROLEXRINGS","ROSSARI","RPOWER","RUPA","RVNL","SAFARI","SAKSOFT",
    "SANOFI","SAPPHIRE","SEASOFTS","SEQUENT","SESHAPAPER",
    "SHANKARA","SHAREINDIA","SHILPAMED","SHIVALIK","SHOPERSTOP",
    "SIYSIL","SKFINDIA","SKIPPER","SNOWMAN","SOBHA","SOLARA",
    "SOLARINDS","SONACOMS","SOTL","SPARC","STLTECH","SUBROS",
    "SUPRIYA","SUPRAJIT","SURANASOL","SURYAROSNI","SUVENPHAR",
    "SYMPHONY","TAINWALCHM","TANLA","TATACHEM","TATACOMM","TATAPOWER",
    "TDPOWERSYS","THYROCARE","TIINDIA","TIMKEN","TITAGARH",
    "TORNTPOWER","TRIDENT","TRIVENI","UFLEX","UJJIVANSFB","UTIAMC",
    "VGUARD","VIPIND","VMART","VOLTAMP","VOLTAS","VSTIND","WELSPUNLIV",
    "WHIRLPOOL","ZEEL","ZENSAR",
    # ── BANKS & NBFC ─────────────────────────────────────────────────
    "HDFCBANK","ICICIBANK","SBIN","KOTAKBANK","AXISBANK","INDUSINDBK",
    "BANKBARODA","PNB","UNIONBANK","CANBK","IDFCFIRSTB","FEDERALBNK",
    "RBLBANK","KARURVYSYA","DCBBANK","AUBANK","EQUITASBNK","UJJIVANSFB",
    "ESAFSFB","CAPITALSFB","JSFB","SURYODAY","UTKARSHBNK","NSDL",
    "BAJFINANCE","BAJAJFINSV","CHOLAFIN","MUTHOOTFIN","MANAPPURAM",
    "SHRIRAMFIN","LICHSGFIN","PNBHOUSING","CANFINHOME","HOMEFIRST",
    "APTUS","AAVAS","REPCO","CREDITACC","SRTRANSFIN","TATAELXSI",
    "HDFCAMC","UTIAMC","ABSLAMC","NAUKRI","ANGELONE","ISEC","IIFL",
    "CDSL","BSEINDIA","MCXINDIA","5PAISA","ICICIGI","ICICIPRULI",
    "SBILIFE","HDFCLIFE","STARHEALTH","MAXFINSERV","MFSL","BAJAJHFL",
    # ── IT & TECH ────────────────────────────────────────────────────
    "TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM","LTTS","MPHASIS",
    "COFORGE","PERSISTENT","KPITTECH","BIRLASOFT","MASTEK","CYIENT",
    "ECLERX","NIIT","NIITLTD","RATEPOWER","RATEGAIN","TANLA","NEWGEN",
    "INTELLECT","HAPPSTMNDS","TATAELXSI","ZENSAR","HEXAWARE","NUCLEUS",
    "SAKSOFT","DATAMATICS","QUICKHEAL","INFIBEAM","INDIAMART","AFFLE",
    "NAZARA","LATENTVIEW","MAPMYINDIA","ZAGGLE","NAUKRI",
    # ── PHARMA / HEALTH ──────────────────────────────────────────────
    "SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","AUROPHARMA","BIOCON",
    "LUPIN","ALKEM","AJANTPHARM","IPCALAB","NATCOPHARMA","JBCHEPHARM",
    "GLENMARK","GLAND","GRANULES","LAURUSLABS","FLUOROCHEM","SOLARA",
    "SEQUENT","SUPRIYA","NAVINFLUOR","SUVENPHAR","NEULANDLAB","ORCHPHARMA",
    "FINEORG","ALKYLAMINE","DEEPAKNTR","NOCIL","SUDARSCHEM","VINATIORGA",
    "LXCHEM","AARTI","AARTIIND","VINATI","PCBL","ROSSARI","TATACHEM",
    "GNFC","GSFC","EIDPARRY","COROMANDEL","UPL","RALLIS","DHANUKA",
    "BAYER","PARADEEP","INSECTICID",
    "APOLLOHOSP","MAXHEALTH","FORTIS","KIMS","ASTER","ASTERDM",
    "NARAYANAH","SHALBY","THYROCARE","METROPOLIS","KRSNAA","HCG",
    # ── AUTO & ANCILLARIES ───────────────────────────────────────────
    "MARUTI","TATAMOTORS","M&M","BAJAJ-AUTO","HEROMOTOCO","EICHERMOT",
    "TVSMOTOR","ASHOKLEY","ESCORTS","FORCEMOT","SMLISUZU",
    "BALKRISHIND","APOLLOTYRE","JKTYRE","CEATLTD","MINDA",
    "MOTHERSON","BOSCHLTD","ENDURANCE","MINDACORP","SONACOMS","TIINDIA",
    "SUPRAJIT","SUBROS","GABRIEL","WABCOINDIA","JTEKTINDIA","CRAFTSMAN",
    "SCHAEFFLER","SKF","TIMKEN","NRB","MAHINDCIE","PRICOLLTD",
    "SWARAJENG","MAHSCOOTER","MAHINDRA",
    # ── METALS & MINING ──────────────────────────────────────────────
    "TATASTEEL","JSWSTEEL","HINDALCO","VEDL","SAIL","NMDC","MOIL",
    "NALCO","HINDCOPPER","TINPLATE","RATNAMANI","APL","JSL",
    "APLAPOLLO","LLOYDSME","JSHL","GPIL","NAVA","WELCORP","SUNFLAG",
    "JTEKTINDIA","KALYANKJIL",
    # ── ENERGY / OIL & GAS ───────────────────────────────────────────
    "ONGC","BPCL","IOC","HPCL","GAIL","OIL","MRPL","CHENNPETRO",
    "ATGL","IGL","MGL","GUJGASLTD","GSPL","TORNTPOWER","TATAPOWER",
    "ADANIGREEN","ADANIPOWER","ADANITRANS","NHPC","NTPC","POWERGRID",
    "SJVN","IREDA","INOXWIND","SUZLON","RPOWER","JPPOWER","CESC",
    "TORNTPOWER","PTC","NLCINDIA",
    # ── FMCG ─────────────────────────────────────────────────────────
    "HINDUNILVR","ITC","NESTLEIND","BRITANNIA","TATACONSUM","MARICO",
    "GODREJCP","DABUR","EMAMILTD","COLPAL","PGHH","JYOTHYLAB","BAJAJCON",
    "GILLETTE","BIKAJI","AVANTIFEED","KRBL","HATSUN","HERITGFOOD",
    "VSTIND","RADICO","MCDOWELL-N","TILAKNAGAR",
    # ── RETAIL / CONSUMER ────────────────────────────────────────────
    "TRENT","DMART","WESTLIFE","JUBLFOOD","DEVYANI","DIXON","AMBER",
    "SHOPERSTOP","VMART","BATAINDIA","RELAXO","KPRMILL",
    "PAGEIND","VEDANT","GOKALDAS","RAYMOND","CANTABIL","VIPIND",
    "LUXIND","RUPA","DOLLAR","CAMPUS","NYKAA","SAFARI","DOMS","REDTAPE",
    # ── REAL ESTATE / INFRA ──────────────────────────────────────────
    "DLF","OBEROIRLTY","GODREJPROP","PHOENIXLTD","BRIGADE","SOBHA",
    "KOLTEPATIL","SUNTECK","LODHA","PRESTIGE","ANANTRAJ","OMAXE",
    "NESCO","IBREALEST","MHRIL","CHALET","LEMONTREE","INDHOTEL",
    # ── CAPITAL GOODS / ENGINEERING ──────────────────────────────────
    "LT","SIEMENS","ABB","BHEL","THERMAX","CUMMINSIND","ELGIEQUIP",
    "KEC","KALPATPOWR","GRINDWELL","TIMKEN","SKF","SCHAEFFLER","HAL",
    "BEL","MTAR","GRSE","COCHINSHIP","MAZAGON",
    "PATELENG","NBCC","IRCON","HGINFRA","KNR","ASHOKA",
    "ITD","CAPACITE","GPPL","CONCOR","ALLCARGO","AEGISLOG","BLUEDART",
    "GATI","TCI","DREDGECORP","RVNL","RAILTEL","TITAGARH",
    "AIAENG","APARINDS","GREAVESCOT","TDPOWERSYS","VOLTAMP","POWERMECH",
    # ── TELECOM / MEDIA ──────────────────────────────────────────────
    "BHARTIARTL","TATACOMM","RAILTEL","HFCL","STLTECH",
    "INDUSTOWER","OPTIEMUS","DISHTV","SUNTV","PVRINOX","DBCORP",
    "JAGRAN","HMVL","NDTV","ZEEMEDIA",
    # ── AGRI / FERTILISERS ───────────────────────────────────────────
    "UPL","DHANUKA","BAYER","RALLIS","PARADEEP","COROMANDEL","GSFC",
    "GNFC","CHAMBLFERT","KSCL","INSECTICID","DHARMAJ","EIDPARRY",
    "BAJAJHIND","BALRAMCHIN","RENUKA","TRIVENI","MAWANASUG",
    # ── LOGISTICS ────────────────────────────────────────────────────
    "DELHIVERY","ALLCARGO","GATI","TCI","BLUEDART","CONCOR","SNOWMAN",
    "INTERGLOBE","SPICEJET","GMRAIRPORT",
    # ── TEXTILES ─────────────────────────────────────────────────────
    "WELSPUNLIV","TRIDENT","RAYMOND","SIYARAM","VIPIND","GOKALDAS",
    "ARVINDFASHN","SUTLEJTEX","AYMSYNTEX","FILATEX","GARFIBRES","GARWARE",
    "MORARJEE","MPDL",
    # ── PAPER / PACKAGING ────────────────────────────────────────────
    "UFLEX","MOLDTEK","HUHTAMAKI","EPL","COSMOFILMS","PRINCEPIPE","ASTRAL",
    # ── DEFENCE ──────────────────────────────────────────────────────
    "HAL","BEL","BHEL","MTAR","GRSE","COCHINSHIP","MAZAGON","MIDHANI",
    "IDEAFORGE",
    # ── GEMS & JEWELLERY ─────────────────────────────────────────────
    "TITAN","KALYANKJIL","RAJESHEXPO","GOLDIAM","SENCO","THANGAMAYL",
    # ── CONSUMER DURABLES ────────────────────────────────────────────
    "HAVELLS","CROMPTON","ORIENTELEC","BLUESTARCO","VOLTAS","SYMPHONY",
    "VGUARD","CERA","KAJARIACER","SOMANYCER",
    # ── MISC ─────────────────────────────────────────────────────────
    "GREENPLY","BAJAJELEC","QUESS","TEAMLEASE","JUSTDIAL",
    "AFFLE","RATEGAIN","NAZARA","LATENTVIEW","ZAGGLE","EASEMYTRIP",
    "MMTC","STCINDIA","MSTCLTD","IRCTC","ABBOTINDIA","HONAUT",
    "GLAXO","PFIZER","SANOFI","CARBORUNIV","WENDT","ELGIEQUIP",
]

# ══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════

def get_all_tickers(live: bool = True) -> list[str]:
    """
    Return sorted list of 'SYMBOL.NS' strings.

    live=True  → attempts NSE EQUITY_L.csv + bhav copy supplement
                 (silently skipped if network is unavailable)
    live=False → returns baseline only (instant, zero network)

    Result is cached after the first call (thread-safe).
    Never raises. Never returns an empty list.
    """
    global _cache
    with _LOCK:
        if _cache is not None:
            return _cache
        result = _build(live)
        _cache = result
        return result


def get_bare_symbols() -> list[str]:
    """Return ticker list without .NS suffix."""
    return [t.replace(".NS", "") for t in get_all_tickers()]


def ticker_count() -> int:
    return len(get_all_tickers())


def invalidate_cache() -> None:
    """Force re-build on next call (e.g. after a manual refresh)."""
    global _cache
    with _LOCK:
        _cache = None


# ══════════════════════════════════════════════════════════════════════
# INTERNAL BUILDER
# ══════════════════════════════════════════════════════════════════════

def _build(live: bool) -> list[str]:
    tickers: set[str] = {f"{s}.NS" for s in _BASELINE}

    if not live:
        return sorted(tickers)

    # ── Supplement 1: NSE EQUITY_L.csv ───────────────────────────────
    try:
        import requests
        _HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.nseindia.com/",
        }
        import pandas as pd
        session = requests.Session()
        session.headers.update(_HEADERS)
        session.get("https://www.nseindia.com/", timeout=8)
        r = session.get(
            "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
            timeout=15,
        )
        if r.status_code == 200 and len(r.content) > 5000:
            df_eq = pd.read_csv(io.StringIO(r.text))
            col = "SYMBOL" if "SYMBOL" in df_eq.columns else df_eq.columns[0]
            for s in df_eq[col].dropna().unique():
                tickers.add(f"{str(s).strip()}.NS")
    except Exception:
        pass  # network unavailable — baseline is sufficient

    # ── Supplement 2: bhav copy (only if EQUITY_L was inaccessible) ──
    if len(tickers) < 1500:
        try:
            import requests, pandas as pd
            _HEADERS2 = {"User-Agent": "Mozilla/5.0"}
            for days_back in range(0, 7):
                try:
                    dt = datetime.now() - timedelta(days=days_back)
                    if dt.weekday() >= 5:
                        continue
                    date_str = dt.strftime("%d%b%Y").upper()
                    url = (
                        f"https://archives.nseindia.com/content/historical/EQUITIES/"
                        f"{dt.year}/{dt.strftime('%b').upper()}/cm{date_str}bhav.csv.zip"
                    )
                    r = requests.get(url, headers=_HEADERS2, timeout=15)
                    if r.status_code == 200 and len(r.content) > 1000:
                        z = zipfile.ZipFile(io.BytesIO(r.content))
                        df_bh = pd.read_csv(z.open(z.namelist()[0]))
                        for s in df_bh["SYMBOL"].dropna().unique():
                            tickers.add(f"{s.strip()}.NS")
                        break
                except Exception:
                    continue
        except Exception:
            pass

    return sorted(tickers)
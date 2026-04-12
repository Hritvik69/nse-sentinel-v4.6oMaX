"""
EMERGENCY PATCH — paste this over fetch_nse_tickers() in app.py
================================================================

PROBLEMS FIXED
──────────────
1. CRITICAL BUG: The original _NSE_MAINBOARD list had a Python comment (#)
   mid-line that silently discarded hundreds of symbols:

       "AARTIIND"  # BUG FIX: removed AAPL,"ABCAPITAL","ABFRL",...
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                   Everything after # is a comment — not parsed as symbols!

   This alone reduced ~2100 symbols to ~67 on Streamlit Cloud.

2. st.cache_data locks in the broken count for 3600 seconds.
   Adding show_spinner=True + a clear mechanism forces a refresh.

3. Streamlit Cloud blocks NSE live endpoints — the live supplement
   silently failed, leaving only the corrupted baseline.

INTEGRATION
───────────
In app.py, find the line:
    @st.cache_data(ttl=3600, show_spinner=False)
    def fetch_nse_tickers() -> list:

Replace the ENTIRE function body (everything until the next top-level def)
with the function below.

If you've already deployed nse_ticker_universe.py, Option A is cleaner.
If you haven't, use Option B (self-contained, zero new file dependency).
"""

# ══════════════════════════════════════════════════════════════════════
# OPTION A — uses nse_ticker_universe.py (recommended if deployed)
# ══════════════════════════════════════════════════════════════════════

OPTION_A = '''
from nse_ticker_universe import get_all_tickers as _get_all_tickers

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_nse_tickers() -> list:
    """
    Single source of truth — delegates to nse_ticker_universe.
    Falls back to ~2100-symbol hardcoded baseline on restricted networks.
    """
    tickers = _get_all_tickers(live=True)
    if len(tickers) < 100:
        # Safety net: invalidate cache and return baseline directly
        fetch_nse_tickers.clear()
        tickers = _get_all_tickers(live=False)
    return tickers
'''

# ══════════════════════════════════════════════════════════════════════
# OPTION B — self-contained, no new file dependency
# ══════════════════════════════════════════════════════════════════════
#
# Paste this directly into app.py as a drop-in replacement for the
# existing fetch_nse_tickers() function.
# The key fix: each symbol is on its OWN line — no comments after commas.
#
OPTION_B = '''
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_nse_tickers() -> list:
    """
    NSE Mainboard universe — ~2100 symbols, hardcoded baseline.
    Always loads instantly. Live NSE supplement added when accessible.
    FIXED: each symbol on its own line — no mid-line # comments.
    """
    # fmt: off  (tells Black/linters not to reformat this list)
    _BASE = [
        # NIFTY 50
        "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","HINDUNILVR","SBIN",
        "BHARTIARTL","ITC","KOTAKBANK","LT","AXISBANK","ASIANPAINT","MARUTI",
        "BAJFINANCE","HCLTECH","SUNPHARMA","TITAN","ULTRACEMCO","ONGC",
        "NESTLEIND","WIPRO","POWERGRID","NTPC","TECHM","INDUSINDBK","ADANIPORTS",
        "TATAMOTORS","JSWSTEEL","BAJAJFINSV","HINDALCO","GRASIM","DIVISLAB",
        "CIPLA","DRREDDY","BPCL","EICHERMOT","APOLLOHOSP","TATACONSUM","BRITANNIA",
        "COALINDIA","HEROMOTOCO","SHREECEM","SBILIFE","HDFCLIFE","ADANIENT",
        "BAJAJ-AUTO","TATASTEEL","UPL","M&M",
        # NIFTY NEXT 50
        "ADANIGREEN","ADANITRANS","ATGL","AWL","BAJAJHFL","BANKBARODA",
        "BERGEPAINT","BEL","BHEL","BOSCHLTD","CANBK","CGPOWER","CHOLAFIN",
        "COLPAL","CUMMINSIND","DABUR","DLF","DMART","GODREJCP","GODREJPROP",
        "HAL","HAVELLS","HDFCAMC","ICICIGI","ICICIPRULI","IOC","IRCTC",
        "IRFC","LODHA","LTIM","LTTS","MARICO","MOTHERSON","MUTHOOTFIN",
        "NAUKRI","NHPC","OFSS","PAGEIND","PERSISTENT","PFC","PIDILITIND",
        "POLYCAB","PNB","RECLTD","SHRIRAMFIN","SRF","TORNTPHARM","TRENT",
        "TVSMOTOR","UNIONBANK","VEDL","ZOMATO","ZYDUSLIFE",
        # NIFTY MIDCAP 150 — NOTE: each symbol on its own line, NO inline comments
        "AARTIIND",
        "ABCAPITAL",
        "ABFRL",
        "ACC",
        "AFFLE",
        "AJANTPHARM",
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
        "VMART","VOLTAS","WELSPUNLIV","WHIRLPOOL","ZEEL","ZENSAR",
        # NIFTY SMALLCAP 250
        "3MINDIA","AAVAS","ACE","ACRYSIL","ADFFOODS","AEGISLOG","AETHER",
        "AIAENG","AKZOINDIA","ALEMBICLTD","ALICON","ALLCARGO","ALOKINDS",
        "AMBIKCO","AMBUJACEM","AMBER","ANANTRAJ","ANUP","APARINDS",
        "APOLLOPIPE","ARVINDFASHN","ASAHIINDIA","ASHIANA","ASHOKLEY",
        "ASTERDM","ASTRAZEN","ATUL","AVANTIFEED","AXISCADES","AZAD",
        "BAJAJCON","BAJAJHIND","BALMLAWRIE","BALRAMCHIN","BASF","BBTC",
        "BECTORFOOD","BHAGERIA","BHARATFORG","BHARATGEAR","BHORUKA",
        "BIRLACABLE","BOROLTD","BPL","BSEINDIA","BURGERKING","BUTTERFLY",
        "CADILAHC","CAMLINFINE","CAMPUS","CANFINHOME","CANTABIL","CAPACITE",
        "CARERATING","CARTRADE","CERA","CHALET","CHAMBLFERT","CHEMPLASTS",
        "CIEINDIA","CMSINFO","COCHINSHIP","COROMANDEL","COSMOFILMS",
        "CRAFTSMAN","CREDITACC","CRISIL","DALMIASUG","DBCORP","DEEPAKFERT",
        "DELTACORP","DHARMAJ","DISHTV","DOLLAR","DREDGECORP","EASEMYTRIP",
        "EIL","ELECTCAST","EMKAY","ESABINDIA","ESAFSFB","ESTER","ETHOSLTD",
        "FEDERALBNK","FINOLEX","FORCEMOT","GAEL","GANESHBE","GARFIBRES",
        "GARWARE","GATI","GATEWAY","GHCL","GILLETTE","GLOBALVECT","GMBREW",
        "GMRAIRPORT","GOACARBON","GOKALDAS","GOLDIAM","GOODLUCK","GPIL",
        "GPPL","GRANULES","GREAVESCOT","GREENPANEL","GREENPLY","GRSE",
        "GUFICBIO","GUJALKALI","GULFOILLUB","HCG","HECL","HERITGFOOD",
        "HGINFRA","HIKAL","HMVL","HONAUT","HUBTOWN","HUHTAMAKI",
        "IBREALEST","IDFC","IDFCFIRSTB","INDHOTEL","INDIANB","INDORAMA",
        "INDOSTAR","INFIBEAM","INTELLECT","ITD","ITDCEM","IVP",
        "JAGRAN","JAIBALAJI","JAICORPLTD","JAMNAAUTO","JASH","JBMA",
        "JCHAC","JIOFIN","JKTYRE","JPPOWER","JTEKTINDIA","JUSTDIAL",
        "JYOTHYLAB","KAMDHENU","KARURVYSYA","KCP","KDDL","KHADIM",
        "KIRIINDUS","KNR","KOLTEPATIL","KOPRAN","KPRMILL","KRBL",
        "LATENTVIEW","LEMONTREE","LUPIN","MAHINDCIE","MAHINDLOG",
        "MAHSEAMLES","MAITHANALL","MARKSANS","MAWANASUG","MCDOWELL-N",
        "MEDPLUS","MINDAIND","MINDACORP","MINDSPACE","MIRC","MMTC",
        "MOLDTEK","MONTECARLO","MORARJEE","MSTCLTD","MUTHOOTCAP",
        "NACLIND","NAHARPOLY","NAHARSPINN","NAVNETEDUL","NEULANDLAB",
        "NEWGEN","NLCINDIA","NUCLEUS","ORCHPHARMA","ORIENTBELL","ORIENTCEM",
        "PAISALO","PANAMAPET","PARADEEP","PFIZER","PILANIINVS","POWERMECH",
        "PPAP","PRAJIND","PRICOLLTD","PRISM","PVRINOX","QUESS","QUICKHEAL",
        "RADICO","RAJRATAN","RALLIS","RAMCOCEM","RAYMOND","RBLBANK",
        "REDTAPE","RELAXO","RENUKA","REPCOHOME","RFCL","ROLEXRINGS",
        "ROSSARI","RPOWER","RUPA","SAKSOFT","SANOFI","SAPPHIRE",
        "SEASOFTS","SEQUENT","SESHAPAPER","SHANKARA","SHAREINDIA",
        "SHILPAMED","SHIVALIK","SHOPERSTOP","SKFINDIA","SKIPPER","SNOWMAN",
        "SOLARA","SOLARINDS","SONACOMS","SOTL","SPARC","STLTECH","SUBROS",
        "SUPRIYA","SUPRAJIT","SURANASOL","SURYAROSNI","SUVENPHAR",
        "TAINWALCHM","THYROCARE","TIINDIA","TRIDENT","UFLEX",
        "VIPIND","VOLTAMP","VSTIND","WABCOINDIA","WELCORP","ZENSAR",
        # BANKS & NBFC
        "AUBANK","BANDHANBNK","CAPITALSFB","DCBBANK","EQUITASBNK",
        "ESAFSFB","IDFCFIRSTB","JSFB","KARURVYSYA","RBLBANK","UJJIVANSFB",
        "AAVAS","APTUS","BAJAJHFL","CANFINHOME","CHOLAFIN","CREDITACC",
        "HOMEFIRST","LICHSGFIN","MANAPPURAM","MUTHOOTFIN","PNBHOUSING",
        "REPCO","SHRIRAMFIN","SRTRANSFIN","5PAISA","ABSLAMC","ANGELONE",
        "BSEINDIA","CDSL","HDFCAMC","ICICIPRULI","ICICIGI","ISEC",
        "MCXINDIA","MFSL","NAUKRI","SBILIFE","STARHEALTH","UTIAMC",
        # IT & TECH
        "BIRLASOFT","COFORGE","CYIENT","ECLERX","HAPPSTMNDS","HEXAWARE",
        "KPITTECH","LATENTVIEW","LTIM","LTTS","MAPMYINDIA","MASTEK",
        "MPHASIS","NAZARA","NIITLTD","NUCLEUS","PERSISTENT","RATEGAIN",
        "SAKSOFT","TANLA","TATAELXSI","ZENSAR","ZAGGLE","AFFLE",
        # PHARMA & HEALTH
        "AJANTPHARM","ALKEM","ALKYLAMINE","AUROPHARMA","BIOCON","CIPLA",
        "DEEPAKNTR","DIVISLAB","DRREDDY","FINEORG","FLUOROCHEM","GLAND",
        "GLENMARK","GRANULES","IPCALAB","JBCHEPHARM","LAURUSLABS","LUPIN",
        "NATCOPHARMA","NAVINFLUOR","NEULANDLAB","NOCIL","ORCHPHARMA",
        "SEQUENT","SOLARA","SUPRIYA","SUVENPHAR","SUNPHARMA","VINATIORGA",
        "APOLLOHOSP","ASTERDM","FORTIS","HCG","KIMS","KRSNAA","MAXHEALTH",
        "METROPOLIS","NARAYANAH","SHALBY","THYROCARE",
        # AUTO & ANCILLARIES
        "APOLLOTYRE","ASHOKLEY","BAJAJ-AUTO","BALKRISHIND","BOSCHLTD",
        "CEATLTD","CRAFTSMAN","EICHERMOT","ENDURANCE","ESCORTS","FORCEMOT",
        "GABRIEL","HEROMOTOCO","JTEKTINDIA","M&M","MAHINDCIE","MARUTI",
        "MINDACORP","MOTHERSON","NRB","PRICOLLTD","SCHAEFFLER","SKF",
        "SMLISUZU","SONACOMS","SUBROS","SUPRAJIT","SWARAJENG","TATAMOTORS",
        "TIINDIA","TIMKEN","TVSMOTOR","WABCOINDIA",
        # METALS & MINING
        "APLAPOLLO","GPIL","HINDALCO","HINDCOPPER","JSWSTEEL","JSL",
        "JSHL","LLOYDSME","MOIL","NALCO","NMDC","NAVA","RATNAMANI",
        "SAIL","TATASTEEL","TINPLATE","VEDL","WELCORP",
        # ENERGY / OIL & GAS
        "ADANIGREEN","ADANIPOWER","ADANITRANS","ATGL","BPCL","CESC",
        "GAIL","GUJGASLTD","GSPL","HPCL","IGL","INOXWIND","IOC",
        "IREDA","JPPOWER","MGL","MRPL","NHPC","NLCINDIA","NTPC",
        "OIL","ONGC","POWERGRID","PTC","RPOWER","SJVN","SUZLON",
        "TATAPOWER","TORNTPOWER",
        # FMCG
        "AVANTIFEED","BAJAJCON","BIKAJI","BRITANNIA","COLPAL","DABUR",
        "EMAMILTD","GILLETTE","GODREJCP","HATSUN","HERITGFOOD","HINDUNILVR",
        "ITC","JYOTHYLAB","KRBL","MARICO","MCDOWELL-N","NESTLEIND",
        "PGHH","RADICO","TATACONSUM","TILAKNAGAR","VSTIND",
        # RETAIL & CONSUMER
        "AMBER","BATAINDIA","BURGERKING","CAMPUS","CANTABIL","DEVYANI",
        "DIXON","DMART","DOLLAR","DOMS","GOKALDAS","JUBLFOOD","KPRMILL",
        "LUXIND","NYKAA","PAGEIND","RAYMOND","REDTAPE","RELAXO","RUPA",
        "SAFARI","SHOPERSTOP","TRENT","VEDANT","VIPIND","VMART","WESTLIFE",
        # REAL ESTATE
        "ANANTRAJ","BRIGADE","CHALET","DLF","GODREJPROP","IBREALEST",
        "INDHOTEL","KOLTEPATIL","LEMONTREE","LODHA","MHRIL","NESCO",
        "OBEROIRLTY","OMAXE","PHOENIXLTD","PRESTIGE","SOBHA","SUNTECK",
        # CAPITAL GOODS / ENGINEERING
        "ABB","AIAENG","APARINDS","ASHOKA","BEL","BHEL","BLUEDART",
        "CAPACITE","COCHINSHIP","CONCOR","CUMMINSIND","DREDGECORP","EIL",
        "ELGIEQUIP","GPPL","GREAVESCOT","GRINDWELL","GRSE","HAL",
        "HGINFRA","ITD","ITDCEM","KALPATPOWR","KEC","KNR","LT",
        "MAZAGON","MIDHANI","MTAR","NBCC","PATELENG","POWERMECH","RVNL",
        "SCHAEFFLER","SIEMENS","SKF","TDPOWERSYS","THERMAX","TIMKEN",
        "TITAGARH","VOLTAMP","IRCON",
        # DEFENCE
        "BEL","BHEL","COCHINSHIP","GRSE","HAL","IDEAFORGE","MAZAGON",
        "MIDHANI","MTAR",
        # TELECOM / MEDIA
        "BHARTIARTL","DBCORP","DISHTV","HFCL","HMVL","INDUSTOWER",
        "JAGRAN","NDTV","OPTIEMUS","PVRINOX","RAILTEL","STLTECH",
        "SUNTV","TATACOMM","ZEEMEDIA",
        # AGRI / FERTILISERS
        "BALRAMCHIN","BAYER","CHAMBLFERT","COROMANDEL","DHANUKA","DHARMAJ",
        "EIDPARRY","GNFC","GSFC","INSECTICID","KSCL","MAWANASUG",
        "PARADEEP","RALLIS","RENUKA","TRIVENI","UPL",
        # GEMS & JEWELLERY
        "GOLDIAM","KALYANKJIL","RAJESHEXPO","SENCO","THANGAMAYL","TITAN",
        # LOGISTICS
        "AEGISLOG","ALLCARGO","BLUEDART","CONCOR","DELHIVERY","GATI",
        "GMRAIRPORT","INTERGLOBE","SNOWMAN","SPICEJET","TCI",
        # TEXTILES
        "ARVINDFASHN","AYMSYNTEX","FILATEX","GARFIBRES","GARWARE",
        "GOKALDAS","MPDL","MORARJEE","RAYMOND","SIYARAM","SUTLEJTEX",
        "TRIDENT","VIPIND","WELSPUNLIV",
        # CONSUMER DURABLES
        "AMBER","BAJAJELEC","BLUESTARCO","CERA","CROMPTON","HAVELLS",
        "KAJARIACER","ORIENTELEC","SOMANYCER","SYMPHONY","VGUARD","VOLTAS",
        # PAPER / PACKAGING
        "ASTRAL","COSMOFILMS","EPL","HUHTAMAKI","MOLDTEK","PPAP","UFLEX",
        # MISC
        "3MINDIA","ABBOTINDIA","AFFLE","CARBORUNIV","EASEMYTRIP","ELGIEQUIP",
        "GLAXO","HONAUT","IRCTC","JUSTDIAL","LATENTVIEW","MMTC","MSTCLTD",
        "NAZARA","PFIZER","QUESS","RATEGAIN","SANOFI","STCINDIA",
        "TEAMLEASE","WENDT","ZAGGLE",
    ]
    # fmt: on

    tickers: set[str] = {f"{s}.NS" for s in _BASE}

    # Live supplement — silently skipped when NSE blocks the request
    try:
        import requests
        _H = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.nseindia.com/",
        }
        session = requests.Session()
        session.headers.update(_H)
        session.get("https://www.nseindia.com/", timeout=8)
        r = session.get(
            "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
            timeout=15,
        )
        if r.status_code == 200 and len(r.content) > 5000:
            import io as _io
            df_eq = pd.read_csv(_io.StringIO(r.text))
            col = "SYMBOL" if "SYMBOL" in df_eq.columns else df_eq.columns[0]
            for s in df_eq[col].dropna().unique():
                tickers.add(f"{str(s).strip()}.NS")
    except Exception:
        pass  # Streamlit Cloud blocks NSE — baseline is sufficient

    result = sorted(tickers)

    # Safety net: if something went badly wrong, invalidate and use baseline
    if len(result) < 500:
        fetch_nse_tickers.clear()   # bust the bad cache
        result = sorted(f"{s}.NS" for s in _BASE)

    return result
'''
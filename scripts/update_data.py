"""
scripts/update_data.py — Credit Risk Engine
──────────────────────────────────────────
Fetches live market data for 500 tickers and writes market_data.csv.
GitHub Actions runs this every weekday at 06:00 UTC.
Estimated runtime: ~33 minutes (500 tickers x 4s). Within 6h job limit.
"""

import time, logging, signal, numpy as np, pandas as pd, yfinance as yf
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(__file__).parent.parent / "market_data.csv"

TICKERS = [
    "AAPL","MSFT","JPM","JNJ","PG","F","M","CCL","AAL","AMC",
    "C","BAC","GS","MS","WFC","GOOGL","AMZN","META","NVDA","TSLA",
    "ORCL","CRM","ADBE","INTC","AMD","QCOM","TXN","CSCO","IBM","NOW",
    "AMAT","MU","LRCX","KLAC","SNPS","CDNS","PANW","CRWD","FTNT","NET",
    "DDOG","ZS","TEAM","HUBS","WDAY","SNOW","PLTR","APP","UBER","LYFT",
    "ABNB","DASH","SPOT","RBLX","U","HOOD","COIN","MSTR","BRK-B","V",
    "MA","AXP","BLK","SCHW","USB","PNC","TFC","COF","DFS","SYF",
    "AIG","MET","PRU","ALL","TRV","PGR","CB","MMC","AON","ICE",
    "CME","SPGI","MCO","MSCI","FI","FIS","GPN","WEX","UNH","LLY",
    "ABBV","MRK","PFE","TMO","ABT","DHR","BMY","AMGN","GILD","ISRG",
    "SYK","BSX","HCA","ELV","CI","HUM","CNC","MOH","ZBH","BAX",
    "BDX","EW","HOLX","IDXX","IQV","MCK","COR","CAH","WMT","COST",
    "HD","LOW","TGT","MCD","SBUX","NKE","TJX","BKNG","EXPE","YUM",
    "QSR","DPZ","DKNG","LVS","WYNN","CZR","MGM","KO","PEP","MDLZ",
    "GIS","K","CAG","SJM","HRL","TSN","MKC","CLX","CL","KMB",
    "CHD","EL","ULTA","XOM","CVX","COP","SLB","EOG","MPC","PSX",
    "VLO","OXY","HAL","DVN","FANG","BKR","HES","MRO","APA","PXD",
    "CVI","CTRA","EQT","RRC","AR","NOV","BA","CAT","GE","HON",
    "RTX","LMT","UPS","FDX","DE","MMM","NOC","GD","HII","LHX",
    "TDG","HWM","TXT","WWD","AXON","IR","ITW","EMR","ETN","ROK",
    "AME","PH","DOV","FAST","GWW","MSC","CTAS","VRSK","BR","PAYC",
    "ADP","PAYX","NEE","DUK","SO","D","AEP","EXC","XEL","ES",
    "ED","PCG","EIX","WEC","DTE","ETR","FE","AES","NRG","VST",
    "PLD","AMT","EQIX","SPG","O","WELL","DLR","PSA","EXR","VICI",
    "WPC","NNN","ARE","BXP","KIM","UAL","DAL","ALK","NCLH","RCL",
    "HLT","MAR","H","T","VZ","TMUS","LUMN","FTR","DIS","NFLX",
    "WBD","FOX","PARA","CMCSA","CHTR","EA","TTWO","ATVI","LYV","LIN",
    "APD","ECL","DD","DOW","LYB","PPG","SHW","NEM","FCX","NUE",
    "STLD","CLF","X","AA","CF","MOS","IFF","ALB","MP","BIIB",
    "REGN","VRTX","MRNA","BNTX","ALNY","SGEN","INCY","EXAS","IONS","RARE",
    "FATE","TSM","AVGO","ASML","MRVL","MPWR","ON","WOLF","NXPI","STM",
    "SWKS","QRVO","ENTG","MKSI","SAP","INTU","ADSK","ANSS","PTC","PRGS",
    "GWRE","VEEV","TTD","ROKU","ZM","DOCN","BOX","SMAR","DELL","HPQ",
    "HPE","WDC","STX","NTAP","PSTG","SMCI","VIAV","CIEN","JNPR","FFIV",
    "AKAM","LDOS","SAIC","BAH","CTSH","ACN","WIT","INFY","WIX","SHOP",
    "SQ","PYPL","AFRM","SOFI","NU","MELI","SE","GRAB","BIDU","JD",
    "PDD","BABA","TCOM","NTES","ALLY","SLM","NAVI","OMF","CACC","TREE",
    "LC","LPLA","RJF","SF","HLI","LAZ","EVR","PJT","MKTX","CBOE",
    "NDAQ","IEX","BEN","IVZ","TROW","WTW","AFG","RLI","CINF","HIG",
    "L","MKL","WRB","ERIE","RE","RNR","DXCM","PODD","ALGN","TECH",
    "XRAY","HSIC","PRGO","MYL","AGN","JAZZ","UTHR","BMRN","SRPT","PCVX",
    "KRYS","SMMT","LEGN","CRVS","PHAT","RCKT","ETSY","W","CHWY","PETS",
    "PRTS","AN","KMX","PAG","LAD","GPC","AAP","AZO","ORLY","BBY",
    "GPS","PVH","RL","HBI","VFC","TPR","CPRI","KSS","JWN","DDS",
    "BJ","SFM","GO","CASY","CHEF","CARR","TT","JCI","OTIS","ALLE",
    "MAS","SWK","FBHS","NVT","REXR","GNRC","HUBB","ACHR","JOBY","LILM",
    "SPCE","RKT","OPEN","RDFN","Z","COOP","TRGP","WES","AM","HESM",
    "CQPX","LNG","ET","EPD","MMP","PAA","PAGP","KMI","WMB","OKE",
    "TALO","SM","CRC","VTLE","FSLR","ENPH","SEDG","RUN","NOVA","ARRY",
    "BE","PLUG","BLDP","HYZN","CHPT","EVGO","BLNK","CEG","EQR","AVB",
]

seen = set(); TICKERS = [t for t in TICKERS if not (t in seen or seen.add(t))]
logger.info("Total unique tickers: %d", len(TICKERS))

SECTOR_LGD = {
    "Financial Services":0.55,"Financials":0.55,"Banks":0.55,
    "Energy":0.45,"Industrials":0.40,"Consumer Cyclical":0.40,
    "Consumer Defensive":0.35,"Technology":0.35,"Healthcare":0.35,
    "Communication Services":0.40,"Utilities":0.40,
    "Real Estate":0.50,"Basic Materials":0.45,"default":0.40,
}
def get_lgd(sector):
    for k,v in SECTOR_LGD.items():
        if k.lower() in sector.lower() or sector.lower() in k.lower(): return v
    return 0.40

SHORT_KEYS=["Current Debt","Short Term Debt","CurrentDebt","Short Long Term Debt",
    "ShortTermDebt","Current Debt And Capital Lease Obligation"]
LONG_KEYS=["Long Term Debt","LongTermDebt",
    "Long Term Debt And Capital Lease Obligation","Long-Term Debt"]

def _from_sheet(sheet):
    if sheet is None or sheet.empty: return 0.0
    s,l=0.0,0.0
    for idx in sheet.index:
        istr=str(idx).strip()
        try:
            v=float(sheet.loc[idx].iloc[0])
            if np.isnan(v): continue
        except: continue
        if any(k.lower() in istr.lower() for k in SHORT_KEYS): s=max(s,v)
        if any(k.lower() in istr.lower() for k in LONG_KEYS): l=max(l,v)
    return s+l

def get_debt(t,info):
    for fn in [lambda:t.quarterly_balance_sheet,lambda:t.balance_sheet]:
        try:
            d=_from_sheet(fn())
            if d>0: return d
        except: pass
    return float(info.get("totalDebt") or 0)

FETCH_TIMEOUT_SEC = 30  # hard wall-clock timeout per ticker

class _Timeout(Exception): pass

def _timeout_handler(signum, frame):
    raise _Timeout()

def fetch_one(ticker):
    logger.info("Fetching %-8s...", ticker)

    # Set a hard 30-second alarm — catches hangs on history() or info()
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(FETCH_TIMEOUT_SEC)

    try:
        return _fetch_one_inner(ticker)
    except _Timeout:
        logger.error("  TIMEOUT after %ds: %s (likely delisted/zombie ticker)", FETCH_TIMEOUT_SEC, ticker)
        return None
    finally:
        signal.alarm(0)  # always cancel alarm


def _fetch_one_inner(ticker):
    for attempt in range(1,4):
        try:
            t=yf.Ticker(ticker); info=t.info or {}
            if not info.get("marketCap"):
                logger.warning("  %s empty info attempt %d",ticker,attempt)
                time.sleep(attempt*5); continue
            # Detect delisted: quoteType will be NONE or missing for acquired/delisted tickers
            quote_type = info.get("quoteType", "")
            if quote_type in ("", "NONE") or info.get("regularMarketPrice") is None:
                logger.warning("  %s appears delisted/acquired (quoteType=%r) — skipping", ticker, quote_type)
                return None
            name=info.get("longName") or info.get("shortName") or ticker
            sector=info.get("sector") or "Unknown"
            mktcap=float(info.get("marketCap") or 0)
            debt=get_debt(t,info)
            hist=t.history(period="1y",auto_adjust=True)
            if hist.empty or len(hist)<20:
                logger.warning("  %s insufficient history",ticker); time.sleep(attempt*5); continue
            closes=hist["Close"].dropna().values
            vol=float(np.std(np.diff(np.log(closes)),ddof=1)*np.sqrt(252))
            today=datetime.now(timezone.utc).strftime("%Y-%m-%d")
            logger.info("  %-8s cap=$%7.1fB debt=$%6.1fB vol=%5.1f%% %s",
                ticker,mktcap/1e9,debt/1e9,vol*100,sector)
            return {"ticker":ticker,"company_name":name,"sector":sector,
                    "market_cap":mktcap,"total_debt":debt,
                    "equity_volatility":round(vol,6),"lgd":get_lgd(sector),
                    "last_updated":today,"data_source":"yfinance"}
        except Exception as e:
            logger.warning("  %s attempt %d error: %s",ticker,attempt,e)
            time.sleep(attempt*5)
    logger.error("  FAILED: %s",ticker)
    return None

def main():
    logger.info("="*60)
    logger.info("Credit Risk Engine — Market Data Update")
    logger.info("Tickers: %d | Output: %s",len(TICKERS),OUTPUT_PATH)
    logger.info("Estimated time: ~%d minutes",(len(TICKERS)*4)//60)
    logger.info("="*60)

    existing={}
    if OUTPUT_PATH.exists():
        try:
            df_old=pd.read_csv(OUTPUT_PATH)
            for _,row in df_old.iterrows(): existing[row["ticker"]]=row.to_dict()
            logger.info("Loaded %d existing rows as fallback",len(existing))
        except Exception as e: logger.warning("Could not load existing CSV: %s",e)

    rows,failed=[],[]
    for i,ticker in enumerate(TICKERS,1):
        logger.info("[%3d/%d]",i,len(TICKERS))
        result=fetch_one(ticker)
        if result: rows.append(result)
        elif ticker in existing:
            old=existing[ticker].copy()
            old["data_source"]=f"cached — fetch failed {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
            rows.append(old); logger.info("  %s: using cached data",ticker)
        else: failed.append(ticker)
        time.sleep(3)

    df=pd.DataFrame(rows)
    cols=["ticker","company_name","sector","market_cap","total_debt",
          "equity_volatility","lgd","last_updated","data_source"]
    df=df[[c for c in cols if c in df.columns]]
    df.to_csv(OUTPUT_PATH,index=False)
    logger.info("="*60)
    logger.info("Complete: %d rows written",len(df))
    if failed: logger.warning("No fallback data: %s",failed)
    logger.info("="*60)

if __name__=="__main__": main()

import json
import os
import time
from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd

CACHE_EXPIRY_SECONDS = 300  # 5 minutes cache for market data
_data_cache: Dict[str, dict] = {}

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
STOCK_DIR_PATH = os.path.join(DIR_PATH, "stock_directory.json")

try:
    from .stock_catalog import STOCK_CATALOG
except (ImportError, ValueError):
    try:
        from stock_catalog import STOCK_CATALOG
    except Exception:
        try:
            from backend.stock_catalog import STOCK_CATALOG
        except Exception:
            STOCK_CATALOG = []

def load_stock_directory() -> List[dict]:
    if STOCK_CATALOG:
        return list(STOCK_CATALOG)
    try:
        with open(STOCK_DIR_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading stock directory: {e}")
        return []

STOCKS_CATALOG = load_stock_directory()

def search_stocks(query: str) -> List[dict]:
    """Search stocks by name or ticker."""
    catalog = load_stock_directory()
    q = query.strip().upper()
    if not q:
        return catalog[:15]
    
    matches = []
    
    # Check if query is an alias
    alias_sym = TICKER_ALIASES.get(q) or TICKER_ALIASES.get(f"{q}.NS")
    if alias_sym:
        for s in catalog:
            if s["symbol"] == alias_sym and s not in matches:
                matches.append(s)
                
    # Exact ticker match first
    for s in catalog:
        if s["ticker"] == q or s["symbol"] == q:
            if s not in matches:
                matches.append(s)
            
    # Then prefix / substring matches
    for s in catalog:
        if s not in matches:
            if q in s["ticker"] or q in s["name"].upper() or q in s["symbol"].upper():
                matches.append(s)
                
    # If no catalog match and query looks like a ticker, suggest as direct custom NSE symbol
    if not matches and len(q) >= 2:
        custom_sym = q if "." in q or q.startswith("^") else f"{q}.NS"
        matches.append({
            "symbol": custom_sym,
            "name": f"{q} (Direct NSE/BSE Symbol)",
            "ticker": q,
            "sector": "Custom / Other"
        })
        
    return matches[:15]

TICKER_ALIASES = {
    "TATAMOTORS": "TMPV.NS",
    "TATAMOTORS.NS": "TMPV.NS",
    "TATAMOTORS.BO": "TMPV.BO",
    "ZOMATO": "ETERNAL.NS",
    "ZOMATO.NS": "ETERNAL.NS",
    "ZOMATO.BO": "ETERNAL.BO",
}

def normalize_symbol(user_sym: str) -> str:
    """Normalize input ticker to Yahoo finance format with alias support."""
    s = user_sym.strip().upper()
    if s in TICKER_ALIASES:
        return TICKER_ALIASES[s]
    base = s.replace(".NS", "").replace(".BO", "")
    if base in TICKER_ALIASES:
        return TICKER_ALIASES[base]
    if s.startswith("^") or "." in s or "=" in s:
        return s
    return f"{s}.NS"

def fetch_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch history DataFrame with caching.
    Returns DataFrame with datetime index and 'Close' column.
    """
    symbol = normalize_symbol(symbol)
    cache_key = f"{symbol}_{period}"
    now = time.time()
    
    if cache_key in _data_cache:
        entry = _data_cache[cache_key]
        if now - entry["timestamp"] < CACHE_EXPIRY_SECONDS:
            return entry["data"].copy()
            
    # Valid yfinance periods: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    period_map = {
        "1m": "1mo",
        "1mo": "1mo",
        "6m": "6mo",
        "6mo": "6mo",
        "1y": "1y",
        "3y": "5y",
        "5y": "5y",
        "max": "max"
    }
    yf_period = period_map.get(period.lower(), "1y")
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=yf_period, interval="1d", auto_adjust=True)
    
    if df.empty:
        # Check alias
        base = symbol.replace(".NS", "").replace(".BO", "")
        if base in TICKER_ALIASES:
            alt_sym = TICKER_ALIASES[base]
            if alt_sym != symbol:
                df = yf.Ticker(alt_sym).history(period=yf_period, interval="1d", auto_adjust=True)
                if not df.empty:
                    symbol = alt_sym

    if df.empty:
        # Retry with .BO if .NS was attempted
        if symbol.endswith(".NS"):
            bse_sym = symbol.replace(".NS", ".BO")
            df = yf.Ticker(bse_sym).history(period=yf_period, interval="1d", auto_adjust=True)
            if not df.empty:
                symbol = bse_sym
                
    if df.empty:
        raise ValueError(f"No price data available for symbol '{symbol}'")
        
    # Standardize index timezone
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df.index = pd.to_datetime(df.index).normalize()
    
    # Filter 3y if requested
    if period.lower() in ("3y", "3yr"):
        start_date = pd.Timestamp.now() - pd.DateOffset(years=3)
        df = df[df.index >= start_date]

    # Save to cache
    _data_cache[cache_key] = {
        "timestamp": now,
        "data": df
    }
    
    return df.copy()

def get_company_info(symbol: str) -> dict:
    """Get company metadata and friendly name."""
    norm = normalize_symbol(symbol)
    # Check directory
    for item in STOCKS_CATALOG:
        if item["symbol"].upper() == norm.upper() or item["ticker"].upper() == symbol.strip().upper():
            return {
                "symbol": item["symbol"],
                "name": item["name"],
                "ticker": item["ticker"],
                "sector": item.get("sector", "Equities")
            }
            
    # Try fetching fast info from yfinance
    try:
        t = yf.Ticker(norm)
        info = getattr(t, "fast_info", None)
        long_name = getattr(t, "info", {}).get("longName", norm)
        currency = getattr(info, "currency", "INR")
        return {
            "symbol": norm,
            "name": long_name or norm,
            "ticker": norm.replace(".NS", "").replace(".BO", ""),
            "sector": "Indian Equities"
        }
    except Exception:
        return {
            "symbol": norm,
            "name": norm,
            "ticker": norm,
            "sector": "Equities"
        }

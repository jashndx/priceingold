import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure current directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .stock_data import search_stocks, load_stock_directory
    from .gold_service import compute_stock_in_gold
except (ImportError, ValueError):
    from stock_data import search_stocks, load_stock_directory
    from gold_service import compute_stock_in_gold

app = FastAPI(
    title="Indian Equities in Gold (mg/share) — Research Tool",
    description="Research tool for analyzing Indian stock prices denominated strictly in milligrams of 24K gold."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/api/health")
def api_health():
    return {"status": "ok"}

@app.get("/search")
@app.get("/api/search")
def api_search(q: str = Query("", description="Search ticker or company name")):
    try:
        results = search_stocks(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/popular")
@app.get("/api/popular")
def api_popular():
    try:
        popular_symbols = [
            "^NSEI", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
            "TMPV.NS", "ITC.NS", "TITAN.NS", "HAL.NS", "ETERNAL.NS"
        ]
        catalog = load_stock_directory()
        popular_list = []
        catalog_map = {s["symbol"]: s for s in catalog}
        for sym in popular_symbols:
            if sym in catalog_map:
                popular_list.append(catalog_map[sym])
        return {"popular": popular_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stock-gold")
@app.get("/api/stock-gold")
def api_stock_gold(
    symbol: str = Query("RELIANCE.NS", description="Stock symbol"),
    period: str = Query("1y", description="Timeframe: 1m, 6m, 1y, 3y, 5y, max")
):
    try:
        data = compute_stock_in_gold(symbol, period=period)
        return data
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data retrieval failed: {str(e)}")

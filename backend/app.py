import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.stock_data import search_stocks, load_stock_directory
from backend.gold_service import compute_stock_in_gold

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

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/api/search")
def api_search(q: str = Query("", description="Search ticker or company name")):
    """Search for Indian stocks by ticker or company name."""
    try:
        results = search_stocks(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/popular")
def api_popular():
    """Return popular Indian stocks for quick selection."""
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

@app.get("/api/stock-gold")
def api_stock_gold(
    symbol: str = Query("RELIANCE.NS", description="Stock symbol"),
    period: str = Query("1y", description="Timeframe: 1m, 6m, 1y, 3y, 5y, max")
):
    """Fetch stock price in milligrams of 24K Gold."""
    try:
        data = compute_stock_in_gold(symbol, period=period)
        return data
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data retrieval failed: {str(e)}")

# Mount static frontend
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Server active. Frontend directory not found."}

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)

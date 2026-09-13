import pandas as pd
import numpy as np
from typing import Dict, Any
try:
    from .stock_data import fetch_history, normalize_symbol, get_company_info
except (ImportError, ValueError):
    from stock_data import fetch_history, normalize_symbol, get_company_info

TROY_OUNCE_TO_GRAMS = 31.1034768

def get_gold_inr_series(period: str = "1y") -> pd.DataFrame:
    """
    Fetch Gold Futures in USD (GC=F) and USD/INR (INR=X)
    and compute Gold Spot INR price per gram.
    """
    gold_df = fetch_history("GC=F", period=period)
    inr_df = fetch_history("INR=X", period=period)
    
    # Extract close prices
    gold_close = gold_df["Close"]
    inr_close = inr_df["Close"]
    
    # Merge on date index
    combined = pd.DataFrame({"gold_usd": gold_close, "usdinr": inr_close}).dropna()
    
    # Calculate spot gold price per gram in INR
    combined["gold_inr_per_gram"] = (combined["gold_usd"] * combined["usdinr"]) / TROY_OUNCE_TO_GRAMS
    combined["gold_inr_10g"] = combined["gold_inr_per_gram"] * 10.0
    
    return combined

def compute_stock_in_gold(stock_symbol: str, period: str = "1y", benchmark: str = "spot") -> Dict[str, Any]:
    """
    Computes real stock price in terms of Gold.
    Returns metadata, summary metrics, and synchronized time-series.
    """
    norm_symbol = normalize_symbol(stock_symbol)
    company_info = get_company_info(norm_symbol)
    
    # 1. Fetch stock history
    stock_df = fetch_history(norm_symbol, period=period)
    
    # 2. Fetch gold history
    gold_df = get_gold_inr_series(period=period)
    
    # 3. Synchronize on dates (forward fill minor trading calendar holiday mismatches)
    merged = pd.merge(
        stock_df[["Close"]].rename(columns={"Close": "stock_inr"}),
        gold_df[["gold_inr_per_gram", "gold_inr_10g"]],
        left_index=True,
        right_index=True,
        how="inner"
    )
    
    if merged.empty or len(merged) < 2:
        # Try outer join with ffill if holiday mismatch
        merged = pd.merge(
            stock_df[["Close"]].rename(columns={"Close": "stock_inr"}),
            gold_df[["gold_inr_per_gram", "gold_inr_10g"]],
            left_index=True,
            right_index=True,
            how="outer"
        ).sort_index().ffill().dropna()
        
    if merged.empty:
        raise ValueError(f"Could not align price series for {norm_symbol} and Gold.")

    # 4. Calculate Key Metrics
    merged["stock_in_gold_grams"] = merged["stock_inr"] / merged["gold_inr_per_gram"]
    merged["stock_in_gold_mg"] = merged["stock_in_gold_grams"] * 1000.0
    merged["shares_per_10g"] = 10.0 / merged["stock_in_gold_grams"]
    
    # Normalized performance (Base 100)
    start_stock = merged["stock_inr"].iloc[0]
    start_gold = merged["gold_inr_per_gram"].iloc[0]
    start_ratio = merged["stock_in_gold_grams"].iloc[0]
    start_gold_per_mg = start_gold / 1000.0
    
    merged["indexed_stock_inr"] = (merged["stock_inr"] / start_stock) * 100.0
    merged["indexed_gold_inr"] = (merged["gold_inr_per_gram"] / start_gold) * 100.0
    merged["indexed_stock_gold"] = (merged["stock_in_gold_grams"] / start_ratio) * 100.0
    
    # Real INR: purchasing power in constant Rupees at period start
    merged["real_inr"] = merged["stock_in_gold_mg"] * start_gold_per_mg

    # 5. Summary values
    latest = merged.iloc[-1]
    first = merged.iloc[0]
    
    curr_stock_inr = float(latest["stock_inr"])
    curr_gold_per_gram = float(latest["gold_inr_per_gram"])
    curr_gold_10g = float(latest["gold_inr_10g"])
    curr_gold_grams = float(latest["stock_in_gold_grams"])
    curr_gold_mg = float(latest["stock_in_gold_mg"])
    curr_shares_10g = float(latest["shares_per_10g"])
    
    # Returns over the period
    stock_return_pct = float(((latest["stock_inr"] - first["stock_inr"]) / first["stock_inr"]) * 100.0)
    gold_return_pct = float(((latest["gold_inr_per_gram"] - first["gold_inr_per_gram"]) / first["gold_inr_per_gram"]) * 100.0)
    gold_denominated_return_pct = float(((latest["stock_in_gold_grams"] - first["stock_in_gold_grams"]) / first["stock_in_gold_grams"]) * 100.0)
    
    # Real alpha: difference between stock return in gold vs 0%, or stock vs gold
    real_alpha = gold_denominated_return_pct
    
    # Craft insightful verdict
    if real_alpha >= 10.0:
        verdict_status = "TRUE_WEALTH_CREATOR"
        verdict_title = "Outperforming Gold (Real Wealth Creator)"
        verdict_badge = "success"
        verdict_text = (
            f"Over this period, {company_info['ticker']} delivered a +{gold_denominated_return_pct:.1f}% real gain in Gold terms, "
            f"easily beating currency inflation (+{gold_return_pct:.1f}% Gold rise)."
        )
    elif real_alpha >= 0.0:
        verdict_status = "PRESERVING_WEALTH"
        verdict_title = "Holding Purchasing Power"
        verdict_badge = "neutral"
        verdict_text = (
            f"{company_info['ticker']} has kept pace with Gold (+{gold_denominated_return_pct:.1f}% real change), "
            f"preserving purchasing power against currency debasement."
        )
    else:
        verdict_status = "PURCHASING_POWER_LOSS"
        verdict_title = "Losing Purchasing Power to Gold"
        verdict_badge = "warning"
        verdict_text = (
            f"Although {company_info['ticker']} moved {stock_return_pct:+.1f}% in nominal INR, "
            f"it lost {abs(gold_denominated_return_pct):.1f}% of its real value in Gold terms."
        )

    # 6. Format time-series for frontend charts
    time_series = []
    for idx, row in merged.iterrows():
        time_series.append({
            "date": idx.strftime("%Y-%m-%d"),
            "stock_inr": round(float(row["stock_inr"]), 2),
            "real_inr": round(float(row["real_inr"]), 2),
            "gold_inr_per_gram": round(float(row["gold_inr_per_gram"]), 2),
            "gold_inr_10g": round(float(row["gold_inr_10g"]), 2),
            "stock_in_gold_grams": round(float(row["stock_in_gold_grams"]), 5),
            "stock_in_gold_mg": round(float(row["stock_in_gold_mg"]), 2),
            "shares_per_10g": round(float(row["shares_per_10g"]), 2),
            "indexed_stock_inr": round(float(row["indexed_stock_inr"]), 2),
            "indexed_gold_inr": round(float(row["indexed_gold_inr"]), 2),
            "indexed_stock_gold": round(float(row["indexed_stock_gold"]), 2),
        })

    return {
        "company": company_info,
        "period": period,
        "latest": {
            "stock_inr": round(curr_stock_inr, 2),
            "real_inr": round(float(latest["real_inr"]), 2),
            "start_stock_inr": round(float(first["stock_inr"]), 2),
            "gold_inr_per_gram": round(curr_gold_per_gram, 2),
            "gold_inr_10g": round(curr_gold_10g, 2),
            "stock_in_gold_grams": round(curr_gold_grams, 5),
            "stock_in_gold_mg": round(curr_gold_mg, 2),
            "shares_per_10g": round(curr_shares_10g, 2),
            "start_shares_per_10g": round(float(first["shares_per_10g"]), 2),
            "start_gold_grams": round(float(first["stock_in_gold_grams"]), 5),
            "start_gold_mg": round(float(first["stock_in_gold_mg"]), 2),
            "start_date": first.name.strftime("%Y-%m-%d"),
            "end_date": latest.name.strftime("%Y-%m-%d"),
            "stock_return_pct": round(stock_return_pct, 2),
            "gold_return_pct": round(gold_return_pct, 2),
            "gold_denominated_return_pct": round(gold_denominated_return_pct, 2),
            "real_alpha": round(real_alpha, 2),
        },
        "verdict": {
            "status": verdict_status,
            "title": verdict_title,
            "badge": verdict_badge,
            "text": verdict_text,
        },
        "series": time_series
    }

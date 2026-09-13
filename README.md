# Indian Equities Priced in Gold (mg/share) — Research Tool

A clean, minimalist research tool for evaluating Indian stocks (NSE/BSE) priced strictly in **milligrams of 24K Gold per share (mg/share)**.

---

## Core Purpose

Evaluating stock returns solely in nominal Indian Rupees (INR) ignores the impact of monetary expansion and currency debasement. 

By measuring the price of 1 share strictly in **milligrams of physical 24K Gold**:
$$\text{Price in Gold (mg/share)} = \frac{\text{Stock Price (INR)}}{\text{24K Gold Spot Price (INR/gram)}} \times 1,000$$

You can evaluate whether a company has truly expanded its purchasing power over time relative to sound monetary gold.

---

## Features

1. **Simple, Professional Interface**:
   - Clean dark-slate financial research design without marketing branding or decorative clutter.
   - Live 24K Gold Spot benchmark (INR/gram).
2. **Strict mg/share Focus**:
   - Live and historical trajectory of **mg of 24K Gold per Share**.
   - Net change in mg/share and percentage real return in gold terms.
   - Benchmark comparison with nominal INR stock price and domestic gold spot.
3. **Two Distinct Graph Views**:
   - **`mg / share`**: Plots the stock's historical price in milligrams of 24K pure gold per share.
   - **`Real INR`**: Plots the **Real Price (Constant INR deflated by Gold)** alongside the **Nominal Stock Price (INR)**, immediately revealing the purchasing power gap.
   - Timeframe filters: `1M`, `6M`, `1Y`, `3Y`, `5Y`, `MAX`.
4. **Fast Autocomplete**:
   - Pre-indexed catalog of Indian stocks (NIFTY 50, NIFTY 500) and support for any NSE/BSE ticker.

---

## Launching the Tool

### Windows (One-Click)
Double-click `run.bat` in this directory. It will start the server and open `http://localhost:8000` in your browser.

### Command Line
```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Then visit `http://localhost:8000`.

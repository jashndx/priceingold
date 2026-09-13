// Research Tool Logic - Indian Equities in Gold (mg/share)
let currentSymbol = "RELIANCE.NS";
let currentPeriod = "1y";
let currentChartType = "mg_share"; // "mg_share" or "real_inr"
let currentData = null;
let chartInstance = null;
let searchDebounceTimer = null;

// DOM Elements
const searchInput = document.getElementById("stockSearchInput");
const searchDropdown = document.getElementById("searchDropdown");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const popularPillsContainer = document.getElementById("popularPills");
const loadingIndicator = document.getElementById("loadingIndicator");
const headerGoldSpot = document.getElementById("headerGoldSpot");

// Header info
const companyNameEl = document.getElementById("companyName");
const companyTickerEl = document.getElementById("companyTicker");
const stockMetaEl = document.getElementById("stockMeta");
const chartDateRangeEl = document.getElementById("chartDateRange");
const chartHeading = document.getElementById("chartHeading");
const chartSubheading = document.getElementById("chartSubheading");

// Metric elements
const metricGoldMg = document.getElementById("metricGoldMg");
const metricGoldMgDelta = document.getElementById("metricGoldMgDelta");
const metricRealReturn = document.getElementById("metricRealReturn");
const metricRealVerdict = document.getElementById("metricRealVerdict");
const metricNominalInr = document.getElementById("metricNominalInr");
const metricNominalReturn = document.getElementById("metricNominalReturn");
const metricGoldPerGram = document.getElementById("metricGoldPerGram");
const metricGoldReturn = document.getElementById("metricGoldReturn");

// Table
const tableBody = document.getElementById("tableBody");
const thStartDate = document.getElementById("thStartDate");
const thEndDate = document.getElementById("thEndDate");

// Chart Canvas
const chartCanvas = document.getElementById("mainChart");

// Modal elements
const infoModal = document.getElementById("infoModal");
const openModalBtn = document.getElementById("openModalBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const dismissModalBtn = document.getElementById("dismissModalBtn");

document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  setupModal();
  loadPopularStocks();
  fetchStockInGold(currentSymbol, currentPeriod);
});

function openModal() {
  if (infoModal) infoModal.style.display = "flex";
}

function closeModal() {
  if (infoModal) infoModal.style.display = "none";
  localStorage.setItem("hasSeenGoldIntro", "true");
}

function setupModal() {
  if (openModalBtn) openModalBtn.addEventListener("click", openModal);
  if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
  if (dismissModalBtn) dismissModalBtn.addEventListener("click", closeModal);
  
  if (infoModal) {
    infoModal.addEventListener("click", (e) => {
      if (e.target === infoModal) closeModal();
    });
  }

  // Show automatically on first visit
  if (!localStorage.getItem("hasSeenGoldIntro")) {
    setTimeout(() => {
      openModal();
    }, 450);
  }
}

function setupEventListeners() {
  searchInput.addEventListener("input", (e) => {
    const val = e.target.value;
    clearSearchBtn.style.display = val ? "block" : "none";
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      handleSearch(val);
    }, 200);
  });

  searchInput.addEventListener("focus", () => {
    if (searchInput.value.trim().length >= 1) {
      handleSearch(searchInput.value);
    }
  });

  clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    clearSearchBtn.style.display = "none";
    searchDropdown.style.display = "none";
  });

  document.addEventListener("click", (e) => {
    if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
      searchDropdown.style.display = "none";
    }
  });

  // Timeframe buttons
  document.querySelectorAll(".tf-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentPeriod = btn.dataset.period;
      fetchStockInGold(currentSymbol, currentPeriod);
    });
  });

  // Chart view toggle (mg_share vs real_inr)
  document.querySelectorAll(".chart-toggle-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".chart-toggle-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentChartType = btn.dataset.chart;
      if (currentData && currentData.series) {
        renderChart(currentData.series);
      }
    });
  });
}

// Universal API Fetcher supporting both /api/... and /...
async function apiFetch(path) {
  try {
    const res = await fetch(`/api${path}`);
    if (res.ok) return res;
  } catch (e) {}
  return await fetch(path);
}

// Load popular stocks
async function loadPopularStocks() {
  try {
    const res = await apiFetch("/popular");
    const json = await res.json();
    if (json.popular) {
      popularPillsContainer.innerHTML = "";
      json.popular.forEach(stock => {
        const pill = document.createElement("button");
        pill.className = `pill-btn ${stock.symbol === currentSymbol ? "active" : ""}`;
        pill.textContent = stock.ticker;
        pill.title = stock.name;
        pill.addEventListener("click", () => {
          selectStock(stock.symbol);
        });
        popularPillsContainer.appendChild(pill);
      });
    }
  } catch (err) {
    console.warn("Could not load popular stocks:", err);
  }
}

// Autocomplete search
async function handleSearch(query) {
  if (!query || query.trim().length < 1) {
    searchDropdown.style.display = "none";
    return;
  }
  try {
    const res = await apiFetch(`/search?q=${encodeURIComponent(query)}`);
    const json = await res.json();
    renderDropdown(json.results || []);
  } catch (err) {
    console.error("Search error:", err);
  }
}

function renderDropdown(items) {
  if (!items.length) {
    searchDropdown.innerHTML = `<div style="padding:10px 14px; color:var(--text-muted); font-size:12.5px;">No matching Indian equities found</div>`;
    searchDropdown.style.display = "block";
    return;
  }

  searchDropdown.innerHTML = "";
  items.forEach(item => {
    const row = document.createElement("div");
    row.className = "dropdown-item";
    row.innerHTML = `
      <div>
        <div class="item-name">${item.name}</div>
        <div class="item-sector">${item.sector || 'Equities'}</div>
      </div>
      <span class="item-ticker">${item.ticker}</span>
    `;
    row.addEventListener("click", () => {
      searchInput.value = item.name;
      searchDropdown.style.display = "none";
      selectStock(item.symbol);
    });
    searchDropdown.appendChild(row);
  });
  searchDropdown.style.display = "block";
}

function selectStock(symbol) {
  currentSymbol = symbol;
  document.querySelectorAll(".pill-btn").forEach(p => {
    p.classList.toggle("active", p.textContent === symbol.replace(".NS", ""));
  });
  fetchStockInGold(currentSymbol, currentPeriod);
}

// Fetch stock priced in gold
async function fetchStockInGold(symbol, period) {
  showLoading(true);
  try {
    const res = await apiFetch(`/stock-gold?symbol=${encodeURIComponent(symbol)}&period=${period}`);
    if (!res.ok) {
      let errDetail = "Failed to retrieve data";
      try {
        const err = await res.json();
        errDetail = err.detail || errDetail;
      } catch (e) {}
      throw new Error(errDetail);
    }
    const data = await res.json();
    currentData = data;
    updateUI(data);
  } catch (err) {
    alert(`Data error for ${symbol}: ${err.message}`);
  } finally {
    showLoading(false);
  }
}

function showLoading(isLoading) {
  loadingIndicator.style.display = isLoading ? "flex" : "none";
}

function formatINR(val) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(val);
}

function formatPct(val) {
  const sign = val > 0 ? "+" : "";
  return `${sign}${val.toFixed(2)}%`;
}

function updateUI(data) {
  const { company, latest, series } = data;

  // Header Benchmark
  headerGoldSpot.textContent = `${formatINR(latest.gold_inr_per_gram)} / g (₹${(latest.gold_inr_per_gram * 10).toLocaleString('en-IN', {maximumFractionDigits: 0})} / 10g)`;
  
  // Stock Identity
  companyNameEl.textContent = company.name;
  companyTickerEl.textContent = company.ticker;
  stockMetaEl.textContent = `NSE: ${company.symbol} • ${company.sector || 'Indian Equities'}`;
  chartDateRangeEl.textContent = `${latest.start_date} to ${latest.end_date}`;

  // Metric 1: Gold mg/share
  metricGoldMg.textContent = latest.stock_in_gold_mg.toFixed(2);
  const mgDelta = latest.stock_in_gold_mg - latest.start_gold_mg;
  const mgDeltaSign = mgDelta >= 0 ? "+" : "";
  metricGoldMgDelta.textContent = `${mgDeltaSign}${mgDelta.toFixed(2)} mg (${formatPct(latest.gold_denominated_return_pct)})`;

  // Metric 2: Real Return in Gold
  metricRealReturn.textContent = formatPct(latest.gold_denominated_return_pct);
  metricRealReturn.className = `metric-value ${latest.gold_denominated_return_pct >= 0 ? "positive" : "negative"}`;
  metricRealVerdict.textContent = latest.gold_denominated_return_pct >= 0 ? "Real purchasing power gained" : "Real purchasing power lost to Gold";

  // Metric 3: Nominal Price
  metricNominalInr.textContent = formatINR(latest.stock_inr);
  metricNominalReturn.textContent = `${formatPct(latest.stock_return_pct)} nominal`;
  metricNominalReturn.className = `metric-sub ${latest.stock_return_pct >= 0 ? "positive" : "negative"}`;

  // Metric 4: Gold per gram
  metricGoldPerGram.textContent = formatINR(latest.gold_inr_per_gram);
  metricGoldReturn.textContent = `${formatPct(latest.gold_return_pct)} gold rise`;

  // Table
  renderTable(data);

  // Chart
  renderChart(series);
}

function renderTable(data) {
  const { latest, series } = data;
  if (!series || !series.length) return;
  const first = series[0];
  const last = series[series.length - 1];

  thStartDate.textContent = `Start (${first.date})`;
  thEndDate.textContent = `Current (${last.date})`;

  const rows = [
    {
      indicator: "Price in Gold (24K)",
      start: `${first.stock_in_gold_mg.toFixed(2)} mg/share`,
      end: `${last.stock_in_gold_mg.toFixed(2)} mg/share`,
      change: formatPct(latest.gold_denominated_return_pct),
      impact: latest.gold_denominated_return_pct >= 0 ? "Purchasing power expanded" : "Purchasing power contracted"
    },
    {
      indicator: "Stock Nominal Price",
      start: formatINR(first.stock_inr),
      end: formatINR(last.stock_inr),
      change: formatPct(latest.stock_return_pct),
      impact: "Nominal Rupee change"
    },
    {
      indicator: "24K Gold (per gram)",
      start: formatINR(first.gold_inr_per_gram),
      end: formatINR(last.gold_inr_per_gram),
      change: formatPct(latest.gold_return_pct),
      impact: "Inflation / currency baseline"
    }
  ];

  tableBody.innerHTML = rows.map(r => `
    <tr>
      <td><strong>${r.indicator}</strong></td>
      <td>${r.start}</td>
      <td>${r.end}</td>
      <td class="${r.change.startsWith('+') ? 'positive' : 'negative'}"><strong>${r.change}</strong></td>
      <td style="color:var(--text-secondary); font-size:12px;">${r.impact}</td>
    </tr>
  `).join("");
}

function renderChart(series) {
  if (!series || !series.length || !currentData) return;

  const labels = series.map(d => d.date);

  if (chartInstance) {
    chartInstance.destroy();
  }

  let datasets = [];
  let yAxisCallback;
  let tooltipCallback;
  let showLegend = false;

  if (currentChartType === "mg_share") {
    chartHeading.textContent = `${currentData.company.ticker} in Gold (mg/share)`;
    chartSubheading.textContent = "Milligrams of 24K pure physical gold per share";

    datasets = [{
      label: `${currentData.company.ticker} (mg/share)`,
      data: series.map(d => d.stock_in_gold_mg),
      borderColor: "#d29922",
      backgroundColor: "rgba(210, 153, 34, 0.08)",
      borderWidth: 2,
      fill: true,
      tension: 0.1,
      pointRadius: series.length > 90 ? 0 : 2,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: "#e3b341"
    }];

    yAxisCallback = function(value) {
      return `${value.toFixed(1)} mg`;
    };

    tooltipCallback = {
      label: function(context) {
        const val = context.parsed.y;
        return ` Gold Price: ${val.toFixed(2)} mg/share`;
      },
      afterBody: function(tooltipItems) {
        const idx = tooltipItems[0].dataIndex;
        const pt = series[idx];
        return [
          ` Nominal Stock: ₹${pt.stock_inr.toLocaleString('en-IN')}`,
          ` 24K Gold Benchmark: ₹${pt.gold_inr_per_gram.toLocaleString('en-IN')}/g`
        ];
      }
    };
  } else {
    // "real_inr"
    chartHeading.textContent = `${currentData.company.ticker} Real INR vs Nominal INR`;
    chartSubheading.textContent = `Real purchasing power in constant base Rupees (deflated by 24K Gold) vs Nominal Price`;
    showLegend = true;

    datasets = [
      {
        label: "Real Price (Gold-Deflated INR)",
        data: series.map(d => d.real_inr),
        borderColor: "#d29922",
        backgroundColor: "rgba(210, 153, 34, 0.05)",
        borderWidth: 2.2,
        fill: true,
        tension: 0.1,
        pointRadius: series.length > 90 ? 0 : 2,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#e3b341"
      },
      {
        label: "Nominal Price (INR)",
        data: series.map(d => d.stock_inr),
        borderColor: "#58a6ff",
        backgroundColor: "transparent",
        borderWidth: 1.8,
        borderDash: [4, 4],
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#58a6ff"
      }
    ];

    yAxisCallback = function(value) {
      return `₹${value.toLocaleString('en-IN')}`;
    };

    tooltipCallback = {
      label: function(context) {
        const val = context.parsed.y;
        return ` ${context.dataset.label}: ₹${val.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      },
      afterBody: function(tooltipItems) {
        const idx = tooltipItems[0].dataIndex;
        const pt = series[idx];
        const gap = pt.stock_inr - pt.real_inr;
        const gapSign = gap >= 0 ? "+" : "";
        const inflationDiffPct = (((pt.stock_inr - pt.real_inr) / pt.real_inr) * 100).toFixed(1);
        return [
          ` Purchasing Power Gap: ${gapSign}₹${gap.toLocaleString('en-IN', {maximumFractionDigits: 2})} (${gapSign}${inflationDiffPct}%)`
        ];
      }
    };
  }

  chartInstance = new Chart(chartCanvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          display: showLegend,
          position: "top",
          labels: {
            color: "#8b949e",
            font: { family: "'Inter', sans-serif", size: 12 },
            usePointStyle: true,
            boxWidth: 8
          }
        },
        tooltip: {
          backgroundColor: "#161b22",
          titleColor: "#e6edf3",
          bodyColor: "#8b949e",
          borderColor: "#30363d",
          borderWidth: 1,
          padding: 10,
          displayColors: showLegend,
          callbacks: tooltipCallback
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: {
            color: "#6e7681",
            font: { family: "'JetBrains Mono', monospace", size: 11 },
            maxTicksLimit: 7
          }
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#6e7681",
            font: { family: "'JetBrains Mono', monospace", size: 11 },
            callback: yAxisCallback
          }
        }
      }
    }
  });
}

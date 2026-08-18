"""
Macro Intelligence App — Data Fetch Script
Run locally: python fetch_data.py
Generates all parquet files in ./data/
"""
import os, io, zipfile, warnings
import requests
import pandas as pd
import numpy as np
import yfinance as yf

warnings.filterwarnings("ignore")

FRED_KEY = os.environ.get("FRED_API_KEY", "602106c9a6a641df7c8bf4ffebd153c6")
DATA     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
START    = "2022-01-01"

os.makedirs(DATA, exist_ok=True)

def save(df, name):
    path = os.path.join(DATA, f"{name}.parquet")
    df.to_parquet(path, index=False)
    print(f"  ✓ {name}.parquet  ({len(df)} rows)")

def fred_fetch(series_id, col_name, start=START):
    url = (f"https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={series_id}&observation_start={start}"
           f"&api_key={FRED_KEY}&file_type=json")
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    obs = r.json()["observations"]
    df  = pd.DataFrame(obs)[["date","value"]]
    df["date"]   = pd.to_datetime(df["date"])
    df[col_name] = pd.to_numeric(df["value"], errors="coerce")
    return df[["date", col_name]].dropna()

def boc_fetch(series, col_name, start=START):
    """Correct BoC Valet API format."""
    url = (f"https://www.bankofcanada.ca/valet/observations/{series}/json"
           f"?start_date={start}")
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    obs  = r.json()["observations"]
    rows = []
    for o in obs:
        val = o.get(series, {})
        v   = val.get("v", "") if isinstance(val, dict) else ""
        if v not in ("", None, "NA"):
            rows.append({"date": pd.to_datetime(o["d"]), col_name: float(v)})
    return pd.DataFrame(rows)

def statcan_fetch(table_id):
    clean = table_id.replace("-", "")
    url   = f"https://www150.statcan.gc.ca/t1/tbl1/en/dtbl/{clean}/dtbl.zip"
    r     = requests.get(url, timeout=120)
    r.raise_for_status()
    z     = zipfile.ZipFile(io.BytesIO(r.content))
    csv   = [n for n in z.namelist() if n.endswith(".csv") and "MetaData" not in n][0]
    df    = pd.read_csv(z.open(csv), encoding="latin-1", low_memory=False)
    df.columns = df.columns.str.strip()
    return df

def synth_monthly(start=START, end="2026-07-01"):
    return pd.date_range(start, end, freq="MS")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. BANK OF CANADA
# Correct series codes: https://www.bankofcanada.ca/valet/lists/series/json
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Bank of Canada ──────────────────────────────────────")

boc_series = {
    "V122514":  "overnight_rate",   # Bank of Canada overnight rate target
    "V122530":  "prime_rate",       # Prime business loan rate
    "V39051":   "yield_2y",         # 2-year GoC bond yield
    "V39052":   "yield_5y",         # 5-year GoC bond yield
    "V39055":   "yield_10y",        # 10-year GoC bond yield
    "FXCADUSD": "cad_usd",          # CAD per USD (how many CAD per 1 USD)
}

boc_dfs = []
for series, col in boc_series.items():
    try:
        df = boc_fetch(series, col)
        boc_dfs.append(df)
        print(f"  ✓ {col}: {len(df)} obs | latest {df[col].iloc[-1]:.4f}")
    except Exception as e:
        print(f"  ✗ {col} ({series}): {e}")

if boc_dfs:
    from functools import reduce
    boc_df = reduce(lambda a,b: pd.merge(a,b,on="date",how="outer"), boc_dfs)
    boc_df = boc_df.sort_values("date").ffill()
    boc_df["spread_2y10y"] = boc_df.get("yield_10y", np.nan) - boc_df.get("yield_2y", np.nan)
    boc_df = boc_df[boc_df["date"] >= START]
    save(boc_df, "boc_rates")
    print(f"  Latest overnight: {boc_df['overnight_rate'].dropna().iloc[-1]:.2f}%")
    print(f"  Latest 2Y/10Y spread: {boc_df['spread_2y10y'].dropna().iloc[-1]:.2f}%")
else:
    print("  ! All BoC fetches failed — generating synthetic BoC data")
    dates = pd.date_range(START, "2026-07-01", freq="D")
    # Realistic BoC rate path: hikes to 5% by mid-2023, cuts to 2.75% by mid-2026
    n = len(dates)
    rate_path = np.interp(range(n),
                          [0, 200, 400, 700, n-1],
                          [1.0, 5.0, 5.0, 3.25, 2.75])
    boc_df = pd.DataFrame({
        "date":          dates,
        "overnight_rate":rate_path + np.random.uniform(-0.05,0.05,n),
        "prime_rate":    rate_path + 2.2 + np.random.uniform(-0.02,0.02,n),
        "yield_2y":      rate_path * 0.95 + np.random.uniform(-0.1,0.1,n),
        "yield_5y":      rate_path * 0.97 + np.random.uniform(-0.1,0.1,n),
        "yield_10y":     rate_path * 1.05 + np.random.uniform(-0.1,0.1,n),
        "cad_usd":       1.30 + np.random.uniform(-0.02,0.02,n),
    })
    boc_df["spread_2y10y"] = boc_df["yield_10y"] - boc_df["yield_2y"]
    save(boc_df, "boc_rates")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. STATISTICS CANADA
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Statistics Canada ───────────────────────────────────")

# CPI
print("  Fetching CPI (18-10-0004-01)...")
try:
    cpi_raw = statcan_fetch("18-10-0004-01")
    cpi = cpi_raw[
        (cpi_raw["GEO"] == "Canada") &
        (cpi_raw["Products and product groups"].isin([
            "All-items","Food","Shelter",
            "Household operations, furnishings and equipment",
            "Transportation","Health and personal care",
            "Recreation, education and reading","Clothing and footwear",
        ]))
    ].copy()
    cpi["date"]  = pd.to_datetime(cpi["REF_DATE"], format="%Y-%m")
    cpi["value"] = pd.to_numeric(cpi["VALUE"], errors="coerce")
    cpi = cpi[["date","Products and product groups","value"]].dropna()
    cpi.columns = ["date","component","value"]
    cpi = cpi[cpi["date"] >= START]
    save(cpi, "statcan_cpi")
    allitems = cpi[cpi["component"]=="All-items"].sort_values("date")
    allitems["cpi_yoy"] = allitems["value"].pct_change(12)*100
    print(f"  Latest CPI YoY: {allitems['cpi_yoy'].dropna().iloc[-1]:.1f}%")
except Exception as e:
    print(f"  ! CPI failed: {e} — synthetic")
    dates = synth_monthly()
    components = ["All-items","Food","Shelter","Transportation","Health and personal care"]
    rows = []
    for comp in components:
        base = {"All-items":152,"Food":163,"Shelter":175,"Transportation":145,"Health and personal care":140}[comp]
        vals = base + np.cumsum(np.random.uniform(0.1,0.5,len(dates)))
        for d,v in zip(dates,vals):
            rows.append({"date":d,"component":comp,"value":round(v,1)})
    cpi = pd.DataFrame(rows)
    save(cpi, "statcan_cpi")

# Labour
print("  Fetching Labour (14-10-0017-01)...")
try:
    lab_raw = statcan_fetch("14-10-0017-01")
    lab = lab_raw[
        (lab_raw["GEO"] == "Canada") &
        (lab_raw["Labour force characteristics"].isin([
            "Unemployment rate","Participation rate","Employment rate"
        ])) &
        (lab_raw["Sex"] == "Both sexes") &
        (lab_raw["Age group"] == "15 years and over")
    ].copy()
    lab["date"]  = pd.to_datetime(lab["REF_DATE"], format="%Y-%m")
    lab["value"] = pd.to_numeric(lab["VALUE"], errors="coerce")
    lab = lab[["date","Labour force characteristics","value"]].dropna()
    lab.columns = ["date","metric","value"]
    lab = lab[lab["date"] >= START]
    save(lab, "statcan_labour")
    unemp = lab[lab["metric"]=="Unemployment rate"].sort_values("date")
    print(f"  Latest unemployment: {unemp['value'].iloc[-1]:.1f}%")
except Exception as e:
    print(f"  ! Labour failed: {e} — synthetic")
    dates = synth_monthly()
    rows  = []
    for m,d in enumerate(dates):
        rows += [
            {"date":d,"metric":"Unemployment rate","value":round(6.5+np.sin(m/6)*0.8+np.random.uniform(-0.2,0.2),1)},
            {"date":d,"metric":"Participation rate","value":round(65.2+np.random.uniform(-0.3,0.3),1)},
        ]
    save(pd.DataFrame(rows), "statcan_labour")

# Wages
print("  Fetching Wages (14-10-0064-01)...")
try:
    wage_raw = statcan_fetch("14-10-0064-01")
    # Find the right column name for type of work
    type_col = [c for c in wage_raw.columns if "type" in c.lower() or "work" in c.lower()]
    geo_rows = wage_raw[wage_raw["GEO"] == "Canada"].copy()
    if type_col:
        geo_rows = geo_rows[geo_rows[type_col[0]].str.contains("Both", na=False)]
    geo_rows["date"]  = pd.to_datetime(geo_rows["REF_DATE"], format="%Y-%m")
    geo_rows["value"] = pd.to_numeric(geo_rows["VALUE"], errors="coerce")
    wage = geo_rows[["date","value"]].dropna().sort_values("date")
    wage = wage[wage["date"] >= START]
    wage["wage_yoy"] = wage["value"].pct_change(12)*100
    save(wage, "statcan_wages")
    print(f"  Latest wage YoY: {wage['wage_yoy'].dropna().iloc[-1]:.1f}%")
except Exception as e:
    print(f"  ! Wages failed: {e} — synthetic")
    dates = synth_monthly()
    wage  = pd.DataFrame({
        "date":    dates,
        "value":   28 + np.cumsum(np.random.uniform(0.02,0.07,len(dates))),
        "wage_yoy":np.clip(4.5 + np.random.uniform(-0.8,0.8,len(dates)), 2, 7),
    })
    save(wage, "statcan_wages")

# IPPI
print("  Fetching IPPI (16-10-0044-01)...")
try:
    ippi_raw = statcan_fetch("16-10-0044-01")
    prod_col = [c for c in ippi_raw.columns if "product" in c.lower()][0]
    ippi = ippi_raw[
        ippi_raw[prod_col].isin(["Total industrial products","Energy products",
                                  "Motor vehicles and other transportation equipment"])
    ].copy()
    ippi["date"]  = pd.to_datetime(ippi["REF_DATE"], format="%Y-%m")
    ippi["value"] = pd.to_numeric(ippi["VALUE"], errors="coerce")
    ippi = ippi[["date", prod_col, "value"]].dropna()
    ippi.columns = ["date","product","value"]
    ippi = ippi[ippi["date"] >= START]
    save(ippi, "statcan_ippi")
    print(f"  IPPI rows: {len(ippi)}")
except Exception as e:
    print(f"  ! IPPI failed: {e} — synthetic")
    dates = synth_monthly()
    rows  = []
    for prod,base in [("Total industrial products",108),("Energy products",115),
                       ("Motor vehicles",105)]:
        vals = base + np.cumsum(np.random.uniform(-0.3,0.8,len(dates)))
        for d,v in zip(dates,vals):
            rows.append({"date":d,"product":prod,"value":round(v,1)})
    save(pd.DataFrame(rows), "statcan_ippi")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. FRED
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── FRED (St. Louis Fed) ────────────────────────────────")

fred_series = {
    "FEDFUNDS":          "fed_funds_rate",
    "GSCPI":             "gscpi",
    "DCOILWTICO":        "wti_oil",
    "PCOPPUSDM":         "copper_usd",
    "BAMLH0A0HYM2":      "hy_spread_oas",
    "CPIAUCSL":          "us_cpi",
    "UNRATE":            "us_unemployment",
    "A191RL1Q225SBEA":   "us_gdp_growth",
}

fred_dfs = []
for series_id, col in fred_series.items():
    try:
        df = fred_fetch(series_id, col)
        fred_dfs.append(df)
        print(f"  ✓ {col}: {len(df)} obs | latest {df[col].iloc[-1]:.2f}")
    except Exception as e:
        print(f"  ✗ {col}: {e}")

if fred_dfs:
    from functools import reduce
    fred_df = reduce(lambda a,b: pd.merge(a,b,on="date",how="outer"), fred_dfs)
    fred_df = fred_df.sort_values("date").ffill()
    fred_df = fred_df[fred_df["date"] >= START]
    save(fred_df, "fred_macro")
else:
    print("  ! All FRED fetches failed — generating synthetic")
    dates = synth_monthly()
    n = len(dates)
    fred_df = pd.DataFrame({
        "date":           dates,
        "fed_funds_rate": np.interp(range(n),[0,180,350,600,n-1],[0.25,5.25,5.25,4.5,4.25]),
        "gscpi":          np.interp(range(n),[0,100,200,n-1],[0.5,3.2,-0.5,0.2])+np.random.uniform(-0.1,0.1,n),
        "wti_oil":        75+10*np.sin(np.linspace(0,4*np.pi,n))+np.random.uniform(-3,3,n),
        "copper_usd":     3.8+0.5*np.sin(np.linspace(0,3*np.pi,n))+np.random.uniform(-0.1,0.1,n),
        "hy_spread_oas":  350+80*np.sin(np.linspace(0,2*np.pi,n))+np.random.uniform(-10,10,n),
        "us_cpi":         np.interp(range(n),[0,150,300,n-1],[270,295,308,313]),
        "us_unemployment":np.interp(range(n),[0,50,n-1],[3.6,3.4,4.1])+np.random.uniform(-0.1,0.1,n),
        "us_gdp_growth":  np.random.uniform(1.5,3.5,n),
    })
    save(fred_df, "fred_macro")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. TSX SECTOR ETFs
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── TSX Sector ETFs (yfinance) ───────────────────────────")

etf_map = {
    "XIU.TO": "TSX 60",
    "XFN.TO": "Financials",
    "XIT.TO": "Technology",
    "XEG.TO": "Energy",
    "XST.TO": "Consumer Staples",
    "XUT.TO": "Utilities",
    "XRE.TO": "Real Estate",
}

try:
    tickers = list(etf_map.keys())
    raw = yf.download(tickers, start=START, auto_adjust=True, progress=False)["Close"]
    raw.columns = [etf_map.get(str(t), str(t)) for t in raw.columns]
    raw = raw.reset_index()
    raw.columns = ["date"] + [c for c in raw.columns if c != "date"]
    raw["date"] = pd.to_datetime(raw["date"])
    for col in etf_map.values():
        if col in raw.columns:
            raw[f"{col}_ret12w"] = raw[col].pct_change(60)*100
            raw[f"{col}_vol30d"] = raw[col].pct_change().rolling(30).std()*np.sqrt(252)*100
    save(raw, "tsx_etfs")
    print(f"  {len(raw)} trading days fetched")
except Exception as e:
    print(f"  ! yfinance failed: {e} — synthetic ETFs")
    dates = pd.date_range(START, "2026-08-13", freq="B")
    n = len(dates)
    tsx = pd.DataFrame({"date": dates})
    for name, base, vol in [("TSX 60",28,0.12),("Financials",38,0.14),
                              ("Technology",42,0.22),("Energy",18,0.25),
                              ("Consumer Staples",22,0.10),("Utilities",19,0.10),
                              ("Real Estate",16,0.16)]:
        returns = np.random.normal(0.0003, vol/np.sqrt(252), n)
        tsx[name] = base * np.cumprod(1+returns)
        tsx[f"{name}_ret12w"] = pd.Series(tsx[name]).pct_change(60)*100
        tsx[f"{name}_vol30d"] = pd.Series(tsx[name]).pct_change().rolling(30).std()*np.sqrt(252)*100
    save(tsx, "tsx_etfs")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. SYNTHETIC INTERNAL DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("\n── Synthetic Internal Data ─────────────────────────────")
np.random.seed(42)

sectors      = ["Financials","Technology","Energy","Consumer Staples","Utilities","Real Estate","Manufacturing"]
sector_probs = {"Financials":0.04,"Technology":0.06,"Energy":0.12,
                "Consumer Staples":0.03,"Utilities":0.05,"Real Estate":0.14,"Manufacturing":0.08}

cust_sectors = pd.DataFrame({
    "customer_id":      [f"C{i:03d}" for i in range(1,53)],
    "sector":           np.random.choice(sectors, 52, p=[0.25,0.20,0.18,0.15,0.10,0.07,0.05]),
})
cust_sectors["default_prob_60d"] = (
    cust_sectors["sector"].map(sector_probs) + np.random.uniform(-0.02,0.02,52)
).clip(0.01,0.95)

shap_df = pd.DataFrame({
    "feature":         ["BoC Rate Direction","Sector ETF Momentum","DSO Trend",
                        "HY Spread Level","Customer Leverage","GDP Growth Signal","FX Volatility"],
    "mean_shap_value": [0.35,0.28,0.22,0.15,0.11,0.08,0.05],
    "direction":       ["negative"]*6+["negative"],
})

dates_m = synth_monthly()
headcount = pd.DataFrame({
    "date":      dates_m,
    "headcount": np.clip(185+np.cumsum(np.random.randint(-2,4,len(dates_m))),160,220),
    "avg_salary":72000+np.cumsum(np.random.uniform(100,400,len(dates_m))),
})
freight = pd.DataFrame({
    "date":            dates_m,
    "spot_freight":    1.0+np.cumsum(np.random.uniform(-0.02,0.04,len(dates_m))),
    "hist_avg_freight":1.0,
})
freight["freight_premium"] = freight["spot_freight"] - freight["hist_avg_freight"]

save(cust_sectors, "synthetic_customers_sectors")
save(shap_df,      "synthetic_shap")
save(headcount,    "synthetic_headcount")
save(freight,      "synthetic_freight")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print("\n✓ All done. Files in ./data/:")
for f in sorted(os.listdir(DATA)):
    kb = os.path.getsize(os.path.join(DATA,f))/1024
    print(f"  {f:48s} {kb:.0f} KB")
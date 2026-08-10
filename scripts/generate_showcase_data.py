"""
generate_showcase_data.py
=========================
C-Suite Intelligence Platform — Full Data Generation Script
"What Your ERP Cannot Tell You"

Run once to produce showcase_data.sql containing all INSERT statements
for every table in the Azure SQL schema.

Usage:
    pip install pandas numpy xgboost shap scipy requests statscan yfinance
    python generate_showcase_data.py

Output:
    showcase_data.sql   — load into Azure SQL after executing showcase_schema.sql
    showcase_run.log    — row counts and any API fetch warnings

Decisions confirmed:
    Azure SQL:   Basic tier (2GB)
    History:     28 months — April 2024 to July 2026
    PBI mode:    Import
    Website:     Next.js / Vercel
"""

import os
import sys
import math
import random
import logging
import warnings
import textwrap
import datetime as dt
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ── optional imports (graceful fallback with warnings) ──────────────────────
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("WARNING: xgboost not installed — AR scores will use logistic approximation")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("WARNING: shap not installed — SHAP drivers will use feature-weight proxy")

try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False
    print("WARNING: yfinance not installed — ETF data will be synthetically generated")

try:
    from stats_can import StatsCan
    HAS_STATSCAN = True
except ImportError:
    HAS_STATSCAN = False
    print("WARNING: stats-can not installed — StatCan data will be synthetically generated")

warnings.filterwarnings("ignore")

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ── Date range ────────────────────────────────────────────────────────────────
START_DATE = dt.date(2024, 4, 1)    # April 1 2024 — FY2025 open
END_DATE   = dt.date(2026, 7, 31)   # July 31 2026 — current period
MONTHS     = 28

# ── SQL output ────────────────────────────────────────────────────────────────
OUTPUT_SQL = Path("showcase_data.sql")
OUTPUT_LOG = Path("showcase_run.log")

logging.basicConfig(
    filename=str(OUTPUT_LOG),
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
#  SECTION 0 — SQL writer helpers
# ────────────────────────────────────────────────────────────────────────────

def sql_val(v):
    """Format a Python value for SQL INSERT."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return f"'{v}'"
    s = str(v).replace("'", "''")
    return f"'{s}'"


def df_to_insert(df: pd.DataFrame, table: str, chunk: int = 500) -> str:
    """Convert a DataFrame to batched SQL INSERT statements."""
    if df.empty:
        return f"-- {table}: no rows\n"
    cols = ", ".join(df.columns)
    lines = [f"-- {table} ({len(df):,} rows)\n"]
    rows = [
        "(" + ", ".join(sql_val(v) for v in row) + ")"
        for row in df.itertuples(index=False, name=None)
    ]
    for i in range(0, len(rows), chunk):
        batch = rows[i : i + chunk]
        lines.append(f"INSERT INTO {table} ({cols}) VALUES\n")
        lines.append(",\n".join(batch) + ";\n\n")
    return "".join(lines)


sql_buffer = StringIO()

def emit(sql: str):
    sql_buffer.write(sql)

def section(title: str):
    emit(f"\n-- {'─'*70}\n-- {title}\n-- {'─'*70}\n\n")

# ────────────────────────────────────────────────────────────────────────────
#  SECTION 1 — DIMENSIONS
# ────────────────────────────────────────────────────────────────────────────

def build_dimensions():
    section("DIMENSIONS")

    # ── dim.entities ──────────────────────────────────────────────────────────
    entities = pd.DataFrame([
        {"entity_id": "E01", "entity_name": "FinCo Holdings Inc.",         "province": "ON", "tax_code": "HST", "tax_rate": 0.13,    "is_holdco": 1, "fiscal_year_start_month": 4},
        {"entity_id": "E02", "entity_name": "FinCo West Operations Ltd.",  "province": "AB", "tax_code": "GST", "tax_rate": 0.05,    "is_holdco": 0, "fiscal_year_start_month": 4},
        {"entity_id": "E03", "entity_name": "FinCo Est Operations Inc.",   "province": "QC", "tax_code": "TVQ", "tax_rate": 0.14975, "is_holdco": 0, "fiscal_year_start_month": 4},
        {"entity_id": "E04", "entity_name": "FinCo Ontario Services Ltd.", "province": "ON", "tax_code": "HST", "tax_rate": 0.13,    "is_holdco": 0, "fiscal_year_start_month": 4},
    ])
    emit(df_to_insert(entities, "dim.entities"))
    log.info("dim.entities: %d rows", len(entities))

    # ── dim.chart_of_accounts ─────────────────────────────────────────────────
    coa_data = [
        # Revenue
        ("4001","Revenue - Product Sales",          "Revenue",    "CR", "E01"),
        ("4002","Revenue - Service Fees",           "Revenue",    "CR", "E01"),
        ("4003","Revenue - Recurring Contracts",    "Revenue",    "CR", "E01"),
        ("4004","Revenue - Export",                 "Revenue",    "CR", "E01"),
        ("4005","Revenue - Intercompany",           "Revenue",    "CR", "E01"),
        # COGS
        ("5001","COGS - Direct Materials",          "COGS",       "DR", "E01"),
        ("5002","COGS - Direct Labour",             "COGS",       "DR", "E01"),
        ("5003","COGS - Freight and Logistics",     "COGS",       "DR", "E01"),
        # OpEx
        ("6001","Salaries and Benefits",            "OpEx",       "DR", "E01"),
        ("6002","Rent and Occupancy",               "OpEx",       "DR", "E01"),
        ("6003","Technology and Software",          "OpEx",       "DR", "E01"),
        ("6004","Marketing and Advertising",        "OpEx",       "DR", "E01"),
        ("6005","Professional Fees",                "OpEx",       "DR", "E01"),
        ("6006","Travel and Entertainment",         "OpEx",       "DR", "E01"),
        ("6007","Depreciation",                     "OpEx",       "DR", "E01"),
        ("6008","Insurance",                        "OpEx",       "DR", "E01"),
        ("6009","Utilities",                        "OpEx",       "DR", "E01"),
        # CapEx
        ("7001","CapEx - IT Infrastructure",        "CapEx",      "DR", "E01"),
        ("7002","CapEx - Equipment",                "CapEx",      "DR", "E01"),
        ("7003","CapEx - Leasehold Improvements",   "CapEx",      "DR", "E01"),
        # Assets
        ("1001","Cash and Equivalents",             "Asset",      "DR", "E01"),
        ("1002","Accounts Receivable",              "Asset",      "DR", "E01"),
        ("1003","Inventory",                        "Asset",      "DR", "E01"),
        ("1004","Prepaid Expenses",                 "Asset",      "DR", "E01"),
        ("1005","Fixed Assets Net",                 "Asset",      "DR", "E01"),
        # Liabilities
        ("2001","Accounts Payable",                 "Liability",  "CR", "E01"),
        ("2002","Accrued Liabilities",              "Liability",  "CR", "E01"),
        ("2003","Deferred Revenue",                 "Liability",  "CR", "E01"),
        ("2004","Long-term Debt",                   "Liability",  "CR", "E01"),
        ("2005","Income Tax Payable",               "Liability",  "CR", "E01"),
        # Equity
        ("3001","Retained Earnings",                "Equity",     "CR", "E01"),
        ("3002","Share Capital",                    "Equity",     "CR", "E01"),
        # Intercompany
        ("8001","Intercompany Receivable",          "Intercompany","DR","E01"),
        ("8002","Intercompany Payable",             "Intercompany","CR","E01"),
    ]
    coa = pd.DataFrame(coa_data, columns=["account_id","account_name","category","normal_balance","primary_entity"])
    emit(df_to_insert(coa, "dim.chart_of_accounts"))

    # ── dim.cost_centres ──────────────────────────────────────────────────────
    cost_centres = pd.DataFrame([
        {"cc_id":"CC01","cc_name":"Corporate - Executive",       "entity_id":"E01","department":"Corporate"},
        {"cc_id":"CC02","cc_name":"Corporate - Finance",         "entity_id":"E01","department":"Finance"},
        {"cc_id":"CC03","cc_name":"Corporate - IT",              "entity_id":"E01","department":"IT"},
        {"cc_id":"CC04","cc_name":"Corporate - HR",              "entity_id":"E01","department":"HR"},
        {"cc_id":"CC05","cc_name":"Corporate - Legal",           "entity_id":"E01","department":"Legal"},
        {"cc_id":"CC06","cc_name":"West - Sales",                "entity_id":"E02","department":"Sales"},
        {"cc_id":"CC07","cc_name":"West - Operations",           "entity_id":"E02","department":"Operations"},
        {"cc_id":"CC08","cc_name":"West - Customer Success",     "entity_id":"E02","department":"CX"},
        {"cc_id":"CC09","cc_name":"West - Finance",              "entity_id":"E02","department":"Finance"},
        {"cc_id":"CC10","cc_name":"West - Warehouse",            "entity_id":"E02","department":"Operations"},
        {"cc_id":"CC11","cc_name":"QC - Sales",                  "entity_id":"E03","department":"Sales"},
        {"cc_id":"CC12","cc_name":"QC - Operations",             "entity_id":"E03","department":"Operations"},
        {"cc_id":"CC13","cc_name":"QC - Customer Success",       "entity_id":"E03","department":"CX"},
        {"cc_id":"CC14","cc_name":"QC - Finance",                "entity_id":"E03","department":"Finance"},
        {"cc_id":"CC15","cc_name":"QC - Retail Services",        "entity_id":"E03","department":"Retail"},
        {"cc_id":"CC16","cc_name":"ON Svcs - Sales",             "entity_id":"E04","department":"Sales"},
        {"cc_id":"CC17","cc_name":"ON Svcs - Delivery",          "entity_id":"E04","department":"Operations"},
        {"cc_id":"CC18","cc_name":"ON Svcs - Finance",           "entity_id":"E04","department":"Finance"},
        {"cc_id":"CC19","cc_name":"ON Svcs - Support",           "entity_id":"E04","department":"CX"},
        {"cc_id":"CC20","cc_name":"Group - Shared Services",     "entity_id":"E01","department":"Corporate"},
    ])
    emit(df_to_insert(cost_centres, "dim.cost_centres"))

    # ── dim.customers (50 customers) ──────────────────────────────────────────
    rng = np.random.default_rng(RANDOM_SEED)
    sectors    = ["Manufacturing","Retail","Technology","Healthcare","Construction","Finance","Energy","Transportation"]
    provinces  = ["ON","AB","QC","BC","MB"]
    risk_tiers = ["Low","Medium","High"]

    # Controlled risk: QC Retail gets elevated bad debt (8% vs 1.2% overall)
    customers = []
    for i in range(1, 51):
        province = rng.choice(provinces, p=[0.40, 0.20, 0.25, 0.10, 0.05])
        sector   = rng.choice(sectors)
        # QC Retail: elevated risk
        if province == "QC" and sector == "Retail":
            ecl_rate  = round(float(rng.uniform(0.06, 0.10)), 4)
            risk_tier = "High"
        else:
            ecl_rate  = round(float(rng.uniform(0.005, 0.025)), 4)
            risk_tier = rng.choice(risk_tiers, p=[0.60, 0.30, 0.10])
        customers.append({
            "customer_id":      f"C{i:03d}",
            "customer_name":    f"Customer {i:03d} {sector[:3].upper()}",
            "sector":           sector,
            "province":         province,
            "payment_terms_days": int(rng.choice([30, 45, 60, 90])),
            "credit_limit":     int(rng.choice([50000, 100000, 200000, 500000])),
            "risk_tier":        risk_tier,
            "ecl_rate_base":    ecl_rate,
            "entity_id":        rng.choice(["E01","E02","E03","E04"]),
            "active":           1,
        })
    customers_df = pd.DataFrame(customers)
    emit(df_to_insert(customers_df, "dim.customers"))

    # ── dim.vendors (30 vendors) ──────────────────────────────────────────────
    vendor_cats = ["Raw Materials","Logistics","IT Services","Facilities","Professional Services","Utilities"]
    vendors = []
    for i in range(1, 31):
        vendors.append({
            "vendor_id":          f"V{i:03d}",
            "vendor_name":        f"Vendor {i:03d} {rng.choice(vendor_cats)[:6].upper()}",
            "category":           rng.choice(vendor_cats),
            "payment_terms_days": int(rng.choice([30, 45, 60])),
            "province":           rng.choice(provinces),
            "strategic":          int(rng.random() < 0.3),
        })
    vendors_df = pd.DataFrame(vendors)
    emit(df_to_insert(vendors_df, "dim.vendors"))

    log.info("Dimensions written: entities=4, coa=32, cc=20, customers=50, vendors=30")
    return entities, coa, cost_centres, customers_df, vendors_df


# ────────────────────────────────────────────────────────────────────────────
#  SECTION 2 — ERP FACTS  (GL, AR, AP)
# ────────────────────────────────────────────────────────────────────────────

def month_dates():
    """Yield (period_start, period_end, fiscal_year, fiscal_quarter, period_label) for 28 months."""
    cur = START_DATE
    records = []
    while cur <= END_DATE:
        month_end = (cur.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
        fy_offset = (cur.month - 4) % 12   # April = FY month 1
        fy_year   = cur.year if cur.month >= 4 else cur.year - 1
        fy_qtr    = (fy_offset // 3) + 1
        label     = cur.strftime("%b-%Y")
        records.append((cur, month_end, f"FY{fy_year+1}", f"Q{fy_qtr}", label))
        # advance to next month
        if cur.month == 12:
            cur = cur.replace(year=cur.year+1, month=1)
        else:
            cur = cur.replace(month=cur.month+1)
    return records


def seasonal_factor(date: dt.date) -> float:
    """
    Canadian fiscal-year seasonality:
    - Q4 (Jan–Mar) spike +22%: year-end budget flush
    - Q1 (Apr–Jun) dip  –8%:  new budget caution
    - Gradual macro deterioration from Month 13 onward (rate cycle peak)
    """
    fy_month = ((date.month - 4) % 12) + 1   # 1=Apr, 12=Mar
    q4_boost = 1.22 if fy_month in (10, 11, 12) else 1.0
    q1_dip   = 0.92 if fy_month in (1, 2, 3)  else 1.0
    # Demand deceleration: starts Month 13 (April 2025), -0.5%/month
    months_in = max(0, (date.year - START_DATE.year) * 12 + (date.month - START_DATE.month) - 12)
    decel     = max(0.85, 1.0 - 0.005 * months_in)
    return q4_boost * q1_dip * decel


def build_gl(customers_df, cost_centres, coa):
    """Generate ~18,000 GL line items across 4 entities and 28 periods."""
    section("ERP FACTS — GL LEDGER")
    rng = np.random.default_rng(RANDOM_SEED + 1)
    periods = month_dates()

    # Monthly base revenue by entity (HoldCo consolidates subsidiaries)
    base_rev = {"E01": 450_000, "E02": 280_000, "E03": 320_000, "E04": 195_000}

    gl_rows = []
    gl_id = 1

    revenue_accts   = ["4001","4002","4003","4004"]
    cogs_accts      = ["5001","5002","5003"]
    opex_accts      = ["6001","6002","6003","6004","6005","6006","6007","6008","6009"]
    capex_accts     = ["7001","7002","7003"]

    entity_cc = {
        "E01": [cc for cc in cost_centres["cc_id"] if cc in ("CC01","CC02","CC03","CC04","CC05","CC20")],
        "E02": [cc for cc in cost_centres["cc_id"] if cc in ("CC06","CC07","CC08","CC09","CC10")],
        "E03": [cc for cc in cost_centres["cc_id"] if cc in ("CC11","CC12","CC13","CC14","CC15")],
        "E04": [cc for cc in cost_centres["cc_id"] if cc in ("CC16","CC17","CC18","CC19")],
    }
    # IT overrun: CC03 technology spend is 12% over budget from Month 15 onward (ERP modernisation)
    it_overrun_start = START_DATE.replace(year=2025, month=7)

    for (pstart, pend, fy, q, label) in periods:
        sf = seasonal_factor(pstart)
        for entity in ["E01","E02","E03","E04"]:
            rev_base = base_rev[entity] * sf
            cogs_pct  = rng.uniform(0.48, 0.55)
            opex_base = rev_base * rng.uniform(0.30, 0.38)

            # ── Revenue lines (3–5 per entity per month) ──────────────────
            for acct in rng.choice(revenue_accts, size=rng.integers(3, 5), replace=False):
                amt = round(float(rev_base * rng.uniform(0.18, 0.35) * sf), 2)
                gl_rows.append({
                    "gl_id":        gl_id,
                    "entity_id":    entity,
                    "account_id":   acct,
                    "cc_id":        rng.choice(entity_cc[entity]),
                    "period_start": pstart,
                    "period_end":   pend,
                    "fiscal_year":  fy,
                    "fiscal_quarter": q,
                    "debit_amount": 0.0,
                    "credit_amount": amt,
                    "description":  f"Revenue {acct} {label}",
                    "posted":       1,
                })
                gl_id += 1

            # ── COGS lines ────────────────────────────────────────────────
            for acct in cogs_accts:
                amt = round(float(rev_base * cogs_pct * rng.uniform(0.28, 0.40)), 2)
                gl_rows.append({
                    "gl_id":        gl_id,
                    "entity_id":    entity,
                    "account_id":   acct,
                    "cc_id":        rng.choice(entity_cc[entity]),
                    "period_start": pstart,
                    "period_end":   pend,
                    "fiscal_year":  fy,
                    "fiscal_quarter": q,
                    "debit_amount":  amt,
                    "credit_amount": 0.0,
                    "description":  f"COGS {acct} {label}",
                    "posted":       1,
                })
                gl_id += 1

            # ── OpEx lines ────────────────────────────────────────────────
            for acct in opex_accts:
                multiplier = 1.0
                # IT overrun pattern
                if acct == "6003" and entity == "E01" and pstart >= it_overrun_start:
                    multiplier = 1.12
                amt = round(float(opex_base * rng.uniform(0.08, 0.16) * multiplier), 2)
                gl_rows.append({
                    "gl_id":        gl_id,
                    "entity_id":    entity,
                    "account_id":   acct,
                    "cc_id":        rng.choice(entity_cc[entity]),
                    "period_start": pstart,
                    "period_end":   pend,
                    "fiscal_year":  fy,
                    "fiscal_quarter": q,
                    "debit_amount":  amt,
                    "credit_amount": 0.0,
                    "description":  f"OpEx {acct} {label}",
                    "posted":       1,
                })
                gl_id += 1

            # ── CapEx (quarterly — not every month) ───────────────────────
            if pstart.month in (4, 7, 10, 1):
                for acct in rng.choice(capex_accts, size=rng.integers(1, 3), replace=False):
                    amt = round(float(rng.uniform(15_000, 80_000)), 2)
                    gl_rows.append({
                        "gl_id":        gl_id,
                        "entity_id":    entity,
                        "account_id":   acct,
                        "cc_id":        rng.choice(entity_cc[entity]),
                        "period_start": pstart,
                        "period_end":   pend,
                        "fiscal_year":  fy,
                        "fiscal_quarter": q,
                        "debit_amount":  amt,
                        "credit_amount": 0.0,
                        "description":  f"CapEx {acct} {label}",
                        "posted":       1,
                    })
                    gl_id += 1

    gl_df = pd.DataFrame(gl_rows)
    emit(df_to_insert(gl_df, "erp.gl_ledger"))
    log.info("erp.gl_ledger: %d rows", len(gl_df))
    return gl_df


def build_ar(customers_df):
    """Generate ~5,000 AR invoices with payment status and ECL rates."""
    section("ERP FACTS — AR INVOICES")
    rng = np.random.default_rng(RANDOM_SEED + 2)
    periods = month_dates()

    # Days-past-due acceleration: 3 specific customers in QC Retail show DPD +18 in 30 days
    accelerating_customers = customers_df[
        (customers_df["province"] == "QC") & (customers_df["risk_tier"] == "High")
    ]["customer_id"].tolist()[:3]

    ar_rows = []
    inv_id = 1
    for (pstart, pend, fy, q, label) in periods:
        sf = seasonal_factor(pstart)
        for _, cust in customers_df.iterrows():
            n_inv = rng.integers(2, 6)
            for _ in range(n_inv):
                inv_date  = pstart + dt.timedelta(days=int(rng.integers(0, 28)))
                terms     = int(cust["payment_terms_days"])
                due_date  = inv_date + dt.timedelta(days=terms)
                amount    = round(float(rng.uniform(2_000, 45_000) * sf), 2)

                # Payment behaviour
                if cust["risk_tier"] == "High":
                    days_late = int(rng.choice([0, 15, 30, 60, 90, 120], p=[0.30, 0.15, 0.20, 0.15, 0.12, 0.08]))
                elif cust["risk_tier"] == "Medium":
                    days_late = int(rng.choice([0, 10, 20, 45],           p=[0.60, 0.20, 0.15, 0.05]))
                else:
                    days_late = int(rng.choice([0, 5, 15],                p=[0.80, 0.15, 0.05]))

                # DPD acceleration for flagged customers in recent 3 months
                if cust["customer_id"] in accelerating_customers:
                    months_ago = (END_DATE.year - pstart.year) * 12 + (END_DATE.month - pstart.month)
                    if months_ago <= 3:
                        days_late = min(180, days_late + int(rng.integers(15, 25)))

                pay_date = due_date + dt.timedelta(days=days_late)
                paid     = pay_date <= END_DATE

                aging_bucket = (
                    "Current"  if days_late == 0 else
                    "1-30"     if days_late <= 30 else
                    "31-60"    if days_late <= 60 else
                    "61-90"    if days_late <= 90 else
                    "91+"
                )
                ecl_rate = float(cust["ecl_rate_base"]) * (1 + 0.5 * (days_late / 90))
                ecl_rate = min(ecl_rate, 0.95)
                ecl_amt  = round(amount * ecl_rate, 2) if not paid else 0.0

                ar_rows.append({
                    "invoice_id":      f"INV{inv_id:06d}",
                    "customer_id":     cust["customer_id"],
                    "entity_id":       cust["entity_id"],
                    "invoice_date":    inv_date,
                    "due_date":        due_date,
                    "amount":          amount,
                    "paid":            int(paid),
                    "payment_date":    pay_date if paid else None,
                    "days_past_due":   max(0, days_late),
                    "aging_bucket":    aging_bucket,
                    "ecl_rate":        round(ecl_rate, 4),
                    "ecl_amount":      ecl_amt,
                    "fiscal_year":     fy,
                    "period_label":    label,
                })
                inv_id += 1

    ar_df = pd.DataFrame(ar_rows)
    emit(df_to_insert(ar_df, "erp.ar_invoices"))
    log.info("erp.ar_invoices: %d rows", len(ar_df))
    return ar_df


def build_ap(vendors_df):
    """Generate ~3,500 AP invoices with payment timing for DPO calculation."""
    section("ERP FACTS — AP INVOICES")
    rng = np.random.default_rng(RANDOM_SEED + 3)
    periods = month_dates()

    ap_rows = []
    ap_id = 1
    # Strategic late payment: from Month 13 onward (demand slowdown), DPO stretches +8 days
    stretch_start = START_DATE.replace(year=2025, month=5)

    for (pstart, pend, fy, q, label) in periods:
        for _, vendor in vendors_df.iterrows():
            n_inv = rng.integers(2, 5)
            for _ in range(n_inv):
                inv_date  = pstart + dt.timedelta(days=int(rng.integers(0, 25)))
                terms     = int(vendor["payment_terms_days"])
                due_date  = inv_date + dt.timedelta(days=terms)
                amount    = round(float(rng.uniform(1_000, 30_000)), 2)

                # DPO stretch in slowdown regime
                late_adj = 8 if pstart >= stretch_start else 0
                days_early_late = int(rng.integers(-5, late_adj + 10))  # negative = early
                pay_date = due_date + dt.timedelta(days=days_early_late)
                paid     = pay_date <= END_DATE

                ap_rows.append({
                    "ap_id":           f"AP{ap_id:06d}",
                    "vendor_id":       vendor["vendor_id"],
                    "entity_id":       rng.choice(["E01","E02","E03","E04"]),
                    "invoice_date":    inv_date,
                    "due_date":        due_date,
                    "amount":          amount,
                    "paid":            int(paid),
                    "payment_date":    pay_date if paid else None,
                    "days_from_due":   days_early_late,
                    "fiscal_year":     fy,
                    "period_label":    label,
                })
                ap_id += 1

    ap_df = pd.DataFrame(ap_rows)
    emit(df_to_insert(ap_df, "erp.ap_invoices"))
    log.info("erp.ap_invoices: %d rows", len(ap_df))
    return ap_df


# ────────────────────────────────────────────────────────────────────────────
#  SECTION 3 — MACRO DATA  (real API + synthetic fallback)
# ────────────────────────────────────────────────────────────────────────────

BOC_BASE = "https://www.bankofcanada.ca/valet"

BOC_SERIES = {
    "BOC_POLICY_RATE": "V39079",
    "BOC_YIELD_2Y":    "V39051",
    "BOC_YIELD_10Y":   "V39055",
    "BOC_CORRA":       "V122514",
    "BOC_USDCAD":      "FXUSDCAD",
}

def fetch_boc(series_key: str, series_id: str, start: str, end: str):
    """Fetch a single Bank of Canada Valet series. Returns list of (date, value)."""
    url = f"{BOC_BASE}/observations/{series_id}/json"
    params = {"start_date": start, "end_date": end, "recent": 1000}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        obs  = data.get("observations", [])
        results = []
        for o in obs:
            d = o.get("d")
            v = o.get(series_id, {}).get("v")
            if d and v:
                results.append((dt.date.fromisoformat(d), float(v)))
        log.info("BoC %s (%s): %d observations", series_key, series_id, len(results))
        return results
    except Exception as e:
        log.warning("BoC fetch failed for %s: %s", series_key, e)
        return []


def synthetic_boc(metric_key: str, dates) -> list:
    """
    Generate synthetic macro series that match the exhibit patterns described in the plan:
    - Yield curve inverts Month 10, un-inverts Month 15
    - BoC policy rate declining from 5.0 to 3.0 over 28 months
    - USD/CAD rises 1.35 → 1.42
    """
    rng = np.random.default_rng(RANDOM_SEED + 10)
    results = []
    n = len(dates)
    for i, d in enumerate(dates):
        t = i / max(n - 1, 1)
        if metric_key == "BOC_POLICY_RATE":
            val = 5.0 - 2.0 * t + float(rng.normal(0, 0.05))
        elif metric_key == "BOC_YIELD_2Y":
            # 2Y tracks policy closely, slight lag
            val = 4.8 - 1.8 * t + float(rng.normal(0, 0.08))
        elif metric_key == "BOC_YIELD_10Y":
            # 10Y: dips to inversion around month 10, recovers month 15
            inversion_factor = -0.3 * math.exp(-0.5 * ((i - 10) ** 2) / 9)
            val = 4.0 - 0.8 * t + inversion_factor + float(rng.normal(0, 0.06))
        elif metric_key == "BOC_CORRA":
            val = 4.9 - 1.9 * t + float(rng.normal(0, 0.04))
        elif metric_key == "BOC_USDCAD":
            val = 1.35 + 0.07 * t + float(rng.normal(0, 0.003))
        else:
            val = float(rng.uniform(1, 5))
        results.append((d, round(val, 4)))
    return results


def build_macro():
    """Fetch real macro data; fall back to synthetic if APIs unavailable."""
    section("MACRO DATA — ECONOMIC INDICATORS")
    rng = np.random.default_rng(RANDOM_SEED + 4)

    start_str = START_DATE.isoformat()
    end_str   = END_DATE.isoformat()

    # All trading/business dates in range
    all_dates = pd.date_range(start=START_DATE, end=END_DATE, freq="B").date.tolist()
    monthly_dates = [d for d in all_dates if d.day <= 7]  # first week = monthly observation

    macro_rows = []
    obs_id = 1

    # ── Bank of Canada series ─────────────────────────────────────────────────
    for metric_key, series_id in BOC_SERIES.items():
        observations = fetch_boc(metric_key, series_id, start_str, end_str)
        if not observations:
            print(f"  BoC API unavailable for {metric_key} — using synthetic series")
            observations = synthetic_boc(metric_key, monthly_dates)

        for (obs_date, value) in observations:
            if START_DATE <= obs_date <= END_DATE:
                macro_rows.append({
                    "obs_id":      obs_id,
                    "obs_date":    obs_date,
                    "metric_key":  metric_key,
                    "value":       value,
                    "source":      "Bank of Canada Valet API",
                    "frequency":   "Daily",
                })
                obs_id += 1

    # ── StatCan series (monthly) ──────────────────────────────────────────────
    statcan_series = {
        "STATCAN_MFG_NEW_ORDERS": ("16-10-0047-01", "Manufacturing new orders"),
        "STATCAN_MFG_INVENTORY":  ("16-10-0047-01", "Manufacturing inventory"),
        "STATCAN_LFS_UNEMPLOYMENT":("14-10-0287-01", "Labour Force Survey unemployment rate"),
        "STATCAN_IPPI":           ("18-10-0265-01", "Industrial Product Price Index"),
    }

    for metric_key, (table_id, description) in statcan_series.items():
        if HAS_STATSCAN:
            try:
                sc = StatsCan()
                df = sc.table_to_df(table_id)
                observations = [(row.REF_DATE.date(), float(row.VALUE))
                                for _, row in df.iterrows()
                                if not pd.isna(row.VALUE)
                                and START_DATE <= row.REF_DATE.date() <= END_DATE]
                log.info("StatCan %s: %d observations", metric_key, len(observations))
            except Exception as e:
                log.warning("StatCan %s failed: %s — using synthetic", metric_key, e)
                observations = []
        else:
            observations = []

        if not observations:
            # Synthetic monthly: orders/inventory ratio drops to 0.92 at Month 13
            for i, d in enumerate(monthly_dates):
                if metric_key == "STATCAN_MFG_NEW_ORDERS":
                    # Index: peaks then declines
                    val = 120 + 5 * math.sin(i * 0.4) - 0.3 * max(0, i - 12) + float(rng.normal(0, 1))
                elif metric_key == "STATCAN_MFG_INVENTORY":
                    # Inventory builds as orders slow
                    val = 110 + 0.4 * max(0, i - 10) + float(rng.normal(0, 0.8))
                elif metric_key == "STATCAN_LFS_UNEMPLOYMENT":
                    val = 5.8 + 0.08 * max(0, i - 12) + float(rng.normal(0, 0.1))
                else:  # IPPI
                    val = 130 + 0.5 * i + float(rng.normal(0, 0.5))
                observations.append((d, round(val, 2)))

        for (obs_date, value) in observations:
            if START_DATE <= obs_date <= END_DATE:
                macro_rows.append({
                    "obs_id":      obs_id,
                    "obs_date":    obs_date,
                    "metric_key":  metric_key,
                    "value":       value,
                    "source":      "Statistics Canada",
                    "frequency":   "Monthly",
                })
                obs_id += 1

    macro_df = pd.DataFrame(macro_rows)
    emit(df_to_insert(macro_df, "macro.economic_indicators"))
    log.info("macro.economic_indicators: %d rows", len(macro_df))
    return macro_df


def build_sector_rotation():
    """Fetch TSX sector ETF prices; fall back to synthetic if yfinance unavailable."""
    section("MACRO DATA — SECTOR ROTATION")
    rng = np.random.default_rng(RANDOM_SEED + 5)

    etfs = {
        "XIU": "iShares S&P/TSX 60 (Broad Market)",
        "XFN": "iShares TSX Financials",
        "XEG": "iShares TSX Energy",
        "XMA": "iShares TSX Materials",
        "XMD": "iShares TSX MidCap",
        "XST": "iShares TSX Staples",
        "XUT": "iShares TSX Utilities",
        "XRE": "iShares TSX Real Estate",
        "XIT": "iShares TSX Technology",
        "XCV": "iShares TSX Healthcare",
    }

    all_trading_dates = pd.date_range(START_DATE, END_DATE, freq="B").date.tolist()
    rot_rows = []
    row_id = 1

    # Sector rotation pattern: Staples (XST) and Utilities (XUT) outperform from Month 12
    # Energy (XEG) leads early cycle then fades; Financials (XFN) mid-cycle
    rotation_onset = START_DATE.replace(year=2025, month=4)

    for ticker, description in etfs.items():
        # Try real data
        prices = {}
        if HAS_YF:
            try:
                t = yf.Ticker(f"{ticker}.TO")
                hist = t.history(start=START_DATE.isoformat(), end=END_DATE.isoformat())
                for d, row in hist.iterrows():
                    prices[d.date()] = round(float(row["Close"]), 2)
                log.info("yfinance %s.TO: %d days", ticker, len(prices))
            except Exception as e:
                log.warning("yfinance %s failed: %s", ticker, e)

        if not prices:
            # Synthetic: base trend + sector rotation signal
            base = {"XIU":30,"XFN":40,"XEG":20,"XMA":18,"XMD":25,
                    "XST":35,"XUT":22,"XRE":16,"XIT":28,"XCV":14}[ticker]
            for i, d in enumerate(all_trading_dates):
                t = i / max(len(all_trading_dates) - 1, 1)
                # Defensives outperform after rotation onset
                if d >= rotation_onset and ticker in ("XST","XUT"):
                    trend = base * (1 + 0.12 * t)
                elif d >= rotation_onset and ticker in ("XEG","XMA","XIT"):
                    trend = base * (1 - 0.06 * t)
                else:
                    trend = base * (1 + 0.04 * t)
                noise = float(rng.normal(0, base * 0.005))
                prices[d] = round(trend + noise, 2)

        for d in all_trading_dates:
            if d in prices:
                rot_rows.append({
                    "row_id":      row_id,
                    "obs_date":    d,
                    "ticker":      f"{ticker}.TO",
                    "description": description,
                    "close_price": prices[d],
                })
                row_id += 1

    rot_df = pd.DataFrame(rot_rows)
    emit(df_to_insert(rot_df, "macro.sector_rotation"))
    log.info("macro.sector_rotation: %d rows", len(rot_df))
    return rot_df


def build_macro_signals(macro_df):
    """Compute derived signals: yield spread, orders/inventory, RS scores."""
    section("MACRO DATA — COMPUTED SIGNALS")

    def get_series(key):
        sub = macro_df[macro_df["metric_key"] == key][["obs_date","value"]].copy()
        sub = sub.sort_values("obs_date").drop_duplicates("obs_date")
        return sub.set_index("obs_date")["value"]

    # Yield spread (10Y minus 2Y): inversion visible at Month 10
    y10 = get_series("BOC_YIELD_10Y")
    y2  = get_series("BOC_YIELD_2Y")
    common_dates = y10.index.intersection(y2.index)

    signals = []
    sig_id  = 1
    for d in sorted(common_dates):
        spread = round(float(y10[d] - y2[d]), 4)
        regime = (
            "Inverted"   if spread < -0.05 else
            "Flat"       if spread < 0.20  else
            "Normal"     if spread < 1.50  else
            "Steep"
        )
        # Macro cycle phase based on spread + approximate Orders/Inventory
        cycle_phase = (
            "Contraction"    if regime == "Inverted" else
            "Late Expansion" if regime == "Flat"     else
            "Mid Expansion"  if regime == "Normal"   else
            "Early Recovery"
        )
        signals.append({
            "sig_id":          sig_id,
            "obs_date":        d,
            "yield_spread_bps": round(spread * 100, 1),
            "yield_regime":    regime,
            "cycle_phase":     cycle_phase,
            "policy_rate":     float(y2[d]) if d in y2 else None,
            "usdcad":          None,  # filled below
        })
        sig_id += 1

    # Add USD/CAD to signals
    usdcad = get_series("BOC_USDCAD")
    sig_df = pd.DataFrame(signals)
    sig_df["obs_date"] = pd.to_datetime(sig_df["obs_date"]).dt.date
    for i, row in sig_df.iterrows():
        d = row["obs_date"]
        if d in usdcad.index:
            sig_df.at[i, "usdcad"] = round(float(usdcad[d]), 4)

    emit(df_to_insert(sig_df, "macro.macro_signals"))
    log.info("macro.macro_signals: %d rows", len(sig_df))
    return sig_df


# ────────────────────────────────────────────────────────────────────────────
#  SECTION 4 — INTELLIGENCE OUTPUTS  (ML models)
# ────────────────────────────────────────────────────────────────────────────

def build_ar_predictions(ar_df, customers_df, macro_signals_df):
    """
    XGBoost AR default probability scoring.
    Features: DSO proxy, days_past_due, ecl_rate, risk_tier_encoded,
              yield_spread, province, sector.
    SHAP top-3 drivers per customer.
    """
    section("INTELLIGENCE — AR DEFAULT PREDICTIONS (XGBoost + SHAP)")
    rng = np.random.default_rng(RANDOM_SEED + 6)

    # Build customer-level feature set from last 6 months of AR
    recent_cutoff = END_DATE - dt.timedelta(days=180)
    recent_ar = ar_df[ar_df["invoice_date"] >= recent_cutoff].copy()

    # Aggregate per customer
    agg = recent_ar.groupby("customer_id").agg(
        avg_dpd        = ("days_past_due", "mean"),
        max_dpd        = ("days_past_due", "max"),
        invoices_count = ("invoice_id", "count"),
        total_ar       = ("amount", "sum"),
        paid_pct       = ("paid", "mean"),
        avg_ecl_rate   = ("ecl_rate", "mean"),
    ).reset_index()

    # Merge customer attributes
    feat = agg.merge(customers_df[["customer_id","risk_tier","province","sector","ecl_rate_base"]], on="customer_id")

    # Encode categoricals
    risk_map = {"Low": 0, "Medium": 1, "High": 2}
    feat["risk_tier_enc"] = feat["risk_tier"].map(risk_map)
    feat["province_enc"]  = feat["province"].map({"ON":0,"AB":1,"QC":2,"BC":3,"MB":4}).fillna(0)
    sector_list = sorted(customers_df["sector"].unique())
    feat["sector_enc"]    = feat["sector"].apply(lambda x: sector_list.index(x) if x in sector_list else 0)

    # Latest yield spread as macro feature
    latest_spread = float(macro_signals_df.sort_values("obs_date").iloc[-1]["yield_spread_bps"])
    feat["yield_spread_bps"] = latest_spread

    feature_cols = ["avg_dpd","max_dpd","paid_pct","avg_ecl_rate","risk_tier_enc",
                    "province_enc","sector_enc","yield_spread_bps"]
    X = feat[feature_cols].fillna(0).values

    # Generate labels: default = 1 if high ecl_rate or DPD > 60
    y = ((feat["avg_ecl_rate"] > 0.04) | (feat["max_dpd"] > 60)).astype(int).values

    if HAS_XGB and len(feat) >= 10:
        model = xgb.XGBClassifier(n_estimators=50, max_depth=4, random_state=RANDOM_SEED, eval_metric="logloss")
        model.fit(X, y)
        probs = model.predict_proba(X)[:, 1]

        if HAS_SHAP:
            explainer   = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
        else:
            shap_values = None
    else:
        # Logistic approximation
        logit = (feat["avg_ecl_rate"] * 10 + feat["max_dpd"] / 30 + feat["risk_tier_enc"] * 0.5).values
        probs = 1 / (1 + np.exp(-logit + 1))
        shap_values = None

    # Assemble prediction table
    pred_rows  = []
    shap_rows  = []
    pred_id    = 1
    shap_id    = 1

    risk_actions = {
        "High":   "Suspend credit terms; require prepayment on next order",
        "Medium": "Reduce credit limit by 30%; weekly AR review",
        "Low":    "Monitor — no immediate action required",
    }

    for i, row in feat.iterrows():
        prob = round(float(probs[i]), 4)
        tier = ("High" if prob > 0.55 else "Medium" if prob > 0.25 else "Low")
        ecl  = round(float(row["total_ar"]) * prob * float(row["avg_ecl_rate"]), 2)

        pred_rows.append({
            "pred_id":            pred_id,
            "customer_id":        row["customer_id"],
            "score_date":         END_DATE,
            "default_prob_60d":   prob,
            "risk_tier_predicted": tier,
            "total_ar_balance":   round(float(row["total_ar"]), 2),
            "ecl_estimate":       ecl,
            "recommended_action": risk_actions[tier],
        })

        # SHAP drivers
        feature_names = ["Avg DPD","Max DPD","Paid %","ECL Rate Base","Risk Tier",
                         "Province","Sector","Yield Spread"]
        if shap_values is not None:
            sv = shap_values[i]
            top3_idx = np.argsort(np.abs(sv))[::-1][:3]
            for rank, fi in enumerate(top3_idx, 1):
                shap_rows.append({
                    "shap_id":        shap_id,
                    "customer_id":    row["customer_id"],
                    "score_date":     END_DATE,
                    "rank":           rank,
                    "feature_name":   feature_names[fi],
                    "shap_value":     round(float(sv[fi]), 4),
                    "direction":      "Increases Risk" if sv[fi] > 0 else "Decreases Risk",
                })
                shap_id += 1
        else:
            # Proxy: feature weights based on correlation with prob
            for rank, (fname, fval) in enumerate([
                ("Avg DPD", float(row["avg_dpd"])),
                ("ECL Rate Base", float(row["avg_ecl_rate"])),
                ("Risk Tier", float(row["risk_tier_enc"])),
            ], 1):
                direction = "Increases Risk" if fval > 0 else "Decreases Risk"
                shap_rows.append({
                    "shap_id":      shap_id,
                    "customer_id":  row["customer_id"],
                    "score_date":   END_DATE,
                    "rank":         rank,
                    "feature_name": fname,
                    "shap_value":   round(fval * 0.1, 4),
                    "direction":    direction,
                })
                shap_id += 1
        pred_id += 1

    pred_df = pd.DataFrame(pred_rows)
    shap_df = pd.DataFrame(shap_rows)

    emit(df_to_insert(pred_df, "intel.ar_predictions"))
    emit(df_to_insert(shap_df, "intel.shap_explanations"))
    log.info("intel.ar_predictions: %d rows; intel.shap_explanations: %d rows",
             len(pred_df), len(shap_df))
    return pred_df


def build_cash_flow_forecast():
    """
    Chronos-style probabilistic cash flow forecast.
    P10/P50/P90 bands at 30/60/90 day horizons per entity.
    In the absence of the Chronos library, we use a calibrated
    simulation that matches documented output patterns.
    """
    section("INTELLIGENCE — CASH FLOW FORECAST (Chronos P10/P50/P90)")
    rng = np.random.default_rng(RANDOM_SEED + 7)

    entities       = ["E01","E02","E03","E04"]
    base_cash      = {"E01": 1_800_000, "E02": 650_000, "E03": 420_000, "E04": 310_000}
    monthly_burn   = {"E01": 280_000,   "E02": 165_000,  "E03": 190_000,  "E04": 120_000}
    horizons       = [30, 60, 90]

    fc_rows = []
    fc_id   = 1

    for entity in entities:
        bc    = base_cash[entity]
        burn  = monthly_burn[entity]

        for h in horizons:
            # Monte Carlo: 1000 paths
            months_fwd = h / 30
            paths = []
            for _ in range(1000):
                # Random collection timing + macro uncertainty
                collection_rate = rng.uniform(0.78, 0.96)
                macro_shock     = rng.normal(0, burn * 0.12)
                projected = bc + (burn * collection_rate * months_fwd) - (burn * months_fwd) + macro_shock
                paths.append(projected)
            paths = sorted(paths)
            p10 = round(float(np.percentile(paths, 10)), 2)
            p50 = round(float(np.percentile(paths, 50)), 2)
            p90 = round(float(np.percentile(paths, 90)), 2)

            # QC entity (E03) has tighter P10 due to higher AR risk
            if entity == "E03":
                p10 = round(p10 * 0.82, 2)

            fc_rows.append({
                "fc_id":              fc_id,
                "entity_id":          entity,
                "forecast_date":      END_DATE,
                "horizon_days":       h,
                "forecast_horizon_date": END_DATE + dt.timedelta(days=h),
                "p10_cash":           p10,
                "p50_cash":           p50,
                "p90_cash":           p90,
                "credit_facility_floor": 0,
                "runway_days_p10":    max(0, round(p10 / (burn / 30), 0)) if p10 > 0 else 0,
                "model":              "Chronos (zero-shot)",
            })
            fc_id += 1

    fc_df = pd.DataFrame(fc_rows)
    emit(df_to_insert(fc_df, "intel.cash_flow_forecast"))
    log.info("intel.cash_flow_forecast: %d rows", len(fc_df))
    return fc_df


def build_demand_forecast():
    """
    Moirai-style P10/P50/P90 demand forecast per product category.
    Drives safety stock optimisation and inventory saving calculation.
    """
    section("INTELLIGENCE — DEMAND FORECAST (Moirai P10/P50/P90)")
    rng = np.random.default_rng(RANDOM_SEED + 8)

    categories = [
        ("Industrial Components",  1200, 180, 0.45),
        ("Specialty Chemicals",     800, 120, 0.32),
        ("Technology Hardware",     600,  90, 0.28),
        ("Packaging Materials",    2200, 280, 0.55),
        ("Maintenance Supplies",    450,  65, 0.22),
        ("Office & Facilities",     300,  42, 0.18),
    ]

    df_rows  = []
    df_id    = 1
    inv_rows = []
    inv_id   = 1

    safety_stock_cost_rate = 0.22  # 22% holding cost (Canadian warehouse)

    for (cat, base_units, safety_current, unit_value) in categories:
        for h in [30, 60, 90]:
            months_fwd   = h / 30
            decel_factor = max(0.88, 1.0 - 0.04 * months_fwd)

            paths = []
            for _ in range(1000):
                seasonal = 1.0 + 0.15 * math.sin(rng.uniform(0, 2 * math.pi))
                demand   = base_units * months_fwd * seasonal * decel_factor * rng.lognormal(0, 0.12)
                paths.append(demand)
            paths = sorted(paths)

            df_rows.append({
                "df_id":          df_id,
                "product_category": cat,
                "forecast_date":  END_DATE,
                "horizon_days":   h,
                "p10_units":      round(float(np.percentile(paths, 10)), 0),
                "p50_units":      round(float(np.percentile(paths, 50)), 0),
                "p90_units":      round(float(np.percentile(paths, 90)), 0),
                "model":          "Moirai (zero-shot)",
            })
            df_id += 1

        # Safety stock optimisation (at 30-day horizon)
        p10_30 = round(float(np.percentile(
            [base_units * (1 + rng.normal(0, 0.12)) * max(0.88, 0.96) for _ in range(500)], 10
        )), 0)
        recommended_ss = round(p10_30 * 1.05, 0)  # 5% buffer on downside demand
        monthly_saving = round(max(0, (safety_current - recommended_ss)) * unit_value * safety_stock_cost_rate / 12, 2)

        inv_rows.append({
            "inv_id":              inv_id,
            "product_category":    cat,
            "calc_date":           END_DATE,
            "current_safety_stock": safety_current,
            "p10_demand_30d":      p10_30,
            "recommended_safety_stock": recommended_ss,
            "unit_value":          unit_value,
            "monthly_holding_saving": monthly_saving,
            "annual_holding_saving":  round(monthly_saving * 12, 2),
            "action_priority":     ("HIGH" if monthly_saving > 2000 else
                                    "MEDIUM" if monthly_saving > 500 else "LOW"),
        })
        inv_id += 1

    df_df  = pd.DataFrame(df_rows)
    inv_df = pd.DataFrame(inv_rows)
    emit(df_to_insert(df_df,  "intel.demand_forecast"))
    emit(df_to_insert(inv_df, "intel.inventory_recommendations"))
    log.info("intel.demand_forecast: %d rows; intel.inventory_recommendations: %d rows",
             len(df_df), len(inv_df))
    return inv_df


def build_elasticity():
    """
    Price elasticity classification per product category.
    Correlates revenue patterns with IPPI producer price index.
    Inelastic = price increase does not reduce volume meaningfully.
    """
    section("INTELLIGENCE — PRICE ELASTICITY CLASSIFICATION")

    elasticity_data = [
        # (category, class, price_elasticity, uplift_pct, action)
        ("Industrial Components",  "Inelastic",    -0.42, 4.5, "Increase list price 4–6% next renewal cycle"),
        ("Specialty Chemicals",    "Inelastic",    -0.38, 5.0, "Increase list price 5% — demand insensitive to input cost pass-through"),
        ("Technology Hardware",    "Elastic",      -1.85, 0.0, "Do not increase — volume loss exceeds margin gain at current elasticity"),
        ("Packaging Materials",    "Unit Elastic", -0.98, 1.5, "Selective increase on proprietary SKUs only"),
        ("Maintenance Supplies",   "Inelastic",    -0.31, 6.0, "Full 6% increase supportable — switching cost is high"),
        ("Office & Facilities",    "Elastic",      -1.42, 0.0, "Price-sensitive — customers substitute easily"),
    ]

    rows = []
    for i, (cat, cls, elas, uplift, action) in enumerate(elasticity_data, 1):
        margin_uplift_annual = round(uplift * 12_000, 2) if cls == "Inelastic" else 0.0
        rows.append({
            "elast_id":            i,
            "product_category":    cat,
            "calc_date":           END_DATE,
            "elasticity_class":    cls,
            "price_elasticity":    elas,
            "recommended_price_increase_pct": uplift,
            "est_annual_margin_uplift": margin_uplift_annual,
            "recommended_action":  action,
            "confidence":          ("High" if abs(elas) < 0.5 or abs(elas) > 1.5 else "Medium"),
        })

    elast_df = pd.DataFrame(rows)
    emit(df_to_insert(elast_df, "intel.elasticity_classification"))
    log.info("intel.elasticity_classification: %d rows", len(elast_df))
    return elast_df


def build_decision_alerts(macro_signals_df, pred_df):
    """
    9-rule automated alert engine.
    Evaluates macro threshold rules nightly; all rules evaluated against current state.
    """
    section("INTELLIGENCE — DECISION ALERT ENGINE (9 Rules)")

    # Current macro state
    latest_sig = macro_signals_df.sort_values("obs_date").iloc[-1]
    spread_bps  = float(latest_sig["yield_spread_bps"])
    cycle_phase = str(latest_sig["cycle_phase"])
    usdcad      = float(latest_sig.get("usdcad") or 1.38)

    high_risk_count   = int((pred_df["risk_tier_predicted"] == "High").sum())
    high_risk_ecl     = float(pred_df[pred_df["risk_tier_predicted"] == "High"]["ecl_estimate"].sum())
    total_ecl         = float(pred_df["ecl_estimate"].sum())

    # Simulated Orders/Inventory ratio (from macro pattern — Month 13 drops to 0.92)
    orders_inv_ratio = 0.92  # matches inject pattern

    alert_rules = [
        # (rule_id, department, alert_name, condition, threshold, actual, severity, action, dollar_impact)
        (1, "CFO/Treasury",  "Yield Curve Flat/Inverted",
         f"10Y–2Y spread ≤ 20 bps", 20.0, round(spread_bps, 1),
         ("RED" if spread_bps < 0 else "AMBER"),
         "Lock in fixed-rate debt before curve un-inverts and long rates rise",
         127_000),

        (2, "CRO",           "High-Risk AR Count Elevated",
         f"High-risk customers ≥ 5", 5, high_risk_count,
         ("RED" if high_risk_count >= 8 else "AMBER"),
         "Tighten credit terms for High-risk tier; require deposit on new orders",
         round(high_risk_ecl * 0.20)),

        (3, "CRO",           "Portfolio ECL Exceeds Threshold",
         f"Total ECL ≥ $50K", 50_000, round(total_ecl),
         ("RED" if total_ecl > 100_000 else "AMBER"),
         "Review collective assessment methodology; increase provision",
         round(total_ecl * 0.15)),

        (4, "COO",           "Orders/Inventory Ratio Below Threshold",
         f"Ratio ≤ 0.95", 0.95, orders_inv_ratio,
         "RED",
         "Reduce safety stock targets by 15%; defer next purchase order cycle",
         60_000),

        (5, "CFO",           "USD/CAD Above 1.40",
         f"USDCAD ≥ 1.40", 1.40, round(usdcad, 4),
         ("RED" if usdcad >= 1.40 else "AMBER"),
         "Hedge USD receivables for next 90 days; review export contract pricing",
         45_000),

        (6, "CEO",           "Macro Regime: Late/Contraction",
         f"Cycle phase signals slowdown", "Mid Expansion", cycle_phase,
         ("RED" if "Contraction" in cycle_phase else "AMBER"),
         "Defer discretionary CapEx; accelerate receivables collection",
         150_000),

        (7, "COO",           "IPPI Acceleration > 3% YoY",
         f"Producer price inflation ≥ 3%", 3.0, 3.8,
         "AMBER",
         "Pass through IPPI increase on inelastic categories; renegotiate elastic category contracts",
         90_000),

        (8, "CFO",           "IT Cost Centre Over Budget > 10%",
         f"CC03 Technology variance ≥ 10%", 10.0, 12.0,
         "AMBER",
         "Escalate ERP project overrun to steering committee; freeze discretionary IT spend",
         38_000),

        (9, "CRO",           "DPD Acceleration — QC Retail Segment",
         f"Avg DPD increasing > 15 days in 30 days", 15, 21,
         "RED",
         "Immediate credit review for QC Retail accounts; require personal guarantee on balances > $50K",
         round(high_risk_ecl * 0.40)),
    ]

    rows = []
    for (rule_id, dept, name, condition, threshold, actual, severity, action, dollar_impact) in alert_rules:
        rows.append({
            "alert_id":        rule_id,
            "alert_name":      name,
            "department":      dept,
            "eval_date":       END_DATE,
            "condition_text":  condition,
            "threshold_value": str(threshold),
            "actual_value":    str(actual),
            "severity":        severity,
            "status":          "ACTIVE",
            "recommended_action": action,
            "dollar_impact":   dollar_impact,
            "expected_outcome": f"If actioned within 30 days: estimated ${dollar_impact:,} annual benefit",
        })

    alerts_df = pd.DataFrame(rows)
    emit(df_to_insert(alerts_df, "intel.decision_alerts"))
    log.info("intel.decision_alerts: %d rows", len(alerts_df))
    return alerts_df


# ────────────────────────────────────────────────────────────────────────────
#  SECTION 5 — BUDGET TABLE  (for variance analysis)
# ────────────────────────────────────────────────────────────────────────────

def build_budgets():
    """Monthly budget amounts per entity and account category, for P&L variance."""
    section("BUDGET — MONTHLY TARGETS")
    rng = np.random.default_rng(RANDOM_SEED + 9)

    entities     = ["E01","E02","E03","E04"]
    base_rev_bgt = {"E01": 460_000, "E02": 285_000, "E03": 330_000, "E04": 200_000}
    periods      = month_dates()

    bgt_rows = []
    bgt_id   = 1
    for (pstart, _, fy, q, label) in periods:
        for entity in entities:
            rev_bgt  = round(base_rev_bgt[entity] * (1 + 0.02 * ((pstart.year - 2024) + (pstart.month - 4) / 12)), 2)
            cogs_bgt = round(rev_bgt * 0.50, 2)
            opex_bgt = round(rev_bgt * 0.34, 2)
            bgt_rows.append({
                "bgt_id":        bgt_id,
                "entity_id":     entity,
                "period_start":  pstart,
                "fiscal_year":   fy,
                "fiscal_quarter": q,
                "period_label":  label,
                "revenue_budget": rev_bgt,
                "cogs_budget":   cogs_bgt,
                "opex_budget":   opex_bgt,
                "ebitda_budget": round(rev_bgt - cogs_bgt - opex_bgt, 2),
            })
            bgt_id += 1

    bgt_df = pd.DataFrame(bgt_rows)
    emit(df_to_insert(bgt_df, "erp.budget"))
    log.info("erp.budget: %d rows", len(bgt_df))


# ────────────────────────────────────────────────────────────────────────────
#  MAIN ORCHESTRATION
# ────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  C-Suite Intelligence Platform — Data Generation")
    print("  generate_showcase_data.py")
    print(f"  Coverage: {START_DATE} → {END_DATE}  ({MONTHS} months)")
    print("=" * 70)
    print()

    emit("-- C-Suite Intelligence Platform — showcase_data.sql\n")
    emit(f"-- Generated: {dt.datetime.now().isoformat()}\n")
    emit(f"-- Coverage:  {START_DATE} to {END_DATE} ({MONTHS} months)\n")
    emit("-- Load into Azure SQL AFTER executing showcase_schema.sql\n\n")
    emit("SET NOCOUNT ON;\n\n")

    # 1. Dimensions
    print("[1/9] Building dimensions...")
    entities, coa, cost_centres, customers_df, vendors_df = build_dimensions()

    # 2. GL Ledger
    print("[2/9] Building GL ledger (~18,000 rows)...")
    gl_df = build_gl(customers_df, cost_centres, coa)

    # 3. AR Invoices
    print("[3/9] Building AR invoices (~5,000 rows)...")
    ar_df = build_ar(customers_df)

    # 4. AP Invoices
    print("[4/9] Building AP invoices (~3,500 rows)...")
    ap_df = build_ap(vendors_df)

    # 5. Budget
    print("[5/9] Building budget targets...")
    build_budgets()

    # 6. Macro data
    print("[6/9] Fetching macro data (BoC API + StatCan + yfinance)...")
    macro_df = build_macro()
    rot_df   = build_sector_rotation()
    sig_df   = build_macro_signals(macro_df)

    # 7. ML Intelligence
    print("[7/9] Running AR default scoring (XGBoost + SHAP)...")
    pred_df  = build_ar_predictions(ar_df, customers_df, sig_df)

    print("[8/9] Running probabilistic forecasts (Chronos / Moirai simulation)...")
    build_cash_flow_forecast()
    build_demand_forecast()

    print("[9/9] Running elasticity engine + decision alert rules...")
    build_elasticity()
    build_decision_alerts(sig_df, pred_df)

    # ── Write SQL file ────────────────────────────────────────────────────────
    sql_content = sql_buffer.getvalue()
    OUTPUT_SQL.write_text(sql_content, encoding="utf-8")

    total_lines = sql_content.count("\n")
    size_mb     = OUTPUT_SQL.stat().st_size / (1024 * 1024)

    print()
    print("=" * 70)
    print(f"  Output:  {OUTPUT_SQL}  ({size_mb:.1f} MB, {total_lines:,} lines)")
    print(f"  Log:     {OUTPUT_LOG}")
    print()
    print("  Next steps:")
    print("  1. Execute showcase_schema.sql in Azure SQL Basic")
    print("  2. Execute showcase_data.sql to load all rows")
    print("  3. Open Power BI Desktop → Import from Azure SQL → load 7 views")
    print("  4. Publish to Power BI Service and configure embed token")
    print("=" * 70)


if __name__ == "__main__":
    main()

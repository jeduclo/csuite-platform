"""
CFO Intelligence App — Plotly Dash
Replicates all 8 Power BI pages with matching charts and KPI cards.
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, ctx, ALL, State
import sqlalchemy
import anthropic
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# In-memory cache — generated once per page per session, never regenerated
_brief_cache = {}

# Data cache — loaded once at startup
_data_cache = {}

def get_cached(key, sql):
    if key not in _data_cache:
        _data_cache[key] = query(sql)
    return _data_cache[key].copy()

def preload_data():
    """Load all DB data once at startup."""
    print("Preloading data cache...")
    get_cached("gl", """
        SELECT g.period_start, g.credit_amount, g.debit_amount, c.category, c.account_name
        FROM erp.gl_ledger g
        JOIN dim.chart_of_accounts c ON g.account_id = c.account_id
        WHERE g.period_start >= DATEADD(month, -28, GETDATE())
    """)
    get_cached("ar", "SELECT invoice_date, due_date, amount, paid, days_past_due, customer_id FROM erp.ar_invoices")
    get_cached("ap", "SELECT invoice_date, amount, paid, vendor_id FROM erp.ap_invoices")
    get_cached("cash_burn", "SELECT week_num, week_label, avg_cash_collected, avg_cash_burn, running_balance, scenario FROM intel.cash_burn_weekly ORDER BY week_num")
    get_cached("covenant", "SELECT period, dscr_proxy, debt_ebitda, net_debt, total_liabilities, scenario FROM intel.covenant_tracker ORDER BY period")
    get_cached("forecast", "SELECT forecast_month, revenue_forecast, lower_bound, upper_bound FROM intel.revenue_forecast_12m ORDER BY forecast_month")
    get_cached("macro", "SELECT obs_date, metric_key, value FROM macro.economic_indicators ORDER BY obs_date")
    get_cached("sector", "SELECT obs_date, ticker, description, close_price FROM macro.sector_rotation ORDER BY obs_date")
    get_cached("customers", "SELECT customer_id, customer_name FROM dim.customers")
    get_cached("budget", "SELECT SUM(budget_amount) as total FROM erp.budget")
    print("Data cache loaded.")

def gemini_summary(page_title, kpis: dict, question: str) -> str:
    if page_title in _brief_cache:
        return _brief_cache[page_title]
    if not ANTHROPIC_API_KEY:
        return "Add ANTHROPIC_API_KEY to enable AI summaries."
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        kpi_text = "\n".join([f"- {k}: {v}" for k, v in kpis.items()])
        prompt = f"""You are a CFO advisor. Analyze these metrics from the '{page_title}' page.
Business question: {question}

Key metrics:
{kpi_text}

Write a 3-sentence CFO briefing. Be direct and specific. Flag risks. No vanity metrics. No filler words.
Start with the most important signal. Use plain language a CFO can act on."""
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        result = message.content[0].text.strip()
        _brief_cache[page_title] = result
        return result
    except Exception as e:
        return f"AI summary unavailable: {e}"

# ── DB ────────────────────────────────────────────────────────────────────────

_raw_url = os.environ.get("DATABASE_URL", "")
import re as _re
_m = _re.match(r"mssql\+pyodbc://([^:]+):([^@]+)@([^/]+)/([^?]+)", _raw_url)
if _m:
    _user, _pwd, _host, _db = _m.groups()
    from urllib.parse import unquote as _unquote
    _pwd = _unquote(_pwd)
    DATABASE_URL = f"mssql+pymssql://{_user}:{_pwd}@{_host}/{_db}"
else:
    DATABASE_URL = _raw_url

def get_engine():
    return sqlalchemy.create_engine(DATABASE_URL, connect_args={"timeout": 15})

def query(sql: str) -> pd.DataFrame:
    try:
        with get_engine().connect() as conn:
            result = conn.execute(sqlalchemy.text(sql))
            rows = result.fetchall()
            cols = result.keys()
            import decimal
            converted = []
            for row in rows:
                converted.append([
                    float(v) if isinstance(v, decimal.Decimal) else v
                    for v in row
                ])
            return pd.DataFrame(converted, columns=list(cols))
    except Exception as e:
        print(f"DB error: {e}")
        return pd.DataFrame()

# ── DESIGN TOKENS ─────────────────────────────────────────────────────────────

NAVY    = "#F8FAFC"
NAVY2   = "#FFFFFF"
BLUE    = "#1E3A8A"
BLUE2   = "#2563EB"
SLATE   = "#64748B"
LIGHT   = "#0F172A"
GREEN   = "#059669"
AMBER   = "#D97706"
RED     = "#DC2626"
LBLUE   = "#4472C4"
PURPLE  = "#7C3AED"
TEAL    = "#0D9488"
PINK    = "#DB2777"

FONT    = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT, color="#475569", size=11),
    margin=dict(l=48, r=20, t=44, b=44),
    xaxis=dict(gridcolor="#F1F5F9", showline=False, zeroline=False,
               tickfont=dict(size=10), title_font=dict(size=11)),
    yaxis=dict(gridcolor="#F1F5F9", showline=False, zeroline=False,
               tickfont=dict(size=10), title_font=dict(size=11)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10), orientation="h",
                yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#FFFFFF", font_size=11, font_family=FONT, font_color="#0F172A"),
)

# ── UI HELPERS ────────────────────────────────────────────────────────────────

def kpi(value, label, color=LBLUE, size="26px"):
    return html.Div([
        html.Div(value, style={"fontSize": size, "fontWeight": "700", "color": color,
                               "fontFamily": "monospace", "lineHeight": "1.1"}),
        html.Div(label, style={"fontSize": "10px", "color": SLATE, "textTransform": "uppercase",
                               "letterSpacing": "0.07em", "marginTop": "6px"}),
    ], style={"background": "#FFFFFF", "border": "1px solid #E2E8F0",
              "borderRadius": "10px", "padding": "16px 20px", "flex": "1", "minWidth": "140px",
              "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"})

def kpi_row(cards):
    return html.Div(cards, style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginBottom": "20px"})

def chart_title(title):
    return html.Div(title, style={"fontSize": "12px", "fontWeight": "600", "color": BLUE,
                                  "marginBottom": "8px", "paddingBottom": "6px",
                                  "borderBottom": "1px solid #E2E8F0"})

def chart_box(title, fig, half=False):
    return html.Div([
        chart_title(title),
        dcc.Graph(figure=fig, config={"displayModeBar": False},
                  style={"height": "260px"}),
    ], style={"flex": "1 1 45%" if half else "1 1 100%", "minWidth": "300px",
              "background": "#FFFFFF", "borderRadius": "10px",
              "padding": "16px", "border": "1px solid #E2E8F0",
              "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"})

def charts_row(children):
    return html.Div(children, style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"})

def page_header(num, title, question):
    return html.Div([
        html.Div([
            html.Span(f"CFO {num}", style={"fontSize": "11px", "color": BLUE, "fontWeight": "700",
                                           "letterSpacing": "0.08em", "textTransform": "uppercase"}),
            html.H2(title, style={"fontSize": "18px", "fontWeight": "800", "color": "#0F172A",
                                  "margin": "4px 0 0", "letterSpacing": "-0.01em"}),
        ]),
        html.Div(question, style={"fontSize": "12px", "color": SLATE, "fontStyle": "italic",
                                  "alignSelf": "flex-end"}),
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start",
              "marginBottom": "20px", "paddingBottom": "14px",
              "borderBottom": "1px solid #E2E8F0"})

def empty_fig(msg="No data available"):
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, showarrow=False,
                       font=dict(color=SLATE, size=13, family=FONT), xref="paper", yref="paper")
    fig.update_layout(**BASE_LAYOUT)
    return fig

def apply_layout(fig, **kwargs):
    layout = {**BASE_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig

RISK_KEYWORDS = [
    "risk", "breach", "deficit", "negative", "declining", "insufficient",
    "immediate", "critical", "urgent", "concern", "below", "pressure",
    "compressing", "deteriorat", "cash problem", "covenant", "overdue",
]
POSITIVE_KEYWORDS = [
    "healthy", "strong", "improving", "above", "efficient", "positive",
    "growing", "stable", "solid", "adequate", "exceeding",
]

def highlight_text(text: str):
    """Split text into spans, highlighting risk/positive keywords."""
    import re
    words = re.split(r"(\s+)", text)
    spans = []
    for word in words:
        lower = word.lower().strip(".,;:*#")
        if any(k in lower for k in RISK_KEYWORDS):
            spans.append(html.Span(word, style={"color": "#DC2626", "fontWeight": "700",
                                                "fontStyle": "normal"}))
        elif any(k in lower for k in POSITIVE_KEYWORDS):
            spans.append(html.Span(word, style={"color": "#059669", "fontWeight": "700",
                                                "fontStyle": "normal"}))
        else:
            spans.append(word)
    return spans

def ai_panel(summary_text: str, loading: bool = False):
    if loading:
        body = html.Div([
            html.Span("⏳ ", style={"fontSize": "12px"}),
            html.Span("Generating CFO briefing...", style={
                "fontSize": "12px", "color": "#94A3B8", "fontStyle": "italic"
            }),
        ])
    else:
        # Strip markdown artifacts
        import re
        clean = re.sub(r"[#*]+", "", summary_text).strip()
        # Remove redundant "CFO Briefing: Title" prefix Claude adds
        import re as _re
        clean = _re.sub(r"^CFO Briefing:\s*[^.]+\.\s*", "", clean).strip()
        body = html.P(highlight_text(clean), style={
            "fontSize": "13.5px", "color": "#1E293B", "lineHeight": "1.9",
            "margin": "0",
        })
    return html.Div([
        html.Div([
            html.Span("AI", style={
                "background": "#1E3A8A", "color": "#fff",
                "fontSize": "9px", "fontWeight": "700",
                "padding": "2px 6px", "borderRadius": "4px",
                "letterSpacing": "0.06em", "marginRight": "8px",
            }),
            html.Span("CFO Briefing — Claude Haiku", style={
                "fontSize": "11px", "fontWeight": "600", "color": "#1E3A8A",
            }),
        ], style={"marginBottom": "8px", "display": "flex", "alignItems": "center"}),
        body,
    ], style={
        "background": "#EFF6FF",
        "border": "1px solid #BFDBFE",
        "borderLeft": "4px solid #1E3A8A",
        "borderRadius": "8px",
        "padding": "14px 18px",
        "marginBottom": "20px",
    })

# ── PAGE 1 — FINANCIAL VELOCITY ───────────────────────────────────────────────

def page_financial_velocity():
    df = get_cached("gl", "")
    if df.empty:
        return html.Div("No GL data available", style={"color": SLATE, "padding": "40px"})

    df["month"] = pd.to_datetime(df["period_start"]).dt.to_period("M").astype(str)
    rev_df  = df[df["category"]=="Revenue"]
    cogs_df = df[df["category"]=="COGS"]
    opex_df = df[df["category"]=="OpEx"]

    rev_total  = rev_df["credit_amount"].sum()
    opex_total = opex_df["debit_amount"].sum() + cogs_df["debit_amount"].sum()
    cogs_total = cogs_df["debit_amount"].sum()
    gross      = rev_total - cogs_total
    ebitda     = rev_total - opex_total
    ebitda_pct = ebitda / rev_total * 100 if rev_total else 0

    # AR collection rate
    df_ar = get_cached("ar", "")
    if not df_ar.empty:
        collected = df_ar[df_ar["paid"]==True]["amount"].sum()
        total_ar  = df_ar["amount"].sum()
        coll_rate = collected / total_ar * 100 if total_ar else 0
    else:
        coll_rate = 0

    # ── Waterfall: margin bridge
    wf_fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute","relative","relative","total"],
        x=["Revenue","COGS","OpEx","Total"],
        y=[rev_total/1e6, -cogs_total/1e6, -(opex_total-cogs_total)/1e6, 0],
        connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)),
        increasing=dict(marker_color="#1E3A8A"),
        decreasing=dict(marker_color="#94A3B8"),
        totals=dict(marker_color="#2563EB"),
        text=[f"${rev_total/1e6:.1f}M", f"-${cogs_total/1e6:.1f}M",
              f"-${(opex_total-cogs_total)/1e6:.1f}M", f"${ebitda/1e6:.1f}M"],
        textfont=dict(size=10, color=LIGHT),
    ))
    apply_layout(wf_fig, title=None, yaxis_tickprefix="$", yaxis_ticksuffix="M",
                 margin=dict(l=48, r=10, t=10, b=36))

    # ── Revenue by account
    rev_by_acct = rev_df.groupby("account_name")["credit_amount"].sum().nlargest(4).reset_index()
    acct_fig = go.Figure(go.Bar(
        x=rev_by_acct["account_name"],
        y=rev_by_acct["credit_amount"]/1e6,
        marker_color=BLUE, opacity=0.85,
        text=[f"${v:.1f}M" for v in rev_by_acct["credit_amount"]/1e6],
        textposition="outside", textfont=dict(size=10, color=LIGHT),
    ))
    apply_layout(acct_fig, margin=dict(l=48, r=10, t=10, b=80),
                 yaxis_tickprefix="$", yaxis_ticksuffix="M",
                 xaxis=dict(tickfont=dict(size=9), gridcolor="rgba(255,255,255,0.05)",
                            showline=False, zeroline=False))

    # ── Monthly revenue + EBITDA margin dual-axis
    rev_mo  = rev_df.groupby("month")["credit_amount"].sum().reset_index()
    opex_mo = df[df["category"].isin(["OpEx","COGS"])].groupby("month")["debit_amount"].sum().reset_index()
    merged  = rev_mo.merge(opex_mo, on="month", how="left").fillna(0)
    merged["ebitda_pct"] = (merged["credit_amount"] - merged["debit_amount"]) / merged["credit_amount"].replace(0,1) * 100

    dual_fig = make_subplots(specs=[[{"secondary_y": True}]])
    dual_fig.add_trace(go.Bar(x=merged["month"], y=merged["credit_amount"]/1e6,
                              name="Revenue Monthly", marker_color=BLUE, opacity=0.7), secondary_y=False)
    dual_fig.add_trace(go.Scatter(x=merged["month"], y=merged["ebitda_pct"],
                                  name="EBITDA Margin %", line=dict(color=GREEN, width=2),
                                  mode="lines+markers", marker=dict(size=3)), secondary_y=True)
    dual_fig.add_hline(y=0, line_color=RED, line_width=1, secondary_y=True)
    apply_layout(dual_fig, margin=dict(l=48, r=48, t=10, b=48),
                 yaxis=dict(tickprefix="$", ticksuffix="M", gridcolor="rgba(255,255,255,0.05)",
                            showline=False, zeroline=False, tickfont=dict(size=10), title_font=dict(size=11)),
                 yaxis2=dict(ticksuffix="%", gridcolor="rgba(0,0,0,0)", showline=False,
                             zeroline=False, tickfont=dict(size=10)))

    ebitda_color = GREEN if ebitda_pct > 0 else RED
    return html.Div([
        page_header(1, "Financial Velocity", "Is the business generating cash efficiently?"),
        html.Div(id="ai-brief", children=ai_panel("Analyzing financials...", loading=True)),
        kpi_row([
            kpi(f"${rev_total/1e6:.1f}M", "Revenue YTD"),
            kpi(f"${opex_total/1e6:.1f}M", "Total OpEx", AMBER),
            kpi(f"{ebitda_pct:.1f}%", "EBITDA Margin %", ebitda_color),
            kpi(f"{coll_rate:.1f}%", "Collection Rate", GREEN),
        ]),
        charts_row([
            chart_box("Where is margin being lost?", wf_fig, half=True),
            chart_box("Which accounts drive revenue?", acct_fig, half=True),
        ]),
        chart_box("Is our margin improving or compressing?", dual_fig),
    ])


# ── PAGE 2 — WORKING CAPITAL ──────────────────────────────────────────────────

def page_working_capital():
    df_ar = get_cached("ar", "").merge(
        get_cached("customers", "")[["customer_id","customer_name"]],
        on="customer_id", how="left")
    df_ap = get_cached("ap", "")

    if df_ar.empty:
        return html.Div("No AR data", style={"color": SLATE, "padding": "40px"})

    df_ar["due_date"] = pd.to_datetime(df_ar["due_date"])
    unpaid = df_ar[df_ar["paid"]==False]
    ar_out = unpaid["amount"].sum()
    ap_out = df_ap[df_ap["paid"]==False]["amount"].sum() if not df_ap.empty else 0

    # DSO: simple days past due average
    dso = df_ar["days_past_due"].mean() if "days_past_due" in df_ar.columns else 0
    coll_rate = df_ar[df_ar["paid"]==True]["amount"].sum() / df_ar["amount"].sum() * 100

    # Cash runway (weeks): AR outstanding / avg weekly AP burn
    weekly_ap = df_ap["amount"].sum() / 52 if not df_ap.empty else 1
    runway = ar_out / weekly_ap if weekly_ap else 0

    # ── Scatter: customers — days past due vs AR outstanding
    cust_risk = unpaid.groupby("customer_name").agg(
        ar=("amount","sum"), dpd=("days_past_due","mean")).reset_index()
    scatter_fig = go.Figure(go.Scatter(
        x=cust_risk["dpd"], y=cust_risk["ar"]/1e6,
        mode="markers", marker=dict(color=BLUE, size=7, opacity=0.75,
                                    line=dict(color=LBLUE, width=0.5)),
        hovertemplate="<b>%{text}</b><br>DPD: %{x:.0f}<br>AR: $%{y:.2f}M<extra></extra>",
        text=cust_risk["customer_name"],
    ))
    apply_layout(scatter_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="Average Days Past Due", yaxis_title="AR Outstanding ($M)",
                 yaxis_tickprefix="$", yaxis_ticksuffix="M")

    # ── AR aging buckets
    now = pd.Timestamp.now()
    def aging_bucket(row):
        if row["paid"]: return None
        dpd = row.get("days_past_due", 0) or 0
        if dpd <= 0:   return "Current"
        elif dpd <= 30: return "1-30"
        elif dpd <= 60: return "31-60"
        elif dpd <= 90: return "61-90"
        else:           return "91+"
    df_ar["bucket"] = df_ar.apply(aging_bucket, axis=1)
    aging = df_ar[df_ar["bucket"].notna()].groupby("bucket")["amount"].sum()
    bucket_order = ["Current","1-30","31-60","61-90","91+"]
    aging = aging.reindex([b for b in bucket_order if b in aging.index])
    aging_fig = go.Figure(go.Bar(
        x=aging.index, y=aging.values/1e6,
        marker_color=[BLUE, LBLUE, AMBER, AMBER, RED][:len(aging)],
        text=[f"${v:.1f}M" for v in aging.values/1e6],
        textposition="outside", textfont=dict(size=10, color=LIGHT),
    ))
    apply_layout(aging_fig, margin=dict(l=48, r=10, t=10, b=36),
                 xaxis_title="aging_bucket", yaxis_tickprefix="$", yaxis_ticksuffix="M")

    # ── DSO trend
    df_ar["due_mo"] = df_ar["due_date"].dt.to_period("M").astype(str)
    dso_trend = df_ar.groupby("due_mo")["days_past_due"].mean().reset_index()
    dso_fig = go.Figure(go.Scatter(
        x=dso_trend["due_mo"], y=dso_trend["days_past_due"],
        fill="tozeroy", line=dict(color=BLUE, width=2),
        fillcolor="rgba(37,99,235,0.12)",
        text=[f"{v:.0f}" for v in dso_trend["days_past_due"]],
        mode="lines+markers+text", textposition="top center",
        textfont=dict(size=8, color=LIGHT),
    ))
    apply_layout(dso_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="due_date", yaxis_title="DSO")

    return html.Div([
        page_header(2, "Working Capital & Liquidity Risk",
                    "How efficiently are we managing the cash conversion cycle?"),
        html.Div(id="ai-brief", children=ai_panel("Analyzing working capital...", loading=True)),
        kpi_row([
            kpi(f"${ar_out/1e6:.2f}M", "AR Outstanding"),
            kpi(f"{dso:.2f}", "DSO", AMBER),
            kpi(f"{coll_rate:.1f}%", "Collection Rate", GREEN),
            kpi(f"{runway:.0f}", "Cash Runway Weeks", GREEN if runway > 12 else RED),
        ]),
        charts_row([
            chart_box("Which customers are highest risk?", scatter_fig, half=True),
            html.Div([
                chart_box("Where is AR risk concentrated?", aging_fig),
                chart_box("Are we collecting faster or slower?", dso_fig),
            ], style={"flex":"1 1 45%","minWidth":"300px","display":"flex","flexDirection":"column","gap":"16px"}),
        ]),
    ])


# ── PAGE 3 — SOLVENCY & DEBT ──────────────────────────────────────────────────

def page_solvency():
    df_cov = get_cached("covenant", "")
    df_cb = get_cached("cash_burn", "").query("scenario == 'base'")[["week_num","week_label","avg_cash_collected","avg_cash_burn"]]
    df_ar = get_cached("ar", "").query("paid == False")[["amount"]]

    ar_out = df_ar["amount"].sum() if not df_ar.empty else 0

    if df_cov.empty:
        return html.Div("No covenant data", style={"color": SLATE, "padding": "40px"})

    base   = df_cov[df_cov["scenario"]=="base"]
    latest = base.iloc[-1] if not base.empty else None
    dscr   = latest["dscr_proxy"] if latest is not None else 0
    net_d  = latest["net_debt"]   if latest is not None else 0
    tot_l  = latest["total_liabilities"] if latest is not None else 0

    # ── Grouped bar: cash collected vs burn
    cb_fig = go.Figure()
    if not df_cb.empty:
        cb_fig.add_trace(go.Bar(x=df_cb["week_label"], y=df_cb["avg_cash_collected"]/1e6,
                                name="avg_cash_collected", marker_color=BLUE, opacity=0.8))
        cb_fig.add_trace(go.Bar(x=df_cb["week_label"], y=df_cb["avg_cash_burn"]/1e6,
                                name="avg_cash_burn", marker_color=GREEN, opacity=0.8))
    apply_layout(cb_fig, barmode="group", margin=dict(l=48, r=10, t=10, b=80),
                 yaxis_tickprefix="$", yaxis_ticksuffix="M",
                 xaxis=dict(tickfont=dict(size=8), gridcolor="rgba(255,255,255,0.05)",
                            showline=False, zeroline=False, title="week_label"))

    # ── DSCR multi-scenario line
    dscr_fig = go.Figure()
    colors = {"base": BLUE, "stress_100bps": LBLUE, "stress_200bps": AMBER}
    for scen, col in colors.items():
        d = df_cov[df_cov["scenario"]==scen]
        if not d.empty:
            dscr_fig.add_trace(go.Scatter(x=d["period"], y=d["dscr_proxy"],
                                          name=scen, line=dict(color=col, width=2)))
    dscr_fig.add_hline(y=0, line_dash="dash", line_color=RED, line_width=1.5,
                       annotation_text="Covenant Floor", annotation_font=dict(color=RED, size=10))
    apply_layout(dscr_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="period", yaxis_title="Sum of dscr_proxy")

    # ── Covenant stress table (top 12 rows)
    tbl_data = df_cov[["period","scenario","dscr_proxy","net_debt"]].head(20)
    tbl = html.Div([
        chart_title("How stressed is our covenant under rate shocks?"),
        html.Table([
            html.Thead(html.Tr([
                html.Th("period", style={"color": SLATE, "fontSize":"10px","padding":"4px 8px","textAlign":"left"}),
                html.Th("scenario", style={"color": SLATE,"fontSize":"10px","padding":"4px 8px","textAlign":"left"}),
                html.Th("DSCR", style={"color": SLATE,"fontSize":"10px","padding":"4px 8px","textAlign":"right"}),
                html.Th("Net Debt", style={"color": SLATE,"fontSize":"10px","padding":"4px 8px","textAlign":"right"}),
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(row["period"], style={"color":"#1E293B","fontSize":"10px","padding":"3px 8px"}),
                    html.Td(row["scenario"], style={"color":LBLUE if row["scenario"]=="base" else AMBER,
                                                    "fontSize":"10px","padding":"3px 8px"}),
                    html.Td(f"{row['dscr_proxy']:.2f}",
                            style={"color": GREEN if row["dscr_proxy"]>0 else RED,
                                   "fontSize":"10px","padding":"3px 8px","textAlign":"right","fontFamily":"monospace"}),
                    html.Td(f"${row['net_debt']:,.0f}",
                            style={"color":"#334155","fontSize":"10px","padding":"3px 8px",
                                   "textAlign":"right","fontFamily":"monospace"}),
                ]) for _, row in tbl_data.iterrows()
            ]),
        ], style={"width":"100%","borderCollapse":"collapse"}),
    ], style={"background":"#FFFFFF","borderRadius":"10px","padding":"14px",
              "border":"1px solid #E2E8F0","overflowY":"auto","maxHeight":"320px","flex":"1 1 45%","boxShadow":"0 1px 3px rgba(0,0,0,0.06)"})

    dscr_color = GREEN if dscr > 0 else RED
    return html.Div([
        page_header(3, "Solvency & Debt", "Are we solvent and within our covenants?"),
        html.Div(id="ai-brief", children=ai_panel("Analyzing solvency...", loading=True)),
        kpi_row([
            kpi(f"{dscr:.0f}", "DSCR Current", dscr_color),
            kpi(f"${net_d/1e6:.2f}M", "Net Debt", AMBER),
            kpi(f"${tot_l/1e6:.1f}M", "Total Liabilities", AMBER),
            kpi(f"${ar_out/1e6:.2f}M", "AR Outstanding"),
        ]),
        chart_box("Are payables outpacing receivables?", cb_fig),
        charts_row([
            chart_box("Are we at risk of breaching our debt covenant?", dscr_fig, half=True),
            tbl,
        ]),
    ])


# ── PAGE 4 — UNIT ECONOMICS ───────────────────────────────────────────────────

def page_unit_economics():
    df = get_cached("gl", "")
    df_fc = get_cached("forecast", "")
    df_bud = get_cached("budget", "")

    if df.empty:
        return html.Div("No GL data", style={"color": SLATE, "padding": "40px"})

    df["month"] = pd.to_datetime(df["period_start"]).dt.to_period("M").astype(str)
    rev_mo   = df[df["category"]=="Revenue"].groupby("month")["credit_amount"].sum()
    cogs_mo  = df[df["category"]=="COGS"].groupby("month")["debit_amount"].sum()
    opex_mo  = df[df["category"]=="OpEx"].groupby("month")["debit_amount"].sum()
    idx      = rev_mo.index.union(cogs_mo.index).union(opex_mo.index)
    rev_mo   = rev_mo.reindex(idx, fill_value=0)
    cogs_mo  = cogs_mo.reindex(idx, fill_value=0)
    opex_mo  = opex_mo.reindex(idx, fill_value=0)
    total_opex_mo = cogs_mo + opex_mo
    gm_mo    = (rev_mo - cogs_mo) / rev_mo.replace(0,1) * 100
    ebitda_mo= (rev_mo - total_opex_mo) / rev_mo.replace(0,1) * 100

    gross_margin = gm_mo.mean()
    ebitda_avg   = ebitda_mo.mean()
    gross_profit = (rev_mo - cogs_mo).sum()
    bud_var      = df_bud["total"].iloc[0] - rev_mo.sum() if not df_bud.empty and len(df_bud) > 0 else 0

    # ── Bar: Revenue vs OpEx monthly
    rev_opex_fig = go.Figure()
    rev_opex_fig.add_trace(go.Bar(x=idx, y=rev_mo.values/1e6,
                                  name="Revenue Monthly", marker_color=GREEN, opacity=0.6))
    rev_opex_fig.add_trace(go.Bar(x=idx, y=total_opex_mo.values/1e6,
                                  name="Opex Monthly", marker_color=BLUE, opacity=0.8))
    apply_layout(rev_opex_fig, barmode="group", margin=dict(l=48, r=10, t=10, b=48),
                 yaxis_tickprefix="$", yaxis_ticksuffix="M", xaxis_title="Month")

    # ── Revenue forecast area
    fc_fig = go.Figure()
    if not df_fc.empty:
        df_fc["forecast_month"] = pd.to_datetime(df_fc["forecast_month"]).astype(str)
        fc_fig.add_trace(go.Scatter(
            x=df_fc["forecast_month"], y=df_fc["revenue_forecast"]/1e6,
            fill="tozeroy", line=dict(color=BLUE, width=2),
            fillcolor="rgba(37,99,235,0.15)", name="P50 Forecast",
        ))
    apply_layout(fc_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="forecast_month", yaxis_title="Sum of revenue_forecast",
                 yaxis_tickprefix="$", yaxis_ticksuffix="M")

    # ── Dual area: gross margin % + ebitda margin %
    margin_fig = go.Figure()
    margin_fig.add_trace(go.Scatter(
        x=idx, y=gm_mo.values, name="Gross Margin %",
        fill="tozeroy", line=dict(color=BLUE, width=2),
        fillcolor="rgba(37,99,235,0.2)",
    ))
    margin_fig.add_trace(go.Scatter(
        x=idx, y=ebitda_mo.values, name="EBITDA Margin Monthly %",
        fill="tozeroy", line=dict(color=GREEN, width=2),
        fillcolor="rgba(16,185,129,0.15)",
    ))
    margin_fig.add_hline(y=0, line_color=RED, line_width=1)
    apply_layout(margin_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="Month", yaxis_ticksuffix="%")

    gm_color = GREEN if gross_margin > 30 else AMBER
    return html.Div([
        page_header(4, "Unit Economics & Break-Even",
                    "Are our margins healthy and how close are we to break-even?"),
        html.Div(id="ai-brief", children=ai_panel("Analyzing unit economics...", loading=True)),
        kpi_row([
            kpi(f"{gross_margin:.1f}%", "Gross Margin %", gm_color),
            kpi(f"{ebitda_avg:.1f}%", "EBITDA Margin Monthly %", GREEN if ebitda_avg>0 else RED),
            kpi(f"${gross_profit/1e6:.2f}M", "Gross Profit"),
            kpi(f"${abs(bud_var)/1e6:.2f}M", "Budget Variance", AMBER),
        ]),
        charts_row([
            chart_box("Is revenue growing faster than costs?", rev_opex_fig, half=True),
            chart_box("What does our 12-month revenue outlook look like?", fc_fig, half=True),
        ]),
        chart_box("Is cost pressure widening our margin gap?", margin_fig),
    ])


# ── PAGE 5 — 13-WEEK CASH FORECAST ───────────────────────────────────────────

def page_cash_forecast():
    df = query("""
        SELECT week_num, week_label, avg_cash_collected, avg_cash_burn, running_balance, scenario
        FROM intel.cash_burn_weekly ORDER BY week_num
    """)
    df_ap = query("SELECT vendor_id, amount FROM erp.ap_invoices WHERE paid=0 ORDER BY amount DESC")

    if df.empty:
        return html.Div("No cash forecast data", style={"color": SLATE, "padding": "40px"})

    base    = df[df["scenario"]=="base"].copy()
    wk13    = base["running_balance"].iloc[-1] if not base.empty else 0
    burn    = base["avg_cash_burn"].mean() if not base.empty else 0
    ar_out_df = get_cached("ar","").query("paid==False")
    ar_val  = ar_out_df["amount"].sum()
    runway  = ar_val / burn if burn > 0 else 0

    # ── Triple line: collected / burn / balance
    tri_fig = make_subplots(specs=[[{"secondary_y": True}]])
    tri_fig.add_trace(go.Scatter(x=base["week_label"], y=base["avg_cash_collected"]/1e6,
                                 name="avg_cash_collected", line=dict(color=LBLUE, width=2)), secondary_y=False)
    tri_fig.add_trace(go.Scatter(x=base["week_label"], y=base["avg_cash_burn"]/1e6,
                                 name="avg_cash_burn", line=dict(color=BLUE2, width=2)), secondary_y=False)
    tri_fig.add_trace(go.Scatter(x=base["week_label"], y=base["running_balance"]/1e6,
                                 name="running_balance", line=dict(color=AMBER, width=2)), secondary_y=True)
    apply_layout(tri_fig, margin=dict(l=48, r=48, t=10, b=80),
                 xaxis=dict(tickfont=dict(size=8), gridcolor="rgba(255,255,255,0.05)",
                            showline=False, zeroline=False, title="week_label"),
                 yaxis=dict(tickprefix="$", ticksuffix="M", gridcolor="rgba(255,255,255,0.05)",
                            showline=False, zeroline=False, tickfont=dict(size=10), title_font=dict(size=11)),
                 yaxis2=dict(tickprefix="$", ticksuffix="M", showgrid=False,
                             showline=False, zeroline=False, tickfont=dict(size=10)))

    # ── Weekly table
    tbl_cols = ["week_label","avg_cash_collected","avg_cash_burn","running_balance"]
    tbl = html.Div([
        chart_title("How sensitive are we to late payments?"),
        html.Table([
            html.Thead(html.Tr([
                html.Th(c, style={"color":SLATE,"fontSize":"9px","padding":"4px 8px",
                                  "textAlign":"right" if i>0 else "left"})
                for i, c in enumerate(["week_label","avg_cash_collected","avg_cash_burn","running_balance"])
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(row["week_label"], style={"color":"#1E293B","fontSize":"9px","padding":"2px 8px"}),
                    *[html.Td(f"${row[c]:,.0f}",
                               style={"color":"#334155","fontSize":"9px","padding":"2px 8px",
                                      "textAlign":"right","fontFamily":"monospace"})
                      for c in ["avg_cash_collected","avg_cash_burn","running_balance"]]
                ]) for _, row in base.iterrows()
            ] + [html.Tr([
                html.Td("Total", style={"color":"#1E3A8A","fontSize":"9px","padding":"4px 8px","fontWeight":"700"}),
                *[html.Td(f"${base[c].sum():,.0f}",
                           style={"color":"#1E3A8A","fontSize":"9px","padding":"4px 8px",
                                  "textAlign":"right","fontFamily":"monospace","fontWeight":"700"})
                  for c in ["avg_cash_collected","avg_cash_burn","running_balance"]]
            ])]),
        ], style={"width":"100%","borderCollapse":"collapse"}),
    ], style={"background":"#FFFFFF","borderRadius":"10px","padding":"14px",
              "border":"1px solid #E2E8F0","flex":"1 1 45%","overflowY":"auto","boxShadow":"0 1px 3px rgba(0,0,0,0.06)"})

    # ── Vendor payables bar
    if not df_ap.empty:
        vendor_ap = df_ap.groupby("vendor_id")["amount"].sum().nlargest(20).reset_index()
        vend_fig = go.Figure(go.Bar(
            x=vendor_ap["vendor_id"].astype(str), y=vendor_ap["amount"]/1e6,
            marker_color=BLUE, opacity=0.8,
        ))
        apply_layout(vend_fig, margin=dict(l=48, r=10, t=10, b=60),
                     xaxis_title="vendor_id", yaxis_tickprefix="$", yaxis_ticksuffix="M",
                     xaxis=dict(tickfont=dict(size=8), gridcolor="rgba(255,255,255,0.05)",
                                showline=False, zeroline=False))
    else:
        vend_fig = empty_fig("No AP data")

    wk13_color = GREEN if wk13 > 0 else RED
    return html.Div([
        page_header(5, "13-Week Cash Forecast", "Do we have a cash problem in the next quarter?"),
        html.Div(id="ai-brief", children=ai_panel("Analyzing cash forecast...", loading=True)),
        kpi_row([
            kpi(f"${wk13/1e6:.1f}M", "Week 13 Cash Balance", wk13_color),
            kpi(f"${burn/1e3:.1f}K", "Weekly Burn Rate", AMBER),
            kpi(f"{runway:.0f}", "Cash Runway Weeks", GREEN if runway > 12 else RED),
            kpi(f"${ar_val/1e6:.2f}M", "AR Outstanding"),
        ]),
        chart_box("When does our cash balance hit the danger zone?", tri_fig),
        charts_row([tbl, chart_box("Where are near-term payables concentrated?", vend_fig, half=True)]),
    ])


# ── PAGE 6 — STRATEGIC MODEL ──────────────────────────────────────────────────

def page_strategic_model():
    df_fc  = get_cached("forecast", "")
    df_gl  = get_cached("gl", "")
    df_cov = get_cached("covenant", "").query("scenario=='base'").sort_values("period", ascending=False)
    df_cb  = get_cached("cash_burn", "").query("scenario=='base'").sort_values("week_num", ascending=False)

    if df_gl.empty:
        return html.Div("No data", style={"color": SLATE, "padding": "40px"})

    df_gl["month"] = pd.to_datetime(df_gl["period_start"]).dt.to_period("M").astype(str)
    rev_mo   = df_gl[df_gl["category"]=="Revenue"].groupby("month")["credit_amount"].sum()
    opex_mo  = df_gl[df_gl["category"].isin(["OpEx","COGS"])].groupby("month")["debit_amount"].sum()
    idx      = rev_mo.index.union(opex_mo.index)
    rev_mo   = rev_mo.reindex(idx, fill_value=0)
    opex_mo  = opex_mo.reindex(idx, fill_value=0)

    # YoY growth
    months = sorted(idx.tolist())
    yoy_rev, yoy_opex, yoy_months = [], [], []
    for i, m in enumerate(months):
        if i >= 12:
            prev = months[i-12]
            if rev_mo[prev] != 0:
                yoy_rev.append((rev_mo[m]-rev_mo[prev])/rev_mo[prev])
                yoy_opex.append((opex_mo[m]-opex_mo[prev])/opex_mo[prev])
                yoy_months.append(m)

    rev_monthly_sum = rev_mo.sum()
    dscr_latest = df_cov["dscr_proxy"].iloc[0] if not df_cov.empty else 0
    gm_pct = (rev_mo - opex_mo).sum() / rev_mo.sum() * 100 if rev_mo.sum() else 0
    wk13 = df_cb["running_balance"].iloc[0] if not df_cb.empty else 0

    # ── Forecast line
    fc_fig = go.Figure()
    if not df_fc.empty:
        df_fc["forecast_month"] = pd.to_datetime(df_fc["forecast_month"]).astype(str)
        fc_fig.add_trace(go.Scatter(
            x=df_fc["forecast_month"], y=df_fc["revenue_forecast"]/1e6,
            fill="tozeroy", line=dict(color=BLUE, width=2.5),
            fillcolor="rgba(37,99,235,0.12)", name="P50",
        ))
    apply_layout(fc_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="forecast_month", yaxis_tickprefix="$", yaxis_ticksuffix="M")

    # ── Historical revenue area
    hist_fig = go.Figure(go.Scatter(
        x=idx, y=rev_mo.values/1e6,
        fill="tozeroy", line=dict(color=BLUE, width=2),
        fillcolor="rgba(37,99,235,0.15)", name="Revenue Monthly",
    ))
    apply_layout(hist_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="Month", yaxis_tickprefix="$", yaxis_ticksuffix="M")

    # ── YoY grouped bar
    yoy_fig = go.Figure()
    if yoy_months:
        yoy_fig.add_trace(go.Bar(x=yoy_months, y=yoy_rev, name="Revenue YoY%",
                                 marker_color=LBLUE, opacity=0.8))
        yoy_fig.add_trace(go.Bar(x=yoy_months, y=yoy_opex, name="Opex YoY%",
                                 marker_color=BLUE2, opacity=0.8))
    yoy_fig.add_hline(y=0, line_color=RED, line_width=1)
    apply_layout(yoy_fig, barmode="group", margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="Month", yaxis_ticksuffix="%")

    gm_color = GREEN if gm_pct > 30 else AMBER
    return html.Div([
        page_header(6, "Strategic Model", "Is the business structurally healthy for the next 12 months?"),
        html.Div(id="ai-brief", children=ai_panel("Analyzing strategic position...", loading=True)),
        kpi_row([
            kpi(f"${rev_monthly_sum/1e6:.2f}M", "Revenue (Total)"),
            kpi(f"{dscr_latest:.0f}", "DSCR Current", GREEN if dscr_latest > 0 else RED),
            kpi(f"{gm_pct:.1f}%", "Gross Margin %", gm_color),
            kpi(f"${wk13/1e6:.1f}M", "Week 13 Cash Balance", GREEN if wk13 > 0 else RED),
        ]),
        charts_row([
            chart_box("Where is our revenue heading in the next 12 months?", fc_fig, half=True),
            chart_box("Is the business structurally healthy?", hist_fig, half=True),
        ]),
        chart_box("Is revenue growing faster than costs?", yoy_fig),
    ])


# ── PAGE 7 — MACRO ENVIRONMENT ────────────────────────────────────────────────

def page_macro():
    df = get_cached("macro", "")

    if df.empty:
        return html.Div("No macro data", style={"color": SLATE, "padding": "40px"})

    df["obs_date"] = pd.to_datetime(df["obs_date"])

    def latest_val(key):
        r = df[df["metric_key"]==key].sort_values("obs_date")
        return r["value"].iloc[-1] if not r.empty else None

    boc  = latest_val("BOC_POLICY_RATE")
    unemp= latest_val("UNEMPLOYMENT_RATE")
    usdcad=latest_val("USD_CAD")

    # Yield spread (10Y - 2Y) — approximate with available metrics
    y10 = df[df["metric_key"].str.contains("10Y|GOC_10Y", na=False, case=False)].sort_values("obs_date")
    y2  = df[df["metric_key"].str.contains("2Y|GOC_2Y",  na=False, case=False)].sort_values("obs_date")
    if not y10.empty and not y2.empty:
        merged_y = y10[["obs_date","value"]].merge(y2[["obs_date","value"]], on="obs_date", suffixes=("_10","_2"))
        merged_y["spread"] = merged_y["value_10"] - merged_y["value_2"]
        spread_latest = merged_y["spread"].iloc[-1] if len(merged_y) > 0 else None
    else:
        merged_y = pd.DataFrame()
        spread_latest = None

    # ── BoC rate line
    boc_df = df[df["metric_key"]=="BOC_POLICY_RATE"]
    boc_fig = go.Figure(go.Scatter(
        x=boc_df["obs_date"], y=boc_df["value"],
        line=dict(color=BLUE, width=2.5), name="BoC Policy Rate",
    ))
    apply_layout(boc_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="obs_date", yaxis_title="BoC Policy Rate")

    # ── Yield spread
    spread_fig = go.Figure()
    if not merged_y.empty:
        spread_fig.add_trace(go.Scatter(
            x=merged_y["obs_date"], y=merged_y["spread"],
            line=dict(color=LBLUE, width=2), name="Yield Spread",
            fill="tozeroy", fillcolor="rgba(147,197,253,0.1)",
        ))
        spread_fig.add_hline(y=0, line_dash="dash", line_color=RED, line_width=1)
    apply_layout(spread_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="obs_date", yaxis_title="Yield Spread")

    # ── IPPI vs MFG new orders
    ippi_df = df[df["metric_key"]=="STATCAN_IPPI"]
    mfg_df  = df[df["metric_key"]=="STATCAN_MFG_NEW_ORDERS"]
    cost_fig = go.Figure()
    if not ippi_df.empty:
        cost_fig.add_trace(go.Scatter(x=ippi_df["obs_date"], y=ippi_df["value"],
                                      name="STATCAN_IPPI", line=dict(color=LBLUE, width=2),
                                      fill="tozeroy", fillcolor="rgba(147,197,253,0.1)"))
    if not mfg_df.empty:
        cost_fig.add_trace(go.Scatter(x=mfg_df["obs_date"], y=mfg_df["value"],
                                      name="STATCAN_MFG_NEW_ORDERS", line=dict(color=BLUE2, width=2),
                                      fill="tozeroy", fillcolor="rgba(30,58,138,0.15)"))
    apply_layout(cost_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="obs_date", yaxis_title="Sum of value")

    return html.Div([
        page_header(7, "Macro Environment", "What is the external environment doing to us?"),
        kpi_row([
            kpi(f"{boc:.2f}" if boc else "—", "BoC Policy Rate"),
            kpi(f"{spread_latest:.2f}" if spread_latest else "—", "Yield Spread", RED if spread_latest and spread_latest < 0 else GREEN),
            kpi(f"{unemp:.2f}" if unemp else "—", "Unemployment Rate", AMBER),
            kpi(f"{usdcad:.2f}" if usdcad else "—", "USD CAD"),
        ]),
        charts_row([
            chart_box("Where is the BoC rate heading?", boc_fig, half=True),
            chart_box("Is the yield curve inverted?", spread_fig, half=True),
        ]),
        chart_box("Are input costs outpacing new orders?", cost_fig),
    ])


# ── PAGE 8 — SECTOR ROTATION ──────────────────────────────────────────────────

def page_sector_rotation():
    df = get_cached("sector", "")
    df_macro = get_cached("macro", "").sort_values("obs_date", ascending=False)

    if df.empty:
        return html.Div("No sector data", style={"color": SLATE, "padding": "40px"})

    df["obs_date"] = pd.to_datetime(df["obs_date"])

    # Cyclical/Defensive ratio
    cyclical_tickers = ["XFN","XIT","XEG"]
    defensive_tickers= ["XST","XUT","XRE"]
    latest_date = df["obs_date"].max()
    latest = df[df["obs_date"]==latest_date]
    cyc_price = latest[latest["ticker"].isin(cyclical_tickers)]["close_price"].mean()
    def_price = latest[latest["ticker"].isin(defensive_tickers)]["close_price"].mean()
    ratio = cyc_price / def_price if def_price else 1
    risk_stance = "Risk-On" if ratio > 1 else "Risk-Off"

    def get_macro(key):
        r = df_macro[df_macro["metric_key"]==key]
        return r["value"].iloc[0] if not r.empty else None
    boc = get_macro("BOC_POLICY_RATE")

    spread_df = df_macro[df_macro["metric_key"].str.contains("SPREAD|10Y|2Y", na=False, case=False)]
    spread = None  # simplified

    # ── Cyclical ratio over time
    cyc_hist = df[df["ticker"].isin(cyclical_tickers)].groupby("obs_date")["close_price"].mean()
    def_hist  = df[df["ticker"].isin(defensive_tickers)].groupby("obs_date")["close_price"].mean()
    ratio_hist= (cyc_hist / def_hist.replace(0,1)).reset_index()
    ratio_hist.columns = ["obs_date","ratio"]

    ratio_fig = go.Figure(go.Scatter(
        x=ratio_hist["obs_date"], y=ratio_hist["ratio"],
        line=dict(color=BLUE, width=2), name="Cyclical Ratio",
    ))
    ratio_fig.add_hline(y=1.0, line_dash="dash", line_color=RED, line_width=1.5,
                        annotation_text="Risk-On threshold 1.0",
                        annotation_font=dict(color=RED, size=10))
    apply_layout(ratio_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="obs_date", yaxis_title="Cyclical Ratio")

    # ── Capital concentration bar
    cap_df = df.groupby("description")["close_price"].max().sort_values(ascending=False).reset_index()
    bar_colors = [BLUE, LBLUE, TEAL, GREEN, AMBER, PURPLE, RED, PINK, BLUE2, SLATE]
    cap_fig = go.Figure(go.Bar(
        x=cap_df["description"], y=cap_df["close_price"],
        marker_color=bar_colors[:len(cap_df)], opacity=0.85,
    ))
    apply_layout(cap_fig, margin=dict(l=48, r=10, t=10, b=100),
                 xaxis_title="description", yaxis_title="Max of close_price",
                 xaxis=dict(tickfont=dict(size=8), gridcolor="rgba(255,255,255,0.05)",
                            showline=False, zeroline=False))

    # ── Sector ETF lines (top 5 by description)
    top_tickers = cap_df.head(5)["description"].tolist()
    line_colors  = [LBLUE, BLUE2, AMBER, PINK, TEAL]
    etf_fig = go.Figure()
    for i, desc in enumerate(top_tickers):
        d = df[df["description"]==desc]
        etf_fig.add_trace(go.Scatter(
            x=d["obs_date"], y=d["close_price"],
            name=desc, line=dict(color=line_colors[i % len(line_colors)], width=1.5),
        ))
    apply_layout(etf_fig, margin=dict(l=48, r=10, t=10, b=48),
                 xaxis_title="obs_date", yaxis_title="Average of close_price")

    ratio_color = GREEN if ratio > 1 else RED
    return html.Div([
        page_header(8, "Sector Rotation", "What are institutional investors telling us about the economy?"),
        kpi_row([
            kpi(f"{ratio:.2f}", "Cyclical Ratio", ratio_color),
            kpi(risk_stance, "Risk Stance", ratio_color),
            kpi(f"{boc:.2f}" if boc else "—", "BoC Policy Rate"),
            kpi("—", "Yield Spread", SLATE),
        ]),
        charts_row([
            chart_box("Are institutional investors Risk-On or Risk-Off?", ratio_fig, half=True),
            chart_box("Where is capital concentrated today?", cap_fig, half=True),
        ]),
        chart_box("Which sectors are institutional investors rotating into?", etf_fig),
    ])


# ── PAGES REGISTRY ────────────────────────────────────────────────────────────

PAGES = [
    {"key": "cfo1", "label": "Financial Velocity",   "fn": page_financial_velocity},
    {"key": "cfo2", "label": "Working Capital",       "fn": page_working_capital},
    {"key": "cfo3", "label": "Solvency & Debt",       "fn": page_solvency},
    {"key": "cfo4", "label": "Unit Economics",        "fn": page_unit_economics},
    {"key": "cfo5", "label": "13-Week Cash Forecast", "fn": page_cash_forecast},
    {"key": "cfo6", "label": "Strategic Model",       "fn": page_strategic_model},
    {"key": "cfo7", "label": "Macro Environment",     "fn": page_macro},
    {"key": "cfo8", "label": "Sector Rotation",       "fn": page_sector_rotation},
]

# ── LAYOUT ────────────────────────────────────────────────────────────────────

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

NAV_BTN_BASE = {
    "display": "block", "width": "100%", "textAlign": "left",
    "background": "transparent", "border": "none", "cursor": "pointer",
    "padding": "9px 14px", "borderRadius": "7px", "marginBottom": "2px",
    "fontSize": "12px", "color": "#475569", "fontWeight": "500",
    "fontFamily": FONT, "transition": "all 0.15s",
}

app.layout = html.Div([
    # ── Sidebar
    html.Div([
        html.Div([
            html.Div("CFO", style={"fontSize": "15px", "fontWeight": "800", "color": "#0F172A"}),
            html.Div("Intelligence App", style={"fontSize": "10px", "color": BLUE,
                                               "letterSpacing": "0.06em", "textTransform": "uppercase"}),
        ], style={"marginBottom": "32px", "paddingBottom": "16px",
                  "borderBottom": "1px solid #E2E8F0"}),
        html.Div([
            html.Button(
                p["label"],
                id={"type": "nav-btn", "index": p["key"]},
                n_clicks=0,
                style=NAV_BTN_BASE,
            )
            for p in PAGES
        ], id="nav-buttons"),
        html.Div([
            html.Div("Last refreshed", style={"fontSize":"9px","color":"#94A3B8",
                "textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"4px"}),
            html.Div(datetime.now().strftime("%b %d, %Y %H:%M"),
                style={"fontSize":"10px","color":"#64748B","fontWeight":"500"}),
        ], style={"paddingTop":"24px","borderTop":"1px solid #E2E8F0","marginTop":"32px"}),
    ], style={
        "width": "185px", "minWidth": "185px",
        "background": "#FFFFFF",
        "padding": "24px 12px",
        "height": "100vh",
        "overflowY": "auto",
        "borderRight": "1px solid #E2E8F0",
        "position": "sticky", "top": 0,
        "display": "flex", "flexDirection": "column",
    }),

    # ── Main
    html.Div([
        dcc.Store(id="active-page", data="cfo1"),
        dcc.Store(id="ai-store", data={}),
        dcc.Interval(id="ai-trigger", interval=100, n_intervals=0, max_intervals=1),
        html.Div(id="page-content", style={"padding": "28px 36px 16px"}),
    ], style={"flex": 1, "overflowY": "auto", "background": "#F1F5F9"}),

], style={"display": "flex", "background": "#F1F5F9", "minHeight": "100vh", "fontFamily": FONT})


# ── CALLBACKS ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("active-page", "data"),
    Input({"type": "nav-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def set_active(n_clicks):
    triggered = ctx.triggered_id
    return triggered["index"] if triggered else "cfo1"

@app.callback(
    Output({"type": "nav-btn", "index": ALL}, "style"),
    Input("active-page", "data"),
)
def highlight_nav(active_page):
    styles = []
    for p in PAGES:
        if p["key"] == active_page:
            styles.append({**NAV_BTN_BASE,
                "background": "#EFF6FF",
                "color": "#1E3A8A",
                "fontWeight": "700",
                "borderLeft": "3px solid #1E3A8A",
                "paddingLeft": "11px",
            })
        else:
            styles.append({**NAV_BTN_BASE,
                "color": "#475569",
                "fontWeight": "500",
            })
    return styles


@app.callback(
    Output("page-content", "children"),
    Input("active-page", "data"),
)
def render_page(key):
    for p in PAGES:
        if p["key"] == key:
            return p["fn"]()
    return PAGES[0]["fn"]()


# AI brief lookup — maps page key to (title, kpis_fn, question)
def get_ai_context(page_key):
    """Returns (title, question) for the AI brief — kpis fetched fresh."""
    contexts = {
        "cfo1": ("Financial Velocity", "Is the business generating cash efficiently?"),
        "cfo2": ("Working Capital & Liquidity Risk", "How efficiently are we managing the cash conversion cycle?"),
        "cfo3": ("Solvency & Debt", "Are we solvent and within our covenants?"),
        "cfo4": ("Unit Economics & Break-Even", "Are our margins healthy and how close are we to break-even?"),
        "cfo5": ("13-Week Cash Forecast", "Do we have a cash problem in the next quarter?"),
        "cfo6": ("Strategic Model", "Is the business structurally healthy for the next 12 months?"),
    }
    return contexts.get(page_key, ("CFO Intelligence", "What does this data tell us?"))

def fetch_kpis_for_page(page_key):
    """Fetch just the KPIs needed for the AI brief."""
    try:
        if page_key == "cfo1":
            df = query("""SELECT g.credit_amount, g.debit_amount, c.category
                FROM erp.gl_ledger g JOIN dim.chart_of_accounts c ON g.account_id=c.account_id
                WHERE g.period_start >= DATEADD(month,-28,GETDATE())""")
            df_ar = query("SELECT paid, amount FROM erp.ar_invoices")
            rev = df[df.category=="Revenue"]["credit_amount"].sum()
            opex = df[df.category.isin(["OpEx","COGS"])]["debit_amount"].sum()
            cogs = df[df.category=="COGS"]["debit_amount"].sum()
            ebitda_pct = (rev-opex)/rev*100 if rev else 0
            coll = df_ar[df_ar.paid==True]["amount"].sum()/df_ar["amount"].sum()*100 if not df_ar.empty else 0
            return {"Revenue YTD": f"${rev/1e6:.1f}M", "Total OpEx": f"${opex/1e6:.1f}M",
                    "EBITDA Margin": f"{ebitda_pct:.1f}%", "Collection Rate": f"{coll:.1f}%"}
        elif page_key == "cfo2":
            df_ar = query("SELECT amount, paid, days_past_due FROM erp.ar_invoices")
            df_ap = query("SELECT amount, paid FROM erp.ap_invoices")
            ar_out = df_ar[df_ar.paid==False]["amount"].sum()
            coll = df_ar[df_ar.paid==True]["amount"].sum()/df_ar["amount"].sum()*100 if not df_ar.empty else 0
            dso = df_ar["days_past_due"].mean()
            ap_burn = df_ap["amount"].sum()/52 if not df_ap.empty else 1
            runway = ar_out/ap_burn if ap_burn else 0
            return {"AR Outstanding": f"${ar_out/1e6:.2f}M", "DSO": f"{dso:.1f} days",
                    "Collection Rate": f"{coll:.1f}%", "Cash Runway": f"{runway:.0f} weeks"}
        elif page_key == "cfo3":
            df = query("SELECT dscr_proxy, net_debt, total_liabilities FROM intel.covenant_tracker WHERE scenario='base' ORDER BY period DESC")
            df_ar = query("SELECT SUM(amount) as t FROM erp.ar_invoices WHERE paid=0")
            r = df.iloc[0] if not df.empty else None
            return {"DSCR": f"{r.dscr_proxy:.1f}x" if r is not None else "—",
                    "Net Debt": f"${r.net_debt/1e6:.2f}M" if r is not None else "—",
                    "AR Outstanding": f"${df_ar.t.iloc[0]/1e6:.2f}M" if not df_ar.empty else "—"}
        elif page_key == "cfo4":
            df = query("""SELECT g.credit_amount, g.debit_amount, c.category
                FROM erp.gl_ledger g JOIN dim.chart_of_accounts c ON g.account_id=c.account_id
                WHERE g.period_start >= DATEADD(month,-28,GETDATE())""")
            rev = df[df.category=="Revenue"]["credit_amount"].sum()
            cogs = df[df.category=="COGS"]["debit_amount"].sum()
            opex = df[df.category.isin(["OpEx","COGS"])]["debit_amount"].sum()
            gm = (rev-cogs)/rev*100 if rev else 0
            ebitda = (rev-opex)/rev*100 if rev else 0
            return {"Gross Margin": f"{gm:.1f}%", "EBITDA Margin": f"{ebitda:.1f}%",
                    "Gross Profit": f"${(rev-cogs)/1e6:.2f}M"}
        elif page_key == "cfo5":
            df = query("SELECT avg_cash_burn, running_balance FROM intel.cash_burn_weekly WHERE scenario='base' ORDER BY week_num")
            df_ar = query("SELECT SUM(amount) as t FROM erp.ar_invoices WHERE paid=0")
            wk13 = df["running_balance"].iloc[-1] if not df.empty else 0
            burn = df["avg_cash_burn"].mean() if not df.empty else 0
            ar = df_ar["t"].iloc[0] if not df_ar.empty else 0
            runway = ar/burn if burn else 0
            return {"Week-13 Balance": f"${wk13/1e6:.1f}M", "Weekly Burn": f"${burn/1e3:.0f}K",
                    "Cash Runway": f"{runway:.0f} weeks", "AR Outstanding": f"${ar/1e6:.2f}M"}
        elif page_key == "cfo6":
            df = query("""SELECT g.credit_amount, g.debit_amount, c.category
                FROM erp.gl_ledger g JOIN dim.chart_of_accounts c ON g.account_id=c.account_id
                WHERE g.period_start >= DATEADD(month,-28,GETDATE())""")
            df_cb = query("SELECT running_balance FROM intel.cash_burn_weekly WHERE scenario='base' ORDER BY week_num DESC")
            df_cov = query("SELECT dscr_proxy FROM intel.covenant_tracker WHERE scenario='base' ORDER BY period DESC")
            rev = df[df.category=="Revenue"]["credit_amount"].sum()
            cogs = df[df.category=="COGS"]["debit_amount"].sum()
            gm = (rev-cogs)/rev*100 if rev else 0
            wk13 = df_cb["running_balance"].iloc[0] if not df_cb.empty else 0
            dscr = df_cov["dscr_proxy"].iloc[0] if not df_cov.empty else 0
            return {"12m Revenue": f"${rev/1e6:.1f}M", "Gross Margin": f"{gm:.1f}%",
                    "DSCR": f"{dscr:.1f}x", "Week-13 Cash": f"${wk13/1e6:.1f}M"}
    except Exception as e:
        return {"Error": str(e)}
    return {}

@app.callback(
    Output("ai-brief", "children"),
    Input("ai-trigger", "n_intervals"),
    Input("active-page", "data"),
    prevent_initial_call=False,
)
def update_ai_brief(n, page_key):
    if page_key not in ["cfo1","cfo2","cfo3","cfo4","cfo5","cfo6"]:
        return ai_panel("No AI briefing available for this page.")
    title, question = get_ai_context(page_key)
    # Serve from cache instantly — no API call
    if title in _brief_cache:
        return ai_panel(_brief_cache[title])
    # Not cached yet — fetch and store
    kpis = fetch_kpis_for_page(page_key)
    text = gemini_summary(title, kpis, question)
    return ai_panel(text)


# Preload all data at startup
preload_data()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)

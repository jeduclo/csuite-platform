"""
CFO Intelligence App — Plotly Dash (Parquet / Demo Edition)
6 CFO pages, light white/grey theme, zero DB dependency
"""
import os
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output

# ── DATA DIRECTORY ────────────────────────────────────────────────────────────
DATA = os.path.join(os.path.dirname(__file__), "data")

def load(name):
    return pd.read_parquet(os.path.join(DATA, f"{name}.parquet"))

# ── PRELOAD ALL DATA ──────────────────────────────────────────────────────────
gl       = load("gl")
ar       = load("ar")
ap       = load("ap")
cb       = load("cash_burn")
cov      = load("covenant")
fcast    = load("forecast")
budget   = load("budget")

# ── DESIGN TOKENS (light theme) ───────────────────────────────────────────────
BG      = "#F8FAFC"
CARD    = "#FFFFFF"
NAVY    = "#1E3A8A"
BLUE    = "#2563EB"
LBLUE   = "#4472C4"
SLATE   = "#64748B"
DARK    = "#0F172A"
GREEN   = "#059669"
AMBER   = "#D97706"
RED     = "#DC2626"
GREY    = "#E2E8F0"

PLOT_BG = "#FFFFFF"
GRID    = "#F1F5F9"

PAGES = [
    ("cfo1", "Financial Velocity"),
    ("cfo2", "Working Capital"),
    ("cfo3", "Solvency & Debt"),
    ("cfo4", "Unit Economics"),
    ("cfo5", "13-Week Cash Forecast"),
    ("cfo6", "Strategic Model"),
]

SUBTITLES = {
    "cfo1": "Is the business generating cash efficiently?",
    "cfo2": "How efficiently are we managing the cash conversion cycle?",
    "cfo3": "Are we solvent and within our covenants?",
    "cfo4": "Are our margins healthy?",
    "cfo5": "Do we have a cash problem in the next quarter?",
    "cfo6": "Is the business structurally healthy for the next 12 months?",
}

# ── APP ───────────────────────────────────────────────────────────────────────
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # gunicorn entry point

# ── LAYOUT HELPERS ────────────────────────────────────────────────────────────
def kpi_card(label, value, color=NAVY):
    return html.Div([
        html.Div(value, style={"fontSize":"28px","fontWeight":"800","color":color,"marginBottom":"4px"}),
        html.Div(label, style={"fontSize":"11px","fontWeight":"600","color":SLATE,"letterSpacing":"0.08em","textTransform":"uppercase"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"20px 24px",
              "flex":"1","boxShadow":"0 1px 3px rgba(0,0,0,0.07)","border":f"1px solid {GREY}"})

def chart_card(title, fig, height=340):
    return html.Div([
        html.Div(title, style={"fontSize":"13px","fontWeight":"700","color":NAVY,"marginBottom":"12px"}),
        dcc.Graph(figure=fig, config={"displayModeBar":False},
                  style={"height":f"{height}px"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"20px 24px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.07)","border":f"1px solid {GREY}"})

def base_layout():
    return dict(
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter, system-ui, sans-serif", size=11, color=DARK),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(size=10)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=10)),
        hovermode="x unified",
    )

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def sidebar(active):
    links = []
    for pid, label in PAGES:
        is_active = pid == active
        links.append(html.Div(
            label,
            id={"type":"nav","index":pid},
            n_clicks=0,
            style={
                "padding":"10px 16px","cursor":"pointer","borderRadius":"6px",
                "fontSize":"13px","fontWeight":"600" if is_active else "400",
                "color":BLUE if is_active else DARK,
                "background":"#EFF6FF" if is_active else "transparent",
                "borderLeft":f"3px solid {BLUE}" if is_active else "3px solid transparent",
                "marginBottom":"2px","transition":"all 0.15s",
            }
        ))
    return html.Div([
        html.Div([
            html.Div("CFO", style={"fontSize":"16px","fontWeight":"900","color":NAVY,"letterSpacing":"0.05em"}),
            html.Div("INTELLIGENCE APP", style={"fontSize":"9px","fontWeight":"600","color":SLATE,"letterSpacing":"0.15em"}),
        ], style={"padding":"20px 16px 16px","borderBottom":f"1px solid {GREY}","marginBottom":"12px"}),
        html.Div(links, style={"padding":"0 8px"}),
        html.Div([
            html.Div("LAST REFRESHED", style={"fontSize":"9px","color":SLATE,"fontWeight":"600","letterSpacing":"0.08em"}),
            html.Div(datetime.now().strftime("%b %d, %Y %H:%M"),
                     style={"fontSize":"11px","color":DARK,"marginTop":"2px"}),
        ], style={"position":"absolute","bottom":"24px","left":"16px"}),
    ], style={
        "width":"185px","minWidth":"185px","background":CARD,"height":"100vh",
        "borderRight":f"1px solid {GREY}","position":"relative","flexShrink":"0",
    })

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="active-page", data="cfo1"),
    html.Div([
        html.Div(id="sidebar-container"),
        html.Div(id="page-content", style={"flex":"1","overflowY":"auto","background":BG}),
    ], style={"display":"flex","height":"100vh","fontFamily":"Inter, system-ui, sans-serif"}),
], style={"margin":"0","padding":"0"})

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
def page_header(num, title, subtitle):
    return html.Div([
        html.Div(f"CFO {num}", style={"fontSize":"11px","color":BLUE,"fontWeight":"700","letterSpacing":"0.08em","marginBottom":"4px"}),
        html.Div([
            html.Span(title, style={"fontSize":"22px","fontWeight":"800","color":DARK}),
            html.Span(subtitle, style={"fontSize":"12px","color":SLATE,"fontStyle":"italic","marginLeft":"auto"}),
        ], style={"display":"flex","alignItems":"baseline","gap":"16px","justifyContent":"space-between"}),
    ], style={"padding":"24px 32px 16px","borderBottom":f"1px solid {GREY}","background":CARD})

def page_body(*rows):
    return html.Div(list(rows), style={"padding":"20px 32px","display":"flex","flexDirection":"column","gap":"16px"})

def kpi_row(*cards):
    return html.Div(list(cards), style={"display":"flex","gap":"16px"})

def chart_row(*cards):
    return html.Div(list(cards), style={"display":"flex","gap":"16px"})

# ═══════════════════════════════════════════════════════════════════════════════
# CFO 1 — FINANCIAL VELOCITY
# ═══════════════════════════════════════════════════════════════════════════════
def build_cfo1():
    rev   = gl[gl.category=="Revenue"]["credit_amount"].sum()
    cogs  = gl[gl.category=="COGS"]["debit_amount"].sum()
    opex  = gl[gl.category=="OpEx"]["debit_amount"].sum()
    ebitda_m = (rev - cogs - opex) / rev * 100
    total_invoiced = ar["amount"].sum()
    total_paid     = ar[ar.paid]["amount"].sum()
    coll_rate = total_paid / total_invoiced * 100

    # Waterfall
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute","relative","relative","total"],
        x=["Revenue","COGS","OpEx","Total"],
        y=[rev, -cogs, -opex, 0],
        text=[f"${rev/1e6:.1f}M", f"-${cogs/1e6:.1f}M", f"-${opex/1e6:.1f}M", f"${(rev-cogs-opex)/1e6:.1f}M"],
        textposition="outside",
        connector=dict(line=dict(color=GREY, width=1)),
        increasing=dict(marker=dict(color=LBLUE)),
        decreasing=dict(marker=dict(color="#94A3B8")),
        totals=dict(marker=dict(color=BLUE)),
    ))
    fig_wf.update_layout(**base_layout())
    fig_wf.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_tickformat=".2s")

    # Revenue by account
    rev_by_acct = (gl[gl.category=="Revenue"]
                   .groupby("account_name")["credit_amount"].sum()
                   .sort_values(ascending=False))
    fig_acct = go.Figure(go.Bar(
        x=rev_by_acct.index, y=rev_by_acct.values,
        marker_color=LBLUE,
        text=[f"${v/1e6:.1f}M" for v in rev_by_acct.values],
        textposition="outside",
    ))
    fig_acct.update_layout(**base_layout())
    fig_acct.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_tickformat=".2s",
                           xaxis_tickangle=-30)

    # Dual-axis revenue + EBITDA margin
    gl_m = gl.copy()
    gl_m["period_start"] = pd.to_datetime(gl_m["period_start"])
    rev_m  = gl_m[gl_m.category=="Revenue"].groupby("period_start")["credit_amount"].sum()
    cogs_m = gl_m[gl_m.category=="COGS"].groupby("period_start")["debit_amount"].sum()
    opex_m = gl_m[gl_m.category=="OpEx"].groupby("period_start")["debit_amount"].sum()
    ebitda_pct = ((rev_m - cogs_m - opex_m) / rev_m * 100).sort_index()
    rev_m = rev_m.sort_index()

    fig_dual = make_subplots(specs=[[{"secondary_y":True}]])
    fig_dual.add_trace(go.Bar(x=rev_m.index, y=rev_m.values, name="Revenue Monthly",
                              marker_color=LBLUE, opacity=0.85), secondary_y=False)
    fig_dual.add_trace(go.Scatter(x=ebitda_pct.index, y=ebitda_pct.values,
                                  name="EBITDA Margin %", line=dict(color=GREEN, width=2),
                                  mode="lines"), secondary_y=True)
    fig_dual.add_hline(y=0, line_color=RED, line_width=1, secondary_y=True)
    fig_dual.update_layout(**base_layout())
    fig_dual.update_layout(legend=dict(orientation="h", y=1.05))
    fig_dual.update_yaxes(tickprefix="$", tickformat=".2s", secondary_y=False, gridcolor=GRID)
    fig_dual.update_yaxes(ticksuffix="%", secondary_y=True, showgrid=False)

    return html.Div([
        page_header(1, "Financial Velocity", SUBTITLES["cfo1"]),
        page_body(
            kpi_row(
                kpi_card("Revenue YTD",    f"${rev/1e6:.1f}M",   NAVY),
                kpi_card("Total OpEx",     f"${opex/1e6:.1f}M",  AMBER),
                kpi_card("EBITDA Margin %",f"{ebitda_m:.1f}%",   GREEN),
                kpi_card("Collection Rate",f"{coll_rate:.1f}%",  GREEN),
            ),
            chart_row(
                html.Div(chart_card("Where is margin being lost?", fig_wf), style={"flex":"1"}),
                html.Div(chart_card("Which accounts drive revenue?", fig_acct), style={"flex":"1"}),
            ),
            chart_card("Is our margin improving or compressing?", fig_dual, height=300),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# CFO 2 — WORKING CAPITAL
# ═══════════════════════════════════════════════════════════════════════════════
def build_cfo2():
    ar_out = ar[~ar.paid]["amount"].sum()
    dso    = ar["days_past_due"].mean()
    total_inv = ar["amount"].sum()
    coll_rate = ar[ar.paid]["amount"].sum() / total_inv * 100
    cash_runway = 27  # weeks, from cash_burn

    # Customer risk scatter
    cust_risk = ar.groupby("customer_id").agg(
        ar_outstanding=("amount","sum"),
        avg_dpd=("days_past_due","mean"),
    ).reset_index()
    fig_scatter = go.Figure(go.Scatter(
        x=cust_risk["avg_dpd"], y=cust_risk["ar_outstanding"]/1e6,
        mode="markers",
        marker=dict(color=LBLUE, size=8, opacity=0.75),
    ))
    fig_scatter.update_layout(**base_layout())
    fig_scatter.update_layout(showlegend=False,
                               xaxis_title="Average Days Past Due",
                               yaxis_title="AR Outstanding ($M)")

    # AR aging buckets
    def bucket(dpd):
        if dpd == 0: return "Current"
        elif dpd <= 30: return "1-30"
        elif dpd <= 60: return "31-60"
        elif dpd <= 90: return "61-90"
        else: return "91+"
    ar2 = ar.copy()
    ar2["bucket"] = ar2["days_past_due"].apply(bucket)
    aging = ar2.groupby("bucket")["amount"].sum().reindex(["Current","1-30","31-60","61-90","91+"], fill_value=0)
    colors = [LBLUE, "#6B88D4", AMBER, "#E07B1A", RED]
    fig_aging = go.Figure(go.Bar(
        x=aging.index, y=aging.values/1e6,
        marker_color=colors,
        text=[f"${v/1e6:.1f}M" for v in aging.values],
        textposition="outside",
    ))
    fig_aging.update_layout(**base_layout())
    fig_aging.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M")

    # DSO trend by due_date month
    ar3 = ar.copy()
    ar3["due_date"] = pd.to_datetime(ar3["due_date"])
    ar3["month"] = ar3["due_date"].dt.to_period("M").dt.to_timestamp()
    dso_trend = ar3.groupby("month")["days_past_due"].mean().sort_index()
    fig_dso = go.Figure(go.Scatter(
        x=dso_trend.index, y=dso_trend.values,
        fill="tozeroy", fillcolor="rgba(68,114,196,0.15)",
        line=dict(color=LBLUE, width=2),
        mode="lines+markers+text",
        text=[f"{v:.0f}" for v in dso_trend.values],
        textposition="top center",
        textfont=dict(size=9),
    ))
    fig_dso.update_layout(**base_layout())
    fig_dso.update_layout(showlegend=False, yaxis_title="DSO", xaxis_title="due_date")

    return html.Div([
        page_header(2, "Working Capital & Liquidity Risk", SUBTITLES["cfo2"]),
        page_body(
            kpi_row(
                kpi_card("AR Outstanding",  f"${ar_out/1e6:.2f}M", NAVY),
                kpi_card("DSO",             f"{dso:.2f}",          AMBER),
                kpi_card("Collection Rate", f"{coll_rate:.1f}%",   GREEN),
                kpi_card("Cash Runway Weeks",f"{cash_runway}",     RED),
            ),
            chart_row(
                html.Div(chart_card("Which customers are highest risk?", fig_scatter), style={"flex":"1"}),
                html.Div(chart_card("Where is AR risk concentrated?", fig_aging), style={"flex":"1"}),
            ),
            chart_card("Are we collecting faster or slower?", fig_dso, height=280),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# CFO 3 — SOLVENCY & DEBT
# ═══════════════════════════════════════════════════════════════════════════════
def build_cfo3():
    base_cov = cov[cov.scenario=="base"]
    dscr_current = base_cov["dscr_proxy"].iloc[-1]
    net_debt = base_cov["net_debt"].iloc[-1]
    total_liab = base_cov["total_liabilities"].iloc[-1]
    ar_out = ar[~ar.paid]["amount"].sum()

    # Cash collected vs burn grouped bar (base only)
    cb_base = cb[cb.scenario=="base"].sort_values("week_num")
    fig_cash = go.Figure([
        go.Bar(name="avg_cash_collected", x=cb_base["week_label"], y=cb_base["avg_cash_collected"]/1e6,
               marker_color=LBLUE),
        go.Bar(name="avg_cash_burn", x=cb_base["week_label"], y=cb_base["avg_cash_burn"]/1e6,
               marker_color=GREEN),
    ])
    fig_cash.update_layout(**base_layout())
    fig_cash.update_layout(barmode="group", yaxis_tickprefix="$", yaxis_ticksuffix="M",
                           xaxis_tickangle=-30)

    # DSCR multi-scenario line
    fig_dscr = go.Figure()
    colors_sc = {"base": NAVY, "stress_100bps": BLUE, "stress_200bps": AMBER}
    for sc in ["base","stress_100bps","stress_200bps"]:
        df_sc = cov[cov.scenario==sc].sort_values("period")
        fig_dscr.add_trace(go.Scatter(
            x=df_sc["period"], y=df_sc["dscr_proxy"],
            name=sc, line=dict(color=colors_sc[sc], width=2), mode="lines+markers",
            marker=dict(size=5),
        ))
    fig_dscr.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5,
                       annotation_text="Covenant Floor", annotation_position="bottom right")
    fig_dscr.update_layout(**base_layout())
    fig_dscr.update_layout(yaxis_title="Sum of dscr_proxy", xaxis_title="period")

    # Stress table
    stress_tbl = cov.sort_values(["period","scenario"])[["period","scenario","dscr_proxy","net_debt"]].head(24)
    def color_dscr(v):
        if v > 2: return GREEN
        elif v > 0: return AMBER
        else: return RED

    tbl_rows = [
        html.Tr([html.Th(c, style={"padding":"6px 12px","fontSize":"11px","color":SLATE,"fontWeight":"600",
                                    "borderBottom":f"1px solid {GREY}"})
                 for c in ["period","scenario","DSCR","Net Debt"]])
    ]
    for _, row in stress_tbl.iterrows():
        tbl_rows.append(html.Tr([
            html.Td(row["period"],   style={"padding":"5px 12px","fontSize":"12px"}),
            html.Td(row["scenario"], style={"padding":"5px 12px","fontSize":"12px",
                                            "color": AMBER if "stress" in row["scenario"] else DARK}),
            html.Td(f"{row['dscr_proxy']:.2f}", style={"padding":"5px 12px","fontSize":"12px",
                                                         "fontWeight":"700","color":color_dscr(row["dscr_proxy"])}),
            html.Td(f"${row['net_debt']:,.0f}", style={"padding":"5px 12px","fontSize":"12px"}),
        ]))

    stress_table_card = html.Div([
        html.Div("How stressed is our covenant under rate shocks?",
                 style={"fontSize":"13px","fontWeight":"700","color":NAVY,"marginBottom":"12px"}),
        html.Div(
            html.Table(tbl_rows, style={"width":"100%","borderCollapse":"collapse"}),
            style={"maxHeight":"320px","overflowY":"auto"},
        ),
    ], style={"background":CARD,"borderRadius":"10px","padding":"20px 24px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.07)","border":f"1px solid {GREY}","flex":"1"})

    return html.Div([
        page_header(3, "Solvency & Debt", SUBTITLES["cfo3"]),
        page_body(
            kpi_row(
                kpi_card("DSCR Current",    f"{dscr_current:.0f}",   RED if dscr_current < 0 else GREEN),
                kpi_card("Net Debt",        f"${net_debt/1e6:.2f}M", AMBER),
                kpi_card("Total Liabilities",f"${total_liab/1e6:.1f}M", AMBER),
                kpi_card("AR Outstanding",  f"${ar_out/1e6:.2f}M",  BLUE),
            ),
            chart_card("Are payables outpacing receivables?", fig_cash),
            chart_row(
                html.Div(chart_card("Are we at risk of breaching our debt covenant?", fig_dscr), style={"flex":"1"}),
                stress_table_card,
            ),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# CFO 4 — UNIT ECONOMICS
# ═══════════════════════════════════════════════════════════════════════════════
def build_cfo4():
    gl4 = gl.copy()
    gl4["period_start"] = pd.to_datetime(gl4["period_start"])
    rev_m  = gl4[gl4.category=="Revenue"].groupby("period_start")["credit_amount"].sum().sort_index()
    cogs_m = gl4[gl4.category=="COGS"].groupby("period_start")["debit_amount"].sum().sort_index()
    opex_m = gl4[gl4.category=="OpEx"].groupby("period_start")["debit_amount"].sum().sort_index()

    gross_margin_pct = ((rev_m - cogs_m) / rev_m * 100)
    ebitda_pct = ((rev_m - cogs_m - opex_m) / rev_m * 100)
    budget_amt = budget["budget_amount"].iloc[0]
    gross_profit = (rev_m - cogs_m).sum()
    budget_variance = rev_m.sum() - budget_amt

    # Revenue vs OpEx grouped bar
    fig_rev_opex = go.Figure([
        go.Bar(name="Revenue Monthly", x=rev_m.index, y=rev_m.values/1e6, marker_color="#A8C4E8"),
        go.Bar(name="Opex Monthly",    x=opex_m.index, y=opex_m.values/1e6, marker_color=LBLUE),
    ])
    fig_rev_opex.update_layout(**base_layout())
    fig_rev_opex.update_layout(barmode="group", yaxis_tickprefix="$", yaxis_ticksuffix="M",
                                xaxis_tickangle=-30)

    # 12m forecast area
    fig_fcast = go.Figure([
        go.Scatter(x=fcast["forecast_month"], y=fcast["upper_bound"]/1e6,
                   fill=None, line=dict(color="rgba(68,114,196,0)"), showlegend=False),
        go.Scatter(x=fcast["forecast_month"], y=fcast["lower_bound"]/1e6,
                   fill="tonexty", fillcolor="rgba(68,114,196,0.12)",
                   line=dict(color="rgba(68,114,196,0)"), name="Confidence Band"),
        go.Scatter(x=fcast["forecast_month"], y=fcast["revenue_forecast"]/1e6,
                   fill="tozeropy", fillcolor="rgba(68,114,196,0.2)",
                   line=dict(color=LBLUE, width=2), name="Revenue Forecast",
                   mode="lines+markers", marker=dict(size=5)),
    ])
    fig_fcast.update_layout(**base_layout())
    fig_fcast.update_layout(yaxis_tickprefix="$", yaxis_ticksuffix="M",
                             xaxis_title="forecast_month")

    # Margin compression dual-area
    fig_margin = go.Figure([
        go.Scatter(x=gross_margin_pct.index, y=gross_margin_pct.values,
                   fill="tozeropy", fillcolor="rgba(30,58,138,0.15)",
                   line=dict(color=NAVY, width=2), name="Gross Margin %", mode="lines"),
        go.Scatter(x=ebitda_pct.index, y=ebitda_pct.values,
                   fill="tozeropy", fillcolor="rgba(5,150,105,0.15)",
                   line=dict(color=GREEN, width=2), name="EBITDA Margin Monthly %", mode="lines"),
    ])
    fig_margin.add_hline(y=0, line_color=RED, line_width=1)
    fig_margin.update_layout(**base_layout())
    fig_margin.update_layout(yaxis_ticksuffix="%", xaxis_title="Month")

    return html.Div([
        page_header(4, "Unit Economics", SUBTITLES["cfo4"]),
        page_body(
            kpi_row(
                kpi_card("Gross Margin %",         f"{gross_margin_pct.mean():.1f}%",  GREEN),
                kpi_card("EBITDA Margin Monthly %", f"{ebitda_pct.mean():.1f}%",       AMBER),
                kpi_card("Gross Profit",            f"${gross_profit/1e6:.2f}M",       NAVY),
                kpi_card("Budget Variance",         f"${budget_variance/1e6:.2f}M",    GREEN if budget_variance>0 else RED),
            ),
            chart_row(
                html.Div(chart_card("Is revenue growing faster than costs?", fig_rev_opex), style={"flex":"1"}),
                html.Div(chart_card("What does our 12-month revenue outlook look like?", fig_fcast), style={"flex":"1"}),
            ),
            chart_card("Is cost pressure widening our margin gap?", fig_margin, height=280),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# CFO 5 — 13-WEEK CASH FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
def build_cfo5():
    cb_base = cb[cb.scenario=="base"].sort_values("week_num")
    week13_bal = cb_base["running_balance"].iloc[-1]
    weekly_burn = cb_base["avg_cash_burn"].mean()
    cash_runway = int(week13_bal / weekly_burn) if weekly_burn > 0 else 99
    ar_out = ar[~ar.paid]["amount"].sum()

    # Triple line chart
    fig_triple = make_subplots(specs=[[{"secondary_y":True}]])
    fig_triple.add_trace(go.Scatter(x=cb_base["week_label"], y=cb_base["avg_cash_collected"]/1e6,
                                    name="avg_cash_collected", line=dict(color=BLUE, width=2),
                                    mode="lines+markers", marker=dict(size=5)), secondary_y=False)
    fig_triple.add_trace(go.Scatter(x=cb_base["week_label"], y=cb_base["avg_cash_burn"]/1e6,
                                    name="avg_cash_burn", line=dict(color=LBLUE, width=2),
                                    mode="lines+markers", marker=dict(size=5)), secondary_y=False)
    fig_triple.add_trace(go.Scatter(x=cb_base["week_label"], y=cb_base["running_balance"]/1e6,
                                    name="running_balance", line=dict(color=AMBER, width=2.5),
                                    mode="lines+markers", marker=dict(size=5)), secondary_y=True)
    fig_triple.update_layout(**base_layout())
    fig_triple.update_layout(legend=dict(orientation="h", y=1.05))
    fig_triple.update_yaxes(tickprefix="$", ticksuffix="M", secondary_y=False, gridcolor=GRID)
    fig_triple.update_yaxes(tickprefix="$", ticksuffix="M", secondary_y=True, showgrid=False)
    fig_triple.update_layout(xaxis=dict(tickangle=-30))

    # Weekly data table
    tbl_cols = ["week_label","avg_cash_collected","avg_cash_burn","running_balance"]
    tbl_head = html.Tr([
        html.Th(c, style={"padding":"6px 12px","fontSize":"11px","color":SLATE,"fontWeight":"600",
                           "borderBottom":f"1px solid {GREY}"})
        for c in ["week_label","avg_cash_collected","avg_cash_burn","running_balance"]
    ])
    tbl_rows_data = [tbl_head]
    for _, row in cb_base.iterrows():
        tbl_rows_data.append(html.Tr([
            html.Td(row["week_label"], style={"padding":"5px 12px","fontSize":"12px","color":BLUE,"fontWeight":"600"}),
            html.Td(f"${row['avg_cash_collected']:,.0f}", style={"padding":"5px 12px","fontSize":"12px"}),
            html.Td(f"${row['avg_cash_burn']:,.0f}",      style={"padding":"5px 12px","fontSize":"12px","color":AMBER}),
            html.Td(f"${row['running_balance']:,.0f}",    style={"padding":"5px 12px","fontSize":"12px","fontWeight":"700","color":GREEN}),
        ]))
    # Totals row
    tbl_rows_data.append(html.Tr([
        html.Td("Total", style={"padding":"5px 12px","fontSize":"12px","fontWeight":"700"}),
        html.Td(f"${cb_base['avg_cash_collected'].sum():,.0f}", style={"padding":"5px 12px","fontSize":"12px","fontWeight":"700","color":BLUE}),
        html.Td(f"${cb_base['avg_cash_burn'].sum():,.0f}",      style={"padding":"5px 12px","fontSize":"12px","fontWeight":"700","color":AMBER}),
        html.Td(f"${cb_base['running_balance'].sum():,.0f}",    style={"padding":"5px 12px","fontSize":"12px","fontWeight":"700","color":GREEN}),
    ], style={"borderTop":f"2px solid {GREY}"}))

    tbl_card = html.Div([
        html.Div("How sensitive are we to late payments?",
                 style={"fontSize":"13px","fontWeight":"700","color":NAVY,"marginBottom":"12px"}),
        html.Div(html.Table(tbl_rows_data, style={"width":"100%","borderCollapse":"collapse"}),
                 style={"overflowX":"auto"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"20px 24px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.07)","border":f"1px solid {GREY}","flex":"1"})

    # Vendor payables bar
    ap_vendor = ap.groupby("vendor_id")["amount"].sum().sort_values(ascending=False).head(25)
    fig_ap = go.Figure(go.Bar(
        x=ap_vendor.index, y=ap_vendor.values/1e6,
        marker_color=LBLUE,
    ))
    fig_ap.update_layout(**base_layout())
    fig_ap.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M",
                          xaxis_title="vendor_id")

    return html.Div([
        page_header(5, "13-Week Cash Forecast", SUBTITLES["cfo5"]),
        page_body(
            kpi_row(
                kpi_card("Week 13 Cash Balance", f"${week13_bal/1e6:.1f}M",   GREEN),
                kpi_card("Weekly Burn Rate",     f"${weekly_burn/1e3:.1f}K",  AMBER),
                kpi_card("Cash Runway Weeks",    f"{cash_runway}",            GREEN),
                kpi_card("AR Outstanding",       f"${ar_out/1e6:.2f}M",       BLUE),
            ),
            chart_card("When does our cash balance hit the danger zone?", fig_triple, height=320),
            chart_row(
                tbl_card,
                html.Div(chart_card("Where are near-term payables concentrated?", fig_ap), style={"flex":"1"}),
            ),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# CFO 6 — STRATEGIC MODEL
# ═══════════════════════════════════════════════════════════════════════════════
def build_cfo6():
    gl6 = gl.copy()
    gl6["period_start"] = pd.to_datetime(gl6["period_start"])
    rev_m  = gl6[gl6.category=="Revenue"].groupby("period_start")["credit_amount"].sum().sort_index()
    cogs_m = gl6[gl6.category=="COGS"].groupby("period_start")["debit_amount"].sum().sort_index()
    opex_m = gl6[gl6.category=="OpEx"].groupby("period_start")["debit_amount"].sum().sort_index()

    rev_total  = rev_m.sum()
    gross_m    = ((rev_m - cogs_m) / rev_m * 100).mean()
    week13_bal = cb[cb.scenario=="base"]["running_balance"].max()
    base_cov   = cov[cov.scenario=="base"]
    dscr_curr  = base_cov["dscr_proxy"].iloc[-1]

    # 12m forecast line
    fig_fcast = go.Figure(go.Scatter(
        x=fcast["forecast_month"], y=fcast["revenue_forecast"]/1e6,
        fill="tozeropy", fillcolor="rgba(68,114,196,0.15)",
        line=dict(color=LBLUE, width=2), mode="lines+markers", marker=dict(size=5),
        name="Revenue Forecast",
    ))
    fig_fcast.update_layout(**base_layout())
    fig_fcast.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M",
                             xaxis_title="forecast_month")

    # Historical revenue area
    fig_hist = go.Figure(go.Scatter(
        x=rev_m.index, y=rev_m.values/1e6,
        fill="tozeropy", fillcolor="rgba(30,58,138,0.12)",
        line=dict(color=NAVY, width=2), mode="lines", name="Revenue",
    ))
    fig_hist.update_layout(**base_layout())
    fig_hist.update_layout(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M",
                            xaxis_title="Month")

    # YoY grouped bar
    rev_yoy  = rev_m.pct_change(12).dropna()
    opex_yoy = opex_m.pct_change(12).dropna()
    common_idx = rev_yoy.index.intersection(opex_yoy.index)
    fig_yoy = go.Figure([
        go.Bar(x=common_idx, y=rev_yoy[common_idx].values * 100,
               name="Revenue YoY%", marker_color=LBLUE),
        go.Bar(x=common_idx, y=opex_yoy[common_idx].values * 100,
               name="Opex YoY%", marker_color="#6B88D4"),
    ])
    fig_yoy.add_hline(y=0, line_color=RED, line_width=1)
    fig_yoy.update_layout(**base_layout())
    fig_yoy.update_layout(barmode="group", yaxis_ticksuffix="%", xaxis_title="Month")

    return html.Div([
        page_header(6, "Strategic Model", SUBTITLES["cfo6"]),
        page_body(
            kpi_row(
                kpi_card("Revenue (Total)",  f"${rev_total/1e6:.2f}M",  NAVY),
                kpi_card("DSCR Current",     f"{dscr_curr:.0f}",        RED if dscr_curr<0 else GREEN),
                kpi_card("Gross Margin %",   f"{gross_m:.1f}%",         AMBER),
                kpi_card("Week 13 Cash Balance", f"${week13_bal/1e6:.1f}M", GREEN),
            ),
            chart_row(
                html.Div(chart_card("Where is our revenue heading in the next 12 months?", fig_fcast), style={"flex":"1"}),
                html.Div(chart_card("Is the business structurally healthy?", fig_hist), style={"flex":"1"}),
            ),
            chart_card("Is revenue growing faster than costs?", fig_yoy, height=280),
        ),
    ])

# ── PAGE DISPATCH ─────────────────────────────────────────────────────────────
PAGE_BUILDERS = {
    "cfo1": build_cfo1,
    "cfo2": build_cfo2,
    "cfo3": build_cfo3,
    "cfo4": build_cfo4,
    "cfo5": build_cfo5,
    "cfo6": build_cfo6,
}

# ── CALLBACKS ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("active-page", "data"),
    [Input({"type":"nav","index":pid}, "n_clicks") for pid,_ in PAGES],
    prevent_initial_call=True,
)
def update_active(*args):
    from dash import ctx
    if not ctx.triggered_id:
        return "cfo1"
    return ctx.triggered_id["index"]

@app.callback(
    Output("sidebar-container", "children"),
    Input("active-page", "data"),
)
def update_sidebar(active):
    return sidebar(active)

@app.callback(
    Output("page-content", "children"),
    Input("active-page", "data"),
)
def render_page(page):
    builder = PAGE_BUILDERS.get(page, build_cfo1)
    return builder()

if __name__ == "__main__":
    app.run(debug=True, port=8050)

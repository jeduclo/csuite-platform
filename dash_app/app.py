"""
CFO Intelligence App — Plotly Dash (Parquet / Demo Edition)
6 pages · light theme · navy palette · icon nav · zero DB
"""
import os
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, State, ctx

# ── DATA ──────────────────────────────────────────────────────────────────────
DATA = os.path.join(os.path.dirname(__file__), "data")
def load(name): return pd.read_parquet(os.path.join(DATA, f"{name}.parquet"))

gl     = load("gl");     gl["period_start"] = pd.to_datetime(gl["period_start"])
ar     = load("ar");     ar["due_date"]      = pd.to_datetime(ar["due_date"])
ap     = load("ap")
cb     = load("cash_burn")
cov    = load("covenant")
fcast  = load("forecast"); fcast["forecast_month"] = pd.to_datetime(fcast["forecast_month"])
budget = load("budget")

# ── TOKENS ────────────────────────────────────────────────────────────────────
BG    = "#F8FAFC"; CARD  = "#FFFFFF"; GREY  = "#E2E8F0"; GRID  = "#F1F5F9"
NAVY  = "#1E3A8A"; BLUE  = "#2563EB"; LBLUE = "#4472C4"; NAVY2 = "#3B5BA5"
SLATE = "#64748B"; DARK  = "#0F172A"
GREEN = "#059669"; AMBER = "#D97706"; RED   = "#DC2626"
C1=NAVY; C2=BLUE; C3=LBLUE; C4=NAVY2  # chart colour family

# ── SVG ICONS ─────────────────────────────────────────────────────────────────
ICONS = {
    "cfo1": "📈",
    "cfo2": "⚖️",
    "cfo3": "🏦",
    "cfo4": "📊",
    "cfo5": "📅",
    "cfo6": "🧭",
}

def nav_icon(pid):
    return html.Span(ICONS[pid], style={"marginRight":"8px","fontSize":"13px"})

# ── PAGES DEF ─────────────────────────────────────────────────────────────────
PAGES = [
    ("cfo1","Financial Velocity"),
    ("cfo2","Working Capital"),
    ("cfo3","Solvency & Debt"),
    ("cfo4","Unit Economics"),
    ("cfo5","13-Week Cash Forecast"),
    ("cfo6","Strategic Model"),
]
SUBTITLES = {
    "cfo1":"Is the business generating cash efficiently?",
    "cfo2":"How efficiently are we managing the cash conversion cycle?",
    "cfo3":"Are we solvent and within our covenants?",
    "cfo4":"Are our margins healthy at the unit level?",
    "cfo5":"Do we have a cash problem in the next quarter?",
    "cfo6":"Is the business structurally healthy for the next 12 months?",
}

# ── APP ───────────────────────────────────────────────────────────────────────
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ── LAYOUT HELPERS ────────────────────────────────────────────────────────────
def kpi(label, value, color=NAVY):
    return html.Div([
        html.Div(value, style={"fontSize":"26px","fontWeight":"800","color":color,"marginBottom":"4px","letterSpacing":"-0.5px"}),
        html.Div(label, style={"fontSize":"10px","fontWeight":"700","color":SLATE,"letterSpacing":"0.09em","textTransform":"uppercase"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"18px 22px","flex":"1",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.06)","border":f"1px solid {GREY}"})

def card(title, fig, height=330):
    return html.Div([
        html.Div(title, style={"fontSize":"12px","fontWeight":"700","color":NAVY,"marginBottom":"10px"}),
        dcc.Graph(figure=fig, config={"displayModeBar":False}, style={"height":f"{height}px"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"18px 22px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.06)","border":f"1px solid {GREY}"})

def bl(**kw):  # base layout
    d = dict(paper_bgcolor=CARD, plot_bgcolor=CARD,
             font=dict(family="Inter,system-ui,sans-serif", size=11, color=DARK),
             margin=dict(l=8,r=8,t=8,b=8),
             xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10), color=SLATE),
             yaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(size=10), color=SLATE),
             legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="left",x=0,font=dict(size=10)),
             hovermode="x unified")
    d.update(kw)
    return d

def row(*items): return html.Div(list(items), style={"display":"flex","gap":"16px"})
def col(content, flex="1"): return html.Div(content, style={"flex":flex})

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def sidebar(active):
    links = []
    for pid, label in PAGES:
        is_active = pid == active
        links.append(html.Div(
            [nav_icon(pid), html.Span(label)],
            id={"type":"nav","index":pid}, n_clicks=0,
            style={
                "display":"flex","alignItems":"center",
                "padding":"9px 14px","cursor":"pointer","borderRadius":"7px",
                "fontSize":"12px","fontWeight":"600" if is_active else "400",
                "color":BLUE if is_active else SLATE,
                "background":"#EFF6FF" if is_active else "transparent",
                "borderLeft":f"3px solid {BLUE}" if is_active else f"3px solid transparent",
                "marginBottom":"2px","transition":"all 0.12s",
            }
        ))
    return html.Div([
        html.Div([
            html.Div("CFO", style={"fontSize":"15px","fontWeight":"900","color":NAVY,"letterSpacing":"0.06em"}),
            html.Div("INTELLIGENCE APP", style={"fontSize":"8px","fontWeight":"700","color":SLATE,"letterSpacing":"0.18em","marginTop":"1px"}),
        ], style={"padding":"20px 14px 14px","borderBottom":f"1px solid {GREY}","marginBottom":"10px"}),
        html.Div(links, style={"padding":"0 6px"}),
        html.Div([
            html.Div("LAST REFRESHED", style={"fontSize":"9px","color":SLATE,"fontWeight":"700","letterSpacing":"0.08em"}),
            html.Div(datetime.now().strftime("%b %d, %Y %H:%M"),
                     style={"fontSize":"11px","color":DARK,"marginTop":"2px"}),
        ], style={"position":"absolute","bottom":"20px","left":"14px"}),
    ], style={"width":"175px","minWidth":"175px","background":CARD,"height":"100vh",
              "borderRight":f"1px solid {GREY}","position":"relative","flexShrink":"0"})

def header(num, title, sub):
    return html.Div([
        html.Div(f"CFO {num}", style={"fontSize":"10px","color":BLUE,"fontWeight":"700","letterSpacing":"0.1em","marginBottom":"3px"}),
        html.Div([
            html.Span(title, style={"fontSize":"20px","fontWeight":"800","color":DARK}),
            html.Span(sub, style={"fontSize":"13px","color":SLATE,"fontStyle":"italic","marginLeft":"auto","fontWeight":"500"}),
        ], style={"display":"flex","alignItems":"baseline","gap":"12px","justifyContent":"space-between"}),
    ], style={"padding":"20px 28px 14px","borderBottom":f"1px solid {GREY}","background":CARD})

def body(*rows_):
    return html.Div(list(rows_), style={"padding":"18px 28px","display":"flex","flexDirection":"column","gap":"14px"})

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        html.Div(id="sidebar-container"),
        html.Div(id="page-content", style={"flex":"1","overflowY":"auto","background":BG}),
    ], style={"display":"flex","height":"100vh","fontFamily":"Inter,system-ui,sans-serif"}),
], style={"margin":"0","padding":"0"})

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def cfo1():
    rev_m  = gl[gl.category=="Revenue"].groupby("period_start")["credit_amount"].sum().sort_index()
    cogs_m = gl[gl.category=="COGS"].groupby("period_start")["debit_amount"].sum().sort_index()
    opex_m = gl[gl.category=="OpEx"].groupby("period_start")["debit_amount"].sum().sort_index()
    rev=rev_m.sum(); cogs=cogs_m.sum(); opex=opex_m.sum()
    ebitda_m_pct = (rev-cogs-opex)/rev*100
    coll_rate = ar[ar.paid]["amount"].sum()/ar["amount"].sum()*100

    # Waterfall
    fig_wf = go.Figure(go.Waterfall(
        orientation="v", measure=["absolute","relative","relative","total"],
        x=["Revenue","COGS","OpEx","EBITDA"],
        y=[rev, -cogs, -opex, 0],
        text=[f"${v/1e6:.1f}M" for v in [rev,-cogs,-opex,(rev-cogs-opex)]],
        textposition="outside",
        connector=dict(line=dict(color=GREY,width=1)),
        increasing=dict(marker=dict(color=LBLUE)),
        decreasing=dict(marker=dict(color="#94A3B8")),
        totals=dict(marker=dict(color=NAVY)),
    ))
    fig_wf.update_layout(**bl(showlegend=False, yaxis_tickformat=".2s", yaxis_tickprefix="$"))

    # Revenue by account (all-time)
    rev_acct = gl[gl.category=="Revenue"].groupby("account_name")["credit_amount"].sum().sort_values(ascending=False)
    fig_acct = go.Figure(go.Bar(
        x=rev_acct.index, y=rev_acct.values/1e6,
        marker_color=[NAVY, BLUE, LBLUE, NAVY2],
        text=[f"${v/1e6:.1f}M" for v in rev_acct.values], textposition="outside",
    ))
    fig_acct.update_layout(**bl(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M", xaxis_tickangle=-25))

    # Dual-axis monthly
    ebitda_pct = ((rev_m - cogs_m - opex_m)/rev_m*100).sort_index()
    fig_dual = make_subplots(specs=[[{"secondary_y":True}]])
    fig_dual.add_trace(go.Bar(x=rev_m.index, y=rev_m.values/1e6, name="Revenue Monthly",
                              marker_color=LBLUE, opacity=0.8), secondary_y=False)
    fig_dual.add_trace(go.Scatter(x=ebitda_pct.index, y=ebitda_pct.values,
                                  name="EBITDA Margin %", line=dict(color=NAVY,width=2.5),
                                  mode="lines"), secondary_y=True)
    fig_dual.add_hline(y=0, line_color=RED, line_width=1, secondary_y=True)
    fig_dual.update_layout(**bl())
    fig_dual.update_layout(legend=dict(orientation="h",y=1.06))
    fig_dual.update_yaxes(tickprefix="$",ticksuffix="M",gridcolor=GRID,secondary_y=False)
    fig_dual.update_yaxes(ticksuffix="%",showgrid=False,secondary_y=True)

    return html.Div([
        header(1,"Financial Velocity",SUBTITLES["cfo1"]),
        body(
            row(kpi("Revenue YTD",f"${rev/1e6:.1f}M",NAVY),
                kpi("Total OpEx",f"${opex/1e6:.1f}M",AMBER),
                kpi("EBITDA Margin %",f"{ebitda_m_pct:.1f}%",GREEN if ebitda_m_pct>0 else RED),
                kpi("Collection Rate",f"{coll_rate:.1f}%",GREEN)),
            row(col(card("Where is margin being lost?",fig_wf)),
                col(card("Which accounts drive revenue?",fig_acct))),
            card("Is our margin improving or compressing?",fig_dual,height=290),
        ),
    ])

def cfo2():
    # Only unpaid invoices count as AR outstanding
    unpaid = ar[~ar.paid].copy()
    ar_out = unpaid["amount"].sum()
    # Weighted DSO (by amount) — realistic
    dso = (unpaid["days_past_due"] * unpaid["amount"]).sum() / unpaid["amount"].sum() if len(unpaid) else 0
    coll_rate = ar[ar.paid]["amount"].sum() / ar["amount"].sum() * 100
    cb_base = cb[cb.scenario=="base"]
    week13_bal = cb_base["running_balance"].iloc[-1]
    weekly_burn = cb_base["avg_cash_burn"].mean()
    cash_runway = int(week13_bal / weekly_burn) if weekly_burn > 0 else 99

    # Customer risk scatter — unpaid only, aggregate per customer
    cust_risk = unpaid.groupby("customer_id").agg(
        ar_out=("amount","sum"), avg_dpd=("days_past_due","mean")).reset_index()
    # Add small jitter to zero-DPD points so they don't stack
    x_vals = cust_risk["avg_dpd"].values.copy().astype(float)
    zero_mask = x_vals == 0
    x_vals[zero_mask] = np.random.uniform(0.3, 1.8, zero_mask.sum())
    fig_scatter = go.Figure(go.Scatter(
        x=x_vals, y=cust_risk["ar_out"]/1e3,
        mode="markers",
        marker=dict(size=cust_risk["ar_out"]/cust_risk["ar_out"].max()*18+6,
                    color=cust_risk["avg_dpd"].values,
                    colorscale=[[0,LBLUE],[0.5,BLUE],[1,NAVY]],
                    showscale=False, opacity=0.78),
        hovertemplate="<b>%{customdata}</b><br>DPD: %{x:.0f}<br>AR: $%{y:.0f}K<extra></extra>",
        customdata=cust_risk["customer_id"],
    ))
    fig_scatter.add_vline(x=30, line_color=AMBER, line_dash="dash", line_width=1.5,
                          annotation_text="30-day threshold", annotation_font_color=AMBER)
    fig_scatter.update_layout(**bl(showlegend=False,
                                   xaxis_title="Days Past Due",
                                   yaxis_title="AR Outstanding ($K)"))
    fig_scatter.update_xaxes(range=[0, max(cust_risk["avg_dpd"].max()*1.1, 35)])

    # AR aging — unpaid invoices only, bucketed by days_past_due
    def bucket(dpd):
        if dpd <= 0:  return "Current"
        elif dpd <= 30: return "1–30"
        elif dpd <= 60: return "31–60"
        elif dpd <= 90: return "61–90"
        else:           return "91+"
    unpaid2 = unpaid.copy()
    unpaid2["bucket"] = unpaid2["days_past_due"].apply(bucket)
    aging = unpaid2.groupby("bucket")["amount"].sum().reindex(
        ["Current","1–30","31–60","61–90","91+"], fill_value=0)
    fig_aging = go.Figure(go.Bar(
        x=aging.index, y=aging.values/1e3,
        marker_color=[NAVY, BLUE, LBLUE, AMBER, RED],
        text=[f"${v/1e3:.0f}K" for v in aging.values], textposition="outside",
    ))
    fig_aging.update_layout(**bl(showlegend=False, yaxis_title="AR ($K)",
                                  yaxis_tickprefix="$", yaxis_ticksuffix="K"))

    # DSO trend — monthly weighted DSO (unpaid only)
    unpaid3 = unpaid.copy()
    unpaid3["month"] = pd.to_datetime(unpaid3["due_date"]).dt.to_period("M").dt.to_timestamp()
    dso_m = (unpaid3.groupby("month")
             .apply(lambda g: (g["days_past_due"]*g["amount"]).sum()/g["amount"].sum()
                    if g["amount"].sum()>0 else 0)
             .sort_index())
    fig_dso = go.Figure(go.Scatter(
        x=dso_m.index, y=dso_m.values,
        fill="tozeroy", fillcolor="rgba(68,114,196,0.12)",
        line=dict(color=NAVY, width=2.5), mode="lines+markers",
        marker=dict(size=5, color=NAVY), name="Weighted DSO",
    ))
    fig_dso.add_hline(y=30, line_color=AMBER, line_dash="dot", line_width=1.5,
                      annotation_text="30-day target", annotation_font_color=AMBER)
    fig_dso.update_layout(**bl(showlegend=False, yaxis_title="Weighted Days Past Due",
                                xaxis_title="Month"))

    return html.Div([
        header(2,"Working Capital & Liquidity Risk",SUBTITLES["cfo2"]),
        body(
            row(kpi("AR Outstanding", f"${ar_out/1e3:.0f}K", NAVY),
                kpi("Weighted DSO",   f"{dso:.1f} days",     AMBER if dso>20 else GREEN),
                kpi("Collection Rate",f"{coll_rate:.1f}%",   GREEN),
                kpi("Cash Runway (Gross)",f"{cash_runway} wks", GREEN if cash_runway>8 else AMBER)),
            row(col(card("Which customers carry the most overdue risk?", fig_scatter)),
                col(card("Where is AR risk concentrated?", fig_aging))),
            card("Are we collecting faster or slower over time?", fig_dso, height=270),
        ),
    ])

def cfo3():
    base_cov = cov[cov.scenario=="base"].sort_values("period")
    dscr_now = base_cov["dscr_proxy"].iloc[-1]
    net_debt = base_cov["net_debt"].iloc[-1]
    total_liab = base_cov["total_liabilities"].iloc[-1]
    ar_out = ar[~ar.paid]["amount"].sum()

    # Cash collected vs burn
    cb_base = cb[cb.scenario=="base"].sort_values("week_num")
    fig_cash = go.Figure([
        go.Bar(name="Cash Collected", x=cb_base["week_label"], y=cb_base["avg_cash_collected"]/1e6,
               marker_color=NAVY, opacity=0.85),
        go.Bar(name="Cash Burn", x=cb_base["week_label"], y=cb_base["avg_cash_burn"]/1e6,
               marker_color=LBLUE, opacity=0.85),
    ])
    fig_cash.update_layout(**bl(barmode="group", yaxis_tickprefix="$", yaxis_ticksuffix="M",
                                xaxis_tickangle=-30))

    # DSCR trend — smooth lines, clear narrative
    fig_dscr = go.Figure()
    sc_styles = {
        "base":          dict(color=NAVY,  width=2.5, dash="solid"),
        "stress_100bps": dict(color=BLUE,  width=2,   dash="dot"),
        "stress_200bps": dict(color=LBLUE, width=2,   dash="dash"),
    }
    for sc in ["base","stress_100bps","stress_200bps"]:
        df_sc = cov[cov.scenario==sc].sort_values("period")
        fig_dscr.add_trace(go.Scatter(
            x=df_sc["period"], y=df_sc["dscr_proxy"],
            name=sc, line=sc_styles[sc], mode="lines+markers",
            marker=dict(size=4, color=sc_styles[sc]["color"]),
        ))
    fig_dscr.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5,
                       annotation_text="Covenant Floor (DSCR = 0)",
                       annotation_position="bottom right",
                       annotation_font_color=RED, annotation_font_size=10)
    fig_dscr.add_hrect(y0=-5, y1=0, fillcolor="rgba(220,38,38,0.06)", line_width=0)
    fig_dscr.update_layout(**bl(yaxis_title="DSCR Proxy", xaxis_title="Period"))

    # Stress table
    stress_rows = [html.Tr([
        html.Th(c, style={"padding":"6px 10px","fontSize":"10px","color":SLATE,
                           "fontWeight":"700","borderBottom":f"1px solid {GREY}","textTransform":"uppercase"})
        for c in ["Period","Scenario","DSCR","Net Debt"]
    ])]
    tbl_data = cov.sort_values(["period","scenario"]).head(21)
    for _, r in tbl_data.iterrows():
        dscr_color = GREEN if r["dscr_proxy"]>1.5 else (AMBER if r["dscr_proxy"]>0 else RED)
        stress_rows.append(html.Tr([
            html.Td(r["period"], style={"padding":"5px 10px","fontSize":"11px"}),
            html.Td(r["scenario"], style={"padding":"5px 10px","fontSize":"11px",
                                          "color":AMBER if "stress" in r["scenario"] else DARK}),
            html.Td(f"{r['dscr_proxy']:.2f}", style={"padding":"5px 10px","fontSize":"11px",
                                                      "fontWeight":"700","color":dscr_color}),
            html.Td(f"${r['net_debt']:,.0f}", style={"padding":"5px 10px","fontSize":"11px"}),
        ]))

    tbl_card = html.Div([
        html.Div("How stressed is our covenant under rate shocks?",
                 style={"fontSize":"12px","fontWeight":"700","color":NAVY,"marginBottom":"10px"}),
        html.Div(html.Table(stress_rows, style={"width":"100%","borderCollapse":"collapse"}),
                 style={"maxHeight":"310px","overflowY":"auto"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"18px 22px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.06)","border":f"1px solid {GREY}","flex":"1"})

    return html.Div([
        header(3,"Solvency & Debt",SUBTITLES["cfo3"]),
        body(
            row(kpi("DSCR Current",f"{dscr_now:.1f}x", GREEN if dscr_now>1.5 else (AMBER if dscr_now>0 else RED)),
                kpi("Net Debt",f"${net_debt/1e6:.2f}M",AMBER),
                kpi("Total Liabilities",f"${total_liab/1e6:.1f}M",AMBER),
                kpi("AR Outstanding",f"${ar_out/1e6:.2f}M",BLUE)),
            card("Are payables outpacing receivables?",fig_cash),
            row(col(card("Are we at risk of breaching our debt covenant?",fig_dscr)),
                tbl_card),
        ),
    ])

def cfo4():
    rev_m  = gl[gl.category=="Revenue"].groupby("period_start")["credit_amount"].sum().sort_index()
    cogs_m = gl[gl.category=="COGS"].groupby("period_start")["debit_amount"].sum().sort_index()
    opex_m = gl[gl.category=="OpEx"].groupby("period_start")["debit_amount"].sum().sort_index()

    gross_m_pct  = ((rev_m - cogs_m)/rev_m*100).sort_index()
    ebitda_m_pct = ((rev_m - cogs_m - opex_m)/rev_m*100).sort_index()
    budget_amt = budget["budget_amount"].iloc[0]
    gross_profit = (rev_m - cogs_m).sum()
    budget_var = rev_m.sum() - budget_amt

    # Rev vs OpEx grouped bar
    fig_re = go.Figure([
        go.Bar(name="Revenue", x=rev_m.index, y=rev_m.values/1e6, marker_color=NAVY, opacity=0.85),
        go.Bar(name="OpEx",    x=opex_m.index, y=opex_m.values/1e6, marker_color=LBLUE, opacity=0.85),
    ])
    fig_re.update_layout(**bl(barmode="group", yaxis_tickprefix="$", yaxis_ticksuffix="M", xaxis_tickangle=-30))

    # 12m forecast area with confidence band
    fig_fc = go.Figure([
        go.Scatter(x=fcast["forecast_month"], y=fcast["upper_bound"]/1e6,
                   fill=None, line=dict(color="rgba(68,114,196,0)"), showlegend=False, name="Upper"),
        go.Scatter(x=fcast["forecast_month"], y=fcast["lower_bound"]/1e6,
                   fill="tonexty", fillcolor="rgba(68,114,196,0.12)",
                   line=dict(color="rgba(68,114,196,0)"), name="P10-P90 Band"),
        go.Scatter(x=fcast["forecast_month"], y=fcast["revenue_forecast"]/1e6,
                   fill="tozeroy", fillcolor="rgba(30,58,138,0.08)",
                   line=dict(color=NAVY, width=2.5), mode="lines+markers",
                   marker=dict(size=5, color=NAVY), name="P50 Forecast"),
    ])
    fig_fc.update_layout(**bl(yaxis_tickprefix="$", yaxis_ticksuffix="M", xaxis_title="Month"))

    # Margin compression — dual axis so both lines are readable
    fig_mg = make_subplots(specs=[[{"secondary_y":True}]])
    fig_mg.add_trace(go.Scatter(x=gross_m_pct.index, y=gross_m_pct.values,
                   fill="tozeroy", fillcolor="rgba(30,58,138,0.10)",
                   line=dict(color=NAVY, width=2.5), name="Gross Margin %", mode="lines"),
                   secondary_y=False)
    fig_mg.add_trace(go.Scatter(x=ebitda_m_pct.index, y=ebitda_m_pct.values,
                   fill="tozeroy", fillcolor="rgba(68,114,196,0.15)",
                   line=dict(color=BLUE, width=2), name="EBITDA Margin %", mode="lines"),
                   secondary_y=True)
    fig_mg.add_hline(y=0, line_color=RED, line_width=1.2, secondary_y=True)
    fig_mg.update_layout(**bl(xaxis_title="Month"))
    fig_mg.update_yaxes(ticksuffix="%", title_text="Gross Margin %", gridcolor=GRID, secondary_y=False)
    fig_mg.update_yaxes(ticksuffix="%", title_text="EBITDA Margin %", showgrid=False, secondary_y=True)

    return html.Div([
        header(4,"Unit Economics",SUBTITLES["cfo4"]),
        body(
            row(kpi("Gross Margin %", f"{gross_m_pct.mean():.1f}%", GREEN),
                kpi("EBITDA Margin %", f"{ebitda_m_pct.mean():.1f}%", AMBER if ebitda_m_pct.mean()>0 else RED),
                kpi("Gross Profit", f"${gross_profit/1e6:.2f}M", NAVY),
                kpi("vs Budget", f"{'+'if budget_var>=0 else ''}${budget_var/1e6:.1f}M",
                    GREEN if budget_var>=0 else RED)),
            row(col(card("Is revenue growing faster than costs?", fig_re)),
                col(card("What does our 12-month revenue outlook look like?", fig_fc))),
            card("Is cost pressure widening our margin gap?", fig_mg, height=270),
        ),
    ])

def cfo5():
    cb_base = cb[cb.scenario=="base"].sort_values("week_num")
    week13_bal = cb_base["running_balance"].iloc[-1]
    weekly_burn = cb_base["avg_cash_burn"].mean()
    cash_runway = int(week13_bal/weekly_burn) if weekly_burn>0 else 99
    ar_out = ar[~ar.paid]["amount"].sum()

    # Triple line chart
    fig_tri = make_subplots(specs=[[{"secondary_y":True}]])
    fig_tri.add_trace(go.Scatter(x=cb_base["week_label"], y=cb_base["avg_cash_collected"]/1e6,
                                 name="Cash Collected", line=dict(color=NAVY,width=2.5),
                                 mode="lines+markers", marker=dict(size=5,color=NAVY)), secondary_y=False)
    fig_tri.add_trace(go.Scatter(x=cb_base["week_label"], y=cb_base["avg_cash_burn"]/1e6,
                                 name="Cash Burn", line=dict(color=LBLUE,width=2),
                                 mode="lines+markers", marker=dict(size=5,color=LBLUE)), secondary_y=False)
    fig_tri.add_trace(go.Scatter(x=cb_base["week_label"], y=cb_base["running_balance"]/1e6,
                                 name="Running Balance", line=dict(color=AMBER,width=2.5),
                                 mode="lines+markers", marker=dict(size=5,color=AMBER)), secondary_y=True)
    fig_tri.update_layout(**bl(legend=dict(orientation="h",y=1.06), xaxis=dict(tickangle=-30,showgrid=False)))
    fig_tri.update_yaxes(tickprefix="$",ticksuffix="M",gridcolor=GRID,secondary_y=False,
                         rangemode="tozero")
    fig_tri.update_yaxes(tickprefix="$",ticksuffix="M",showgrid=False,secondary_y=True,
                         rangemode="tozero")

    # Weekly table
    th_style = {"padding":"6px 10px","fontSize":"10px","color":SLATE,"fontWeight":"700",
                "borderBottom":f"1px solid {GREY}","textTransform":"uppercase"}
    tbl = [html.Tr([html.Th(c,style=th_style) for c in ["Week","Collected","Burn","Balance"]])]
    for _,r in cb_base.iterrows():
        tbl.append(html.Tr([
            html.Td(r["week_label"], style={"padding":"5px 10px","fontSize":"11px","color":BLUE,"fontWeight":"600"}),
            html.Td(f"${r['avg_cash_collected']:,.0f}", style={"padding":"5px 10px","fontSize":"11px"}),
            html.Td(f"${r['avg_cash_burn']:,.0f}", style={"padding":"5px 10px","fontSize":"11px","color":AMBER}),
            html.Td(f"${r['running_balance']:,.0f}", style={"padding":"5px 10px","fontSize":"11px","fontWeight":"700","color":GREEN}),
        ]))
    net_cash = cb_base['avg_cash_collected'].sum() - cb_base['avg_cash_burn'].sum()
    tbl.append(html.Tr([
        html.Td("13-Wk Total",style={"padding":"5px 10px","fontSize":"11px","fontWeight":"700","borderTop":f"2px solid {GREY}"}),
        html.Td(f"${cb_base['avg_cash_collected'].sum():,.0f}",style={"padding":"5px 10px","fontSize":"11px","fontWeight":"700","color":NAVY,"borderTop":f"2px solid {GREY}"}),
        html.Td(f"${cb_base['avg_cash_burn'].sum():,.0f}",style={"padding":"5px 10px","fontSize":"11px","fontWeight":"700","color":AMBER,"borderTop":f"2px solid {GREY}"}),
        html.Td(f"${cb_base['running_balance'].iloc[-1]:,.0f} (Wk 13)",style={"padding":"5px 10px","fontSize":"11px","fontWeight":"700","color":GREEN,"borderTop":f"2px solid {GREY}"}),
    ]))
    tbl_card = html.Div([
        html.Div("13-Week Cash Flow Detail",style={"fontSize":"12px","fontWeight":"700","color":NAVY,"marginBottom":"10px"}),
        html.Div(html.Table(tbl,style={"width":"100%","borderCollapse":"collapse"}),style={"overflowX":"auto"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"18px 22px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.06)","border":f"1px solid {GREY}","flex":"1"})

    # Vendor payables
    ap_v = ap.groupby("vendor_id")["amount"].sum().sort_values(ascending=False).head(20)
    fig_ap = go.Figure(go.Bar(x=ap_v.index, y=ap_v.values/1e6,
                              marker_color=NAVY, opacity=0.85))
    fig_ap.update_layout(**bl(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M",
                               xaxis_title="Vendor"))

    return html.Div([
        header(5,"13-Week Cash Forecast",SUBTITLES["cfo5"]),
        body(
            row(kpi("Wk 13 Cash Balance",f"${week13_bal/1e6:.1f}M",GREEN),
                kpi("Weekly Burn Rate",f"${weekly_burn/1e3:.0f}K",AMBER),
                kpi("Cash Runway",f"{cash_runway} wks",GREEN),
                kpi("AR Outstanding",f"${ar_out/1e6:.2f}M",BLUE)),
            card("When does our cash balance hit the danger zone?", fig_tri, height=300),
            row(tbl_card, col(card("Where are near-term payables concentrated?",fig_ap))),
        ),
    ])

def cfo6():
    rev_m  = gl[gl.category=="Revenue"].groupby("period_start")["credit_amount"].sum().sort_index()
    cogs_m = gl[gl.category=="COGS"].groupby("period_start")["debit_amount"].sum().sort_index()
    opex_m = gl[gl.category=="OpEx"].groupby("period_start")["debit_amount"].sum().sort_index()
    gross_m_pct = ((rev_m-cogs_m)/rev_m*100)
    cb_base = cb[cb.scenario=="base"]
    week13_bal = cb_base["running_balance"].iloc[-1]
    base_cov = cov[cov.scenario=="base"].sort_values("period")
    dscr_now = base_cov["dscr_proxy"].iloc[-1]

    # 12m forecast
    fig_fc = go.Figure(go.Scatter(
        x=fcast["forecast_month"], y=fcast["revenue_forecast"]/1e6,
        fill="tozeroy", fillcolor="rgba(30,58,138,0.10)",
        line=dict(color=NAVY,width=2.5), mode="lines+markers",
        marker=dict(size=5,color=NAVY), name="Revenue Forecast",
    ))
    fig_fc.update_layout(**bl(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M",xaxis_title="Month"))

    # Historical revenue area
    fig_hist = go.Figure(go.Scatter(
        x=rev_m.index, y=rev_m.values/1e6,
        fill="tozeroy", fillcolor="rgba(68,114,196,0.12)",
        line=dict(color=LBLUE,width=2.5), mode="lines", name="Revenue",
    ))
    fig_hist.update_layout(**bl(showlegend=False, yaxis_tickprefix="$", yaxis_ticksuffix="M", xaxis_title="Month"))

    # YoY revenue vs opex
    rev_yoy  = rev_m.pct_change(12).dropna()*100
    opex_yoy = opex_m.pct_change(12).dropna()*100
    idx = rev_yoy.index.intersection(opex_yoy.index)
    fig_yoy = go.Figure([
        go.Bar(x=idx, y=rev_yoy[idx].values, name="Revenue YoY %", marker_color=NAVY, opacity=0.85),
        go.Bar(x=idx, y=opex_yoy[idx].values, name="OpEx YoY %",   marker_color=LBLUE, opacity=0.85),
    ])
    fig_yoy.add_hline(y=0, line_color=RED, line_width=1)
    fig_yoy.update_layout(**bl(barmode="group", yaxis_ticksuffix="%", xaxis_title="Month"))

    return html.Div([
        header(6,"Strategic Model",SUBTITLES["cfo6"]),
        body(
            row(kpi("Total Revenue",f"${rev_m.sum()/1e6:.1f}M",NAVY),
                kpi("DSCR Current",f"{dscr_now:.1f}x",GREEN if dscr_now>1.5 else (AMBER if dscr_now>0 else RED)),
                kpi("Avg Gross Margin",f"{gross_m_pct.mean():.1f}%",GREEN),
                kpi("Wk 13 Cash",f"${week13_bal/1e6:.1f}M",GREEN)),
            row(col(card("Where is revenue heading in the next 12 months?",fig_fc)),
                col(card("Is the business structurally healthy?",fig_hist))),
            card("Is revenue growing faster than costs? (YoY)",fig_yoy,height=270),
        ),
    ])

# ── DISPATCH ──────────────────────────────────────────────────────────────────
BUILDERS = {"cfo1":cfo1,"cfo2":cfo2,"cfo3":cfo3,"cfo4":cfo4,"cfo5":cfo5,"cfo6":cfo6}

def page_from_pathname(pathname):
    """Map URL pathname to page id."""
    if not pathname or pathname == "/":
        return "cfo1"
    # e.g. /cfo2 -> cfo2
    slug = pathname.strip("/")
    return slug if slug in BUILDERS else "cfo1"

# Nav clicks → update URL
@app.callback(Output("url","pathname"),
              [Input({"type":"nav","index":pid},"n_clicks") for pid,_ in PAGES],
              prevent_initial_call=True)
def navigate(*_):
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
        return "/" + ctx.triggered_id["index"]
    return "/cfo1"

# URL → sidebar + page content (single callback, no store needed)
@app.callback(
    Output("sidebar-container","children"),
    Output("page-content","children"),
    Input("url","pathname"),
)
def render_all(pathname):
    page = page_from_pathname(pathname)
    return sidebar(page), BUILDERS[page]()

if __name__ == "__main__":
    app.run(debug=True, port=8050)
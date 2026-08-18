"""
Macro Intelligence App — Plotly Dash
6 pages · real BoC / StatCan / FRED / TSX data · light theme
"""
import os
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, ctx

# ── DATA ──────────────────────────────────────────────────────────────────────
DATA     = os.path.join(os.path.dirname(__file__), "data")
CFO_DATA = os.path.join(os.path.dirname(__file__), "..", "dash_app", "data")

def load(name, folder=None):
    folder = folder or DATA
    return pd.read_parquet(os.path.join(folder, f"{name}.parquet"))

def safe_last(series, default=0):
    s = series.dropna()
    return s.iloc[-1] if len(s) else default

boc       = load("boc_rates");       boc["date"]   = pd.to_datetime(boc["date"])
fred      = load("fred_macro");      fred["date"]  = pd.to_datetime(fred["date"])
cpi       = load("statcan_cpi");     cpi["date"]   = pd.to_datetime(cpi["date"])
labour    = load("statcan_labour");  labour["date"]= pd.to_datetime(labour["date"])
wages     = load("statcan_wages");   wages["date"] = pd.to_datetime(wages["date"])
ippi      = load("statcan_ippi");    ippi["date"]  = pd.to_datetime(ippi["date"])
etfs      = load("tsx_etfs");        etfs["date"]  = pd.to_datetime(etfs["date"])
cust_sec  = load("synthetic_customers_sectors")
shap_df   = load("synthetic_shap")
headcount = load("synthetic_headcount"); headcount["date"] = pd.to_datetime(headcount["date"])
freight   = load("synthetic_freight");   freight["date"]   = pd.to_datetime(freight["date"])

# Fix HY spread units — FRED BAMLH0A0HYM2 is in percent (e.g. 2.67 = 267bps)
fred["hy_spread_bps"] = fred["hy_spread_oas"] * 100 if "hy_spread_oas" in fred.columns else 267.0

# Fix copper units — PCOPPUSDM is USD per metric ton, convert to USD/lb
# 1 metric ton = 2204.6 lbs
if "copper_usd" in fred.columns:
    max_val = fred["copper_usd"].dropna().max()
    if max_val > 1000:  # USD/MT → USD/lb
        fred["copper_usd"] = fred["copper_usd"] / 2204.6
    elif max_val > 20:  # cents/lb → USD/lb
        fred["copper_usd"] = fred["copper_usd"] / 100

# Add gscpi column with fallback if missing
if "gscpi" not in fred.columns:
    fred["gscpi"] = 0.2

# ETF sector columns — flatten if multi-level
ETF_SECTORS = ["Financials","Technology","Energy","Consumer Staples","Utilities","Real Estate","TSX 60"]
etf_cols_available = [c for c in ETF_SECTORS if c in etfs.columns]

# Try loading CFO GL data for revenue per employee
try:
    gl = load("gl", folder=CFO_DATA)
    gl["period_start"] = pd.to_datetime(gl["period_start"])
    HAS_GL = True
except Exception:
    HAS_GL = False

# ── DESIGN TOKENS ─────────────────────────────────────────────────────────────
BG    = "#F8FAFC"; CARD  = "#FFFFFF"; GREY  = "#E2E8F0"; GRID  = "#F1F5F9"
NAVY  = "#1E3A8A"; BLUE  = "#2563EB"; LBLUE = "#4472C4"; NAVY2 = "#3B5BA5"
SLATE = "#64748B"; DARK  = "#0F172A"
GREEN = "#059669"; AMBER = "#D97706"; RED   = "#DC2626"

PAGES = [
    ("macro1","Macro Context"),("macro2","Yield Curve"),("macro3","Sector & AR Risk"),
    ("macro4","Supply Chain"),("macro5","Labour Economics"),("macro6","Scenario Analysis"),
]
SUBTITLES = {
    "macro1":"What is the external environment doing to our business?",
    "macro2":"What is our cost of capital doing?",
    "macro3":"Which customers are in distressed sectors?",
    "macro4":"Are our input costs about to spike?",
    "macro5":"Can we afford to hire and what will it cost?",
    "macro6":"What does the model say happens next?",
}
ICONS = {"macro1":"🌐","macro2":"📉","macro3":"🔄","macro4":"🏭","macro5":"👷","macro6":"🔮"}

# ── APP ───────────────────────────────────────────────────────────────────────
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ── HELPERS ───────────────────────────────────────────────────────────────────
def kpi(label, value, color=NAVY):
    return html.Div([
        html.Div(value, style={"fontSize":"26px","fontWeight":"800","color":color,
                               "marginBottom":"4px","letterSpacing":"-0.5px"}),
        html.Div(label, style={"fontSize":"10px","fontWeight":"700","color":SLATE,
                               "letterSpacing":"0.09em","textTransform":"uppercase"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"18px 22px","flex":"1",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.06)","border":f"1px solid {GREY}"})

def card(title, fig, height=320, question=None):
    header_els = [
        html.Div(title, style={"fontSize":"12px","fontWeight":"700","color":NAVY,"marginBottom":"2px"}),
    ]
    if question:
        header_els.append(
            html.Div(f"❓ {question}", style={"fontSize":"10px","color":SLATE,
                                               "fontStyle":"italic","marginBottom":"8px"})
        )
    else:
        header_els[0] = html.Div(title, style={"fontSize":"12px","fontWeight":"700",
                                                "color":NAVY,"marginBottom":"10px"})
    return html.Div(header_els + [
        dcc.Graph(figure=fig, config={"displayModeBar":False}, style={"height":f"{height}px"}),
    ], style={"background":CARD,"borderRadius":"10px","padding":"18px 22px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.06)","border":f"1px solid {GREY}"})

def bl(**kw):
    d = dict(paper_bgcolor=CARD, plot_bgcolor=CARD,
             font=dict(family="Inter,system-ui,sans-serif", size=11, color=DARK),
             margin=dict(l=8,r=8,t=8,b=8),
             xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10), color=SLATE),
             yaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(size=10), color=SLATE),
             legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="left",x=0,
                         font=dict(size=10)),
             hovermode="x unified")
    d.update(kw)
    return d

def row(*items): return html.Div(list(items), style={"display":"flex","gap":"16px"})
def col(content, flex="1"): return html.Div(content, style={"flex":flex})

def sidebar(active):
    links = []
    for pid, label in PAGES:
        is_active = pid == active
        links.append(html.Div(
            [html.Span(ICONS[pid], style={"marginRight":"8px","fontSize":"13px"}),
             html.Span(label)],
            id={"type":"nav","index":pid}, n_clicks=0,
            style={
                "display":"flex","alignItems":"center",
                "padding":"9px 14px","cursor":"pointer","borderRadius":"7px",
                "fontSize":"12px","fontWeight":"600" if is_active else "400",
                "color":BLUE if is_active else SLATE,
                "background":"#EFF6FF" if is_active else "transparent",
                "borderLeft":f"3px solid {BLUE}" if is_active else "3px solid transparent",
                "marginBottom":"2px",
            }
        ))
    return html.Div([
        html.Div([
            html.Div("MACRO", style={"fontSize":"15px","fontWeight":"900","color":NAVY,"letterSpacing":"0.06em"}),
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
        html.Div(f"MACRO {num}", style={"fontSize":"10px","color":BLUE,"fontWeight":"700",
                                        "letterSpacing":"0.1em","marginBottom":"3px"}),
        html.Div([
            html.Span(title, style={"fontSize":"20px","fontWeight":"800","color":DARK}),
            html.Span(sub, style={"fontSize":"11px","color":SLATE,"fontStyle":"italic","marginLeft":"auto"}),
        ], style={"display":"flex","alignItems":"baseline","gap":"12px","justifyContent":"space-between"}),
    ], style={"padding":"20px 28px 14px","borderBottom":f"1px solid {GREY}","background":CARD})

def body(*rows_):
    return html.Div(list(rows_), style={"padding":"18px 28px","display":"flex",
                                        "flexDirection":"column","gap":"14px"})

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        html.Div(id="sidebar-container"),
        html.Div(id="page-content", style={"flex":"1","overflowY":"auto","background":BG}),
    ], style={"display":"flex","height":"100vh","fontFamily":"Inter,system-ui,sans-serif"}),
], style={"margin":"0","padding":"0"})

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — MACROECONOMIC CONTEXT
# ═══════════════════════════════════════════════════════════════════════════════
def macro1():
    boc_rate  = safe_last(boc["overnight_rate"])
    cad_usd   = safe_last(boc["cad_usd"])
    cpi_all   = cpi[cpi["component"]=="All-items"].sort_values("date")
    cpi_yoy   = cpi_all["value"].pct_change(12).dropna().iloc[-1]*100 if len(cpi_all)>12 else 3.0
    unemp_df  = labour[labour["metric"]=="Unemployment rate"].sort_values("date")
    unemp_now = safe_last(unemp_df["value"], 6.4)

    # Chart 1: BoC Rate vs CPI YoY
    boc_m = boc.set_index("date")["overnight_rate"].resample("MS").last().dropna().reset_index()
    cpi_m = cpi_all.set_index("date")["value"].resample("MS").last().dropna()
    cpi_yoy_s = (cpi_m.pct_change(12)*100).dropna()

    fig1 = make_subplots(specs=[[{"secondary_y":True}]])
    fig1.add_trace(go.Scatter(x=boc_m["date"], y=boc_m["overnight_rate"],
                              name="BoC Overnight Rate", line=dict(color=NAVY,width=2.5),
                              mode="lines"), secondary_y=False)
    fig1.add_trace(go.Scatter(x=cpi_yoy_s.index, y=cpi_yoy_s.values,
                              name="CPI YoY %", line=dict(color=AMBER,width=2,dash="dot"),
                              mode="lines"), secondary_y=True)
    fig1.add_hline(y=2, line_color=GREEN, line_dash="dash", line_width=1,
                   annotation_text="2% target", secondary_y=True,
                   annotation_font_color=GREEN, annotation_font_size=9)
    fig1.update_layout(**bl(legend=dict(orientation="h",y=1.06)))
    fig1.update_yaxes(ticksuffix="%", gridcolor=GRID, secondary_y=False, title_text="Policy Rate")
    fig1.update_yaxes(ticksuffix="%", showgrid=False, secondary_y=True, title_text="CPI YoY")

    # Chart 2: Unemployment trend — fix Y-axis range
    fig2 = go.Figure(go.Scatter(
        x=unemp_df["date"], y=unemp_df["value"],
        fill="tozeroy", fillcolor="rgba(30,58,138,0.10)",
        line=dict(color=NAVY,width=2.5), mode="lines", name="Unemployment %",
    ))
    fig2.add_hline(y=5.5, line_color=GREEN, line_dash="dash", line_width=1,
                   annotation_text="Full employment proxy",
                   annotation_font_color=GREEN, annotation_font_size=9)
    unemp_min = max(0, unemp_df["value"].min() - 1)
    unemp_max = unemp_df["value"].max() + 1
    fig2.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                             yaxis=dict(range=[unemp_min, unemp_max], gridcolor=GRID,
                                        ticksuffix="%", tickfont=dict(size=10))))

    # Chart 3: CPI breakdown — use actual component values relative to All-items
    latest_month = cpi["date"].max()
    cpi_latest   = cpi[cpi["date"]==latest_month].set_index("component")["value"]
    all_items_val = cpi_latest.get("All-items", None)

    # Use absolute index values for components that exist
    comp_order = ["Food","Shelter","Transportation","Health and personal care",
                  "Recreation, education and reading","Clothing and footwear",
                  "Household operations, furnishings and equipment"]
    comp_vals, comp_labels = [], []
    for c in comp_order:
        if c in cpi_latest.index and all_items_val is not None:
            comp_vals.append(round(float(cpi_latest[c]) - float(all_items_val), 1))
            comp_labels.append(c.replace(", furnishings and equipment","").replace("Recreation, education and reading","Recreation"))

    if not comp_vals:
        comp_labels = ["No component data"]
        comp_vals   = [0]

    fig3 = go.Figure(go.Bar(
        x=comp_labels, y=comp_vals,
        marker_color=[NAVY if v >= 0 else RED for v in comp_vals],
        text=[f"{v:+.1f}" for v in comp_vals], textposition="outside",
    ))
    fig3.update_layout(**bl(showlegend=False,
                             yaxis_title="Index Points vs All-items",
                             xaxis_tickangle=-20))

    return html.Div([
        header(1,"Macroeconomic Context",SUBTITLES["macro1"]),
        body(
            row(kpi("BoC Policy Rate", f"{boc_rate:.2f}%",
                    GREEN if boc_rate<3 else (AMBER if boc_rate<4.5 else RED)),
                kpi("CPI YoY", f"{cpi_yoy:.1f}%",
                    GREEN if cpi_yoy<2.5 else (AMBER if cpi_yoy<4 else RED)),
                kpi("Unemployment", f"{unemp_now:.1f}%",
                    GREEN if unemp_now<6 else (AMBER if unemp_now<7 else RED)),
                kpi("CAD / USD", f"{cad_usd:.4f}",
                    AMBER if cad_usd>1.35 else GREEN)),
            row(col(card("BoC Rate vs. CPI Trajectory", fig1, question="Is the central bank winning the inflation battle — and will rates keep falling?")),
                col(card("Unemployment Rate Trend", fig2, question="Is the labour market tightening in ways that could drive wage inflation?"))),
            card("CPI Component Breakdown vs. All-items (latest month)", fig3, height=380, question="Which specific cost categories are squeezing our customers' purchasing power?"),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — YIELD CURVE & CREDIT MARKETS
# ═══════════════════════════════════════════════════════════════════════════════
def macro2():
    spread_now  = safe_last(boc["spread_2y10y"])
    hy_bps      = safe_last(fred["hy_spread_bps"])  # already *100
    overnight   = safe_last(boc["overnight_rate"])
    cod_variance= round((overnight + 2.1) - (overnight + 1.85), 2)

    # Chart 1: Yield curve — FIXED: use actual tenor points, not time series
    boc_sorted = boc.sort_values("date")
    tenors      = ["2Y","5Y","10Y"]
    tenor_cols  = ["yield_2y","yield_5y","yield_10y"]

    def get_yields_at(df, target_date):
        row_ = df[df["date"] <= target_date].tail(1)
        if len(row_) == 0:
            return [np.nan]*3
        return [safe_last(row_[c]) for c in tenor_cols]

    today = boc_sorted["date"].iloc[-1]
    d90   = today - pd.Timedelta(days=90)
    d365  = today - pd.Timedelta(days=365)

    fig1 = go.Figure()
    for label, dt, color, dash in [
        ("Today",    today, NAVY,  "solid"),
        ("90d ago",  d90,   BLUE,  "dot"),
        ("365d ago", d365,  LBLUE, "dash"),
    ]:
        vals = get_yields_at(boc_sorted, dt)
        fig1.add_trace(go.Scatter(
            x=tenors, y=vals, name=label,
            line=dict(color=color, width=2.5, dash=dash),
            mode="lines+markers", marker=dict(size=8),
        ))
    # Remove zero line — set y-axis to start near actual yield range
    all_vals = [v for _,dt,_,_ in [("Today",today,NAVY,"solid"),("90d",d90,BLUE,"dot"),("365d",d365,LBLUE,"dash")]
                for v in get_yields_at(boc_sorted, dt) if not np.isnan(v)]
    y_min = max(0, min(all_vals) - 0.3) if all_vals else 0
    y_max = max(all_vals) + 0.3 if all_vals else 5
    fig1.update_layout(**bl(yaxis_ticksuffix="%", yaxis_title="Yield %",
                             xaxis_title="Tenor",
                             xaxis=dict(showgrid=False, zeroline=False,
                                        tickfont=dict(size=12), color=SLATE),
                             yaxis=dict(range=[y_min, y_max], gridcolor=GRID,
                                        ticksuffix="%", tickfont=dict(size=10))))

    # Chart 2: 2Y/10Y spread over time
    boc_w = boc.set_index("date")["spread_2y10y"].resample("W").last().dropna().reset_index()
    fig2 = go.Figure(go.Scatter(
        x=boc_w["date"], y=boc_w["spread_2y10y"],
        fill="tozeroy", fillcolor="rgba(30,58,138,0.10)",
        line=dict(color=NAVY,width=2.5), mode="lines",
    ))
    fig2.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5,
                   annotation_text="Inversion threshold",
                   annotation_font_color=RED, annotation_font_size=9)
    fig2.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                             yaxis_title="Spread (10Y − 2Y)"))

    # Chart 3: HY Spread in bps — FIXED units
    fred_w = fred.set_index("date")["hy_spread_bps"].resample("W").last().dropna().reset_index()
    fig3 = go.Figure(go.Scatter(
        x=fred_w["date"], y=fred_w["hy_spread_bps"],
        fill="tozeroy", fillcolor="rgba(217,119,6,0.10)",
        line=dict(color=AMBER,width=2.5), mode="lines", name="HY OAS",
    ))
    fig3.add_hline(y=400, line_color=RED, line_dash="dash", line_width=1,
                   annotation_text="400bps stress threshold",
                   annotation_font_color=RED, annotation_font_size=9)
    fig3.update_layout(**bl(showlegend=False, yaxis_title="Basis Points (bps)"))

    return html.Div([
        header(2,"Yield Curve & Credit Markets",SUBTITLES["macro2"]),
        body(
            row(kpi("2Y / 10Y Spread", f"{spread_now:+.2f}%",
                    GREEN if spread_now>0 else RED),
                kpi("HY OAS Spread", f"{hy_bps:.0f} bps",
                    GREEN if hy_bps<300 else (AMBER if hy_bps<400 else RED)),
                kpi("BoC Overnight", f"{overnight:.2f}%",
                    GREEN if overnight<3 else AMBER),
                kpi("Cost of Debt Variance", f"{cod_variance:+.2f}%",
                    GREEN if cod_variance<0 else AMBER)),
            card("Dynamic Yield Curve — Today vs. 90d vs. 365d ago", fig1, height=300, question="Is the yield curve steepening or inverting — and what does that mean for our cost of debt?"),
            row(col(card("2Y/10Y Yield Spread — Recession Signal", fig2, question="Are bond markets pricing in a recession within the next 12 months?")),
                col(card("High Yield Corporate Bond Spread (OAS)", fig3, question="Is credit tightening in ways that will make refinancing harder or more expensive?"))),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — SECTOR ROTATION & AR RISK
# ═══════════════════════════════════════════════════════════════════════════════
def macro3():
    # Momentum using available ETF columns
    sector_cols = [c for c in ETF_SECTORS if c in etfs.columns and c != "TSX 60"]
    etf_sorted  = etfs.sort_values("date")

    momentum = {}
    for sec in sector_cols:
        s = etf_sorted[sec].dropna()
        if len(s) >= 60:
            momentum[sec] = round((s.iloc[-1]/s.iloc[-60]-1)*100, 1)
        elif len(s) >= 2:
            momentum[sec] = round((s.iloc[-1]/s.iloc[0]-1)*100, 1)
        else:
            momentum[sec] = 0.0

    distressed = [s for s,v in momentum.items() if v < -0.5]

    sec_exposure = cust_sec.groupby("sector").agg(
        n_customers=("customer_id","count"),
        avg_default_prob=("default_prob_60d","mean"),
    ).reset_index()

    distressed_ar_val = sec_exposure[sec_exposure["sector"].isin(distressed)]["avg_default_prob"].mean() if distressed else None

    # Volatility
    vol_cols = [f"{c}_vol30d" for c in sector_cols if f"{c}_vol30d" in etfs.columns]
    tsx_vol  = etfs[vol_cols].iloc[-1].mean() if vol_cols else 18.5

    # Chart 1: Sector momentum
    sec_names = list(momentum.keys())
    sec_vals  = list(momentum.values())
    fig1 = go.Figure(go.Bar(
        x=sec_names, y=sec_vals,
        marker_color=[GREEN if v>=0 else RED for v in sec_vals],
        text=[f"{v:+.1f}%" for v in sec_vals], textposition="outside",
    ))
    fig1.add_hline(y=0, line_color=DARK, line_width=1)
    fig1.add_hline(y=-0.5, line_color=RED, line_dash="dot", line_width=1,
                   annotation_text="Distress threshold (−0.5%)",
                   annotation_font_color=RED, annotation_font_size=9)
    fig1.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                             yaxis_title="12-Week Return", xaxis_tickangle=-20))

    # Chart 2: Default prob by sector
    sec_sorted = sec_exposure.sort_values("avg_default_prob", ascending=False)
    fig2 = go.Figure(go.Bar(
        x=sec_sorted["sector"], y=sec_sorted["avg_default_prob"]*100,
        marker_color=[RED if v>10 else (AMBER if v>6 else NAVY)
                      for v in sec_sorted["avg_default_prob"]*100],
        text=[f"{v*100:.1f}%" for v in sec_sorted["avg_default_prob"]],
        textposition="outside",
    ))
    fig2.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                             yaxis_title="60-Day Default Probability",
                             xaxis_tickangle=-20))

    # Chart 3: SHAP — green for positive, red for negative drivers
    shap_s = shap_df.sort_values("mean_shap_value", ascending=True)
    shap_colors = [RED if d=="negative" else GREEN for d in shap_s["direction"]]
    fig3 = go.Figure(go.Bar(
        x=shap_s["mean_shap_value"], y=shap_s["feature"],
        orientation="h",
        marker_color=shap_colors,
        text=[f"{v:.2f}" for v in shap_s["mean_shap_value"]],
        textposition="outside",
    ))
    fig3.update_layout(**bl(showlegend=False, xaxis_title="Mean |SHAP| Value"))

    # Chart 4: ETF lines indexed
    fig4 = go.Figure()
    colors_ = [NAVY, BLUE, LBLUE, AMBER, GREEN, RED]
    for i, sec in enumerate(sector_cols):
        if sec in etfs.columns:
            s = etf_sorted[["date",sec]].dropna()
            base = s[sec].iloc[0]
            fig4.add_trace(go.Scatter(
                x=s["date"], y=s[sec]/base*100,
                name=sec, line=dict(color=colors_[i%len(colors_)],width=1.8),
                mode="lines",
            ))
    fig4.update_layout(**bl(yaxis_title="Indexed (base=100)"))

    dist_str  = f"{distressed_ar_val*100:.1f}%" if distressed_ar_val is not None else "N/A"
    dist_color= RED if distressed_ar_val and distressed_ar_val>0.08 else (AMBER if distressed_ar_val else GREEN)

    return html.Div([
        header(3,"Sector Rotation & AR Risk",SUBTITLES["macro3"]),
        body(
            row(kpi("Sector Avg Volatility (30d)", f"{tsx_vol:.1f}%", AMBER),
                kpi("Distressed Sectors (<−3%)", f"{len(distressed)}", RED if distressed else GREEN),
                kpi("Avg Default Prob (Distressed)", dist_str, dist_color),
                kpi("Customers Tracked", f"{len(cust_sec)}", NAVY)),
            row(col(card("TSX Sector 12-Week Momentum", fig1, height=400, question="Which of our customer industries are under institutional selling pressure right now?")),
                col(card("60-Day Customer Default Probability by Sector", fig2, height=400, question="Which sectors pose the greatest near-term AR collection risk to our business?"))),
            row(col(card("Top Default Risk Drivers — SHAP Analysis", fig3, question="What macro factors are most responsible for driving our customers toward default?")),
                col(card("TSX Sector ETF Performance (Indexed, Jan 2022=100)", fig4, question="Which sectors have structurally outperformed or underperformed since 2022?"))),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — SUPPLY CHAIN & INPUT COSTS
# ═══════════════════════════════════════════════════════════════════════════════
def macro4():
    wti_s_all  = fred["wti_oil"].dropna() if "wti_oil" in fred.columns else pd.Series([85.0])
    wti_now    = safe_last(wti_s_all, 85.0)
    wti_mom    = round((wti_now / wti_s_all.iloc[-2] - 1)*100, 1) if len(wti_s_all)>1 else 0.0
    copper_now = safe_last(fred["copper_usd"] if "copper_usd" in fred.columns else pd.Series([4.2]),  4.2)
    freight_now= safe_last(freight["freight_premium"], 0.1)

    # Chart 1: Commodity tracker
    fig1 = go.Figure()
    for col_, name_, color_ in [("wti_oil","WTI Crude Oil",NAVY),
                                  ("copper_usd","Copper (USD/lb)",BLUE)]:
        if col_ not in fred.columns:
            continue
        s = fred[["date",col_]].dropna().sort_values("date")
        if len(s) < 2:
            continue
        base = s[col_].iloc[0]
        if base == 0:
            continue
        fig1.add_trace(go.Scatter(
            x=s["date"], y=s[col_]/base*100,
            name=name_, line=dict(color=color_,width=2.5), mode="lines",
        ))
    fig1.update_layout(**bl(yaxis_title="Indexed (start = 100)"))

    # Chart 2: CAD/USD + BoC Rate — currency & rate story
    fig2 = make_subplots(specs=[[{"secondary_y":True}]])
    boc_d = boc[["date","cad_usd","overnight_rate"]].dropna().sort_values("date")
    fig2.add_trace(go.Scatter(
        x=boc_d["date"], y=boc_d["cad_usd"],
        name="CAD/USD", line=dict(color=NAVY,width=2.5), mode="lines",
    ), secondary_y=False)
    fig2.add_trace(go.Scatter(
        x=boc_d["date"], y=boc_d["overnight_rate"],
        name="BoC Rate %", line=dict(color=AMBER,width=2,dash="dot"), mode="lines",
    ), secondary_y=True)
    fig2.add_hline(y=0.72, line_color=RED, line_dash="dash", line_width=1,
                   annotation_text="CAD weakness threshold",
                   annotation_font_color=RED, annotation_font_size=9, secondary_y=False)
    fig2.update_layout(**bl(legend=dict(orientation="h",y=1.06)))
    fig2.update_yaxes(title_text="CAD / USD", gridcolor=GRID, secondary_y=False)
    fig2.update_yaxes(ticksuffix="%", title_text="BoC Rate", showgrid=False, secondary_y=True)

    # Chart 3: IPPI — find whatever product column is named
    prod_col = "product" if "product" in ippi.columns else ippi.columns[1]
    ippi_products = ippi[prod_col].unique()
    # Pick total/all-industry row
    total_kw = ["Total","total","All","all"]
    total_prod = next((p for p in ippi_products if any(kw in str(p) for kw in total_kw)), ippi_products[0])
    ippi_total = ippi[ippi[prod_col]==total_prod].sort_values("date")
    # Use 6-month change if fewer than 13 months of data
    n_months = len(ippi_total)
    lookback = 12 if n_months >= 13 else max(1, n_months-1)
    ippi_yoy = ippi_total.set_index("date")["value"].pct_change(lookback).dropna()*100

    fig3 = go.Figure(go.Scatter(
        x=ippi_yoy.index, y=ippi_yoy.values,
        fill="tozeroy", fillcolor="rgba(217,119,6,0.10)",
        line=dict(color=AMBER,width=2.5), mode="lines",
    ))
    fig3.add_hline(y=0, line_color=SLATE, line_width=1)
    fig3.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                             yaxis_title="IPPI YoY %"))

    # Chart 4: Freight premium
    fig4 = go.Figure(go.Bar(
        x=freight["date"], y=freight["freight_premium"],
        marker_color=[RED if v>0 else GREEN for v in freight["freight_premium"]],
    ))
    fig4.add_hline(y=0, line_color=DARK, line_width=1)
    fig4.update_layout(**bl(showlegend=False, yaxis_title="Premium vs Historical Avg"))

    return html.Div([
        header(4,"Supply Chain & Input Costs",SUBTITLES["macro4"]),
        body(
            row(kpi("WTI Crude Oil",  f"${wti_now:.0f}/bbl",
                    AMBER if wti_now>80 else GREEN),
                kpi("Copper Price",   f"${copper_now:.2f}/lb",
                    AMBER if copper_now>4 else GREEN),
                kpi("WTI Oil MoM Change", f"{wti_mom:+.1f}%",
                    RED if wti_now>90 else (AMBER if wti_now>75 else GREEN)),
                kpi("Freight Premium",f"{freight_now:+.2f}x",
                    RED if freight_now>0.2 else (AMBER if freight_now>0 else GREEN))),
            row(col(card("Commodity Price Tracker (Indexed)", fig1, question="Are our key input costs trending up — and how fast should we expect COGS to rise?")),
                col(card("CAD/USD vs. BoC Policy Rate", fig2, question="Is currency weakness amplifying our import costs — and will rate cuts weaken CAD further?"))),
            row(col(card("Industrial Product Price Index YoY — StatCan", fig3, question="Are Canadian producers raising prices in ways that will compress our gross margin?")),
                col(card("Inbound Freight Cost Premium", fig4, question="Are we paying above-market rates for inbound shipping — and is it getting worse?"))),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — LABOUR ECONOMICS
# ═══════════════════════════════════════════════════════════════════════════════
def macro5():
    wage_yoy     = safe_last(wages["wage_yoy"], 3.4)
    particip_df  = labour[labour["metric"]=="Participation rate"].sort_values("date")
    particip_now = safe_last(particip_df["value"], 65.1)
    headcount_now= safe_last(headcount["headcount"], 200)

    if HAS_GL:
        annual_rev  = gl[gl["category"]=="Revenue"]["credit_amount"].sum() / 2.3
        rev_per_emp = annual_rev / max(headcount_now, 1)
    else:
        rev_per_emp = 165_000  # $33M rev / 200 employees

    # Chart 1: Wage growth YoY — fix Y axis range
    wages_s = wages.sort_values("date")
    fig1 = go.Figure(go.Scatter(
        x=wages_s["date"], y=wages_s["wage_yoy"],
        fill="tozeroy", fillcolor="rgba(30,58,138,0.10)",
        line=dict(color=NAVY,width=2.5), mode="lines+markers",
        marker=dict(size=4,color=NAVY),
    ))
    fig1.add_hline(y=2.0, line_color=GREEN, line_dash="dash", line_width=1,
                   annotation_text="2% pre-pandemic norm",
                   annotation_font_color=GREEN, annotation_font_size=9)
    fig1.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                            yaxis_title="Average Wage Growth YoY",
                            xaxis_range=["2022-01-01", None]))

    # Chart 2: Labour participation — fix Y axis to 60–70% range
    fig2 = go.Figure(go.Scatter(
        x=particip_df["date"], y=particip_df["value"],
        fill="tozeroy", fillcolor="rgba(68,114,196,0.10)",
        line=dict(color=LBLUE,width=2.5), mode="lines",
    ))
    p_min = max(55, particip_df["value"].min() - 1)
    p_max = min(75, particip_df["value"].max() + 1)
    fig2.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                             yaxis_title="Labour Force Participation %",
                             yaxis=dict(range=[p_min, p_max], gridcolor=GRID,
                                        ticksuffix="%", tickfont=dict(size=10))))

    # Chart 3: Headcount
    fig3 = go.Figure(go.Bar(
        x=headcount["date"], y=headcount["headcount"],
        marker_color=NAVY, opacity=0.85,
    ))
    fig3.update_layout(**bl(showlegend=False, yaxis_title="Headcount",
                             yaxis=dict(range=[headcount["headcount"].min()-10,
                                               headcount["headcount"].max()+10],
                                        gridcolor=GRID, tickfont=dict(size=10))))

    # Chart 4: Salary trend
    fig4 = go.Figure(go.Scatter(
        x=headcount["date"], y=headcount["avg_salary"]/1000,
        fill="tozeroy", fillcolor="rgba(30,58,138,0.08)",
        line=dict(color=NAVY,width=2.5), mode="lines",
    ))
    sal_min = headcount["avg_salary"].min()/1000 * 0.95
    sal_max = headcount["avg_salary"].max()/1000 * 1.05
    fig4.update_layout(**bl(showlegend=False, yaxis_tickprefix="$",
                             yaxis_ticksuffix="K", yaxis_title="Avg Annual Salary",
                             yaxis=dict(range=[sal_min, sal_max], gridcolor=GRID,
                                        tickprefix="$", ticksuffix="K", tickfont=dict(size=10))))

    return html.Div([
        header(5,"Labour Economics & Operating Leverage",SUBTITLES["macro5"]),
        body(
            row(kpi("Avg Wage Growth YoY",   f"{wage_yoy:.1f}%",
                    AMBER if wage_yoy>4 else GREEN),
                kpi("Labour Participation",  f"{particip_now:.1f}%",
                    GREEN if particip_now>65 else AMBER),
                kpi("Current Headcount",     f"{int(headcount_now)}", NAVY),
                kpi("Revenue per Employee",  f"${rev_per_emp/1e3:.0f}K", GREEN)),
            row(col(card("Average Wage Growth YoY — StatCan", fig1, question="Are external wage pressures building that will force us to raise salaries to stay competitive?")),
                col(card("Labour Force Participation Rate — StatCan", fig2, question="Is the talent pool shrinking — making hiring harder and more expensive?"))),
            row(col(card("Internal Headcount Trend", fig3, question="Are we growing headcount in line with revenue, or is our cost base expanding faster?")),
                col(card("Average Annual Salary Trend", fig4, question="How fast is our average compensation cost rising — and is it sustainable?"))),
        ),
    ])

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — PREDICTIVE SYNTHESIS & SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════
def macro6():
    np.random.seed(42)
    N_SIMS, N_WEEKS = 1000, 13
    starting_cash = 3_500_000
    boc_rate_now  = safe_last(boc["overnight_rate"], 2.26)
    gscpi_now     = safe_last(fred["gscpi"], 0.2)

    trajectories = []
    for _ in range(N_SIMS):
        boc_shock  = np.random.normal(0, 0.5)          # wider rate uncertainty
        gdp_shock  = np.random.normal(0, 0.8)          # GDP uncertainty
        coll_rate  = np.random.beta(18, 1) * 0.954     # slightly wider collection variance
        bal = starting_cash
        traj = [bal]
        for wk in range(N_WEEKS):
            # Weekly noise + macro sensitivity
            collected = np.random.normal(614_000, 45_000) * coll_rate * (1 + gdp_shock*0.005)
            burn      = np.random.normal(553_000, 40_000) * (1 + boc_shock*0.025)
            bal      += collected - burn
            traj.append(bal)
        trajectories.append(traj)

    traj_arr = np.array(trajectories)
    weeks = list(range(N_WEEKS+1))
    p10 = np.percentile(traj_arr, 10, axis=0)/1e6
    p50 = np.percentile(traj_arr, 50, axis=0)/1e6
    p90 = np.percentile(traj_arr, 90, axis=0)/1e6

    cfar         = (p50[-1] - p10[-1])*1e6
    breach_prob  = (traj_arr[:,-1] < 500_000).mean()*100
    macro_beta   = round(0.4*boc_rate_now + 0.3*abs(gscpi_now) + 0.3*0.046*10, 2)

    # Chart 1: Fan chart
    fig1 = go.Figure([
        go.Scatter(x=weeks, y=p90, fill=None,
                   line=dict(color="rgba(68,114,196,0)"), showlegend=False, name="P90"),
        go.Scatter(x=weeks, y=p10, fill="tonexty",
                   fillcolor="rgba(68,114,196,0.15)",
                   line=dict(color="rgba(68,114,196,0)"), name="P10–P90 Band"),
        go.Scatter(x=weeks, y=p50, name="P50 Median",
                   line=dict(color=NAVY,width=2.5), mode="lines+markers",
                   marker=dict(size=5,color=NAVY)),
    ])
    fig1.add_hline(y=0.5, line_color=RED, line_dash="dash", line_width=1.5,
                   annotation_text="Cash floor ($500K)",
                   annotation_font_color=RED, annotation_font_size=9)
    fig1.update_layout(**bl(yaxis_tickprefix="$",yaxis_ticksuffix="M",
                             xaxis_title="Forecast Week",
                             yaxis=dict(range=[0, max(p90)*1.15], gridcolor=GRID,
                                        tickprefix="$", ticksuffix="M", tickfont=dict(size=10))))

    # Chart 2: EBITDA stress test
    scenarios  = ["Soft Landing","Stagflation","Rate Shock","Recession"]
    # Each scenario: (boc_rate, gdp_growth, rev_impact, cost_impact)
    # EBITDA = base + revenue_effect - cost_effect
    ebitda_base = 0.024
    scenario_impacts = [
        (0.005,  0.003),   # Soft Landing: +rev, -cost
        (-0.004, -0.004),  # Stagflation: -rev (demand), -margin (input costs)
        (-0.005, -0.003),  # Rate Shock: -rev, higher interest burden
        (-0.010, -0.005),  # Recession: worst — demand collapse + cost stickiness
    ]
    ebitda_sc = [round((ebitda_base + r + c)*100, 2) for r,c in scenario_impacts]
    fig2 = go.Figure(go.Bar(
        x=scenarios, y=ebitda_sc,
        marker_color=[GREEN if v>2 else (AMBER if v>0 else RED) for v in ebitda_sc],
        text=[f"{v:.2f}%" for v in ebitda_sc], textposition="outside",
    ))
    fig2.add_hline(y=0, line_color=RED, line_width=1)
    fig2.update_layout(**bl(showlegend=False, yaxis_ticksuffix="%",
                             yaxis_title="Projected EBITDA Margin %"))

    # Prescriptive actions — FIXED: no walrus operator
    hy_val   = safe_last(fred["hy_spread_bps"] if "hy_spread_bps" in fred.columns else pd.Series([267.0]), 267.0)
    cad_val  = safe_last(boc["cad_usd"], 1.36)
    actions  = []
    if hy_val > 250:
        actions.append({"Signal":"HY Spread > 350bps","Action":"Delay discretionary capex; preserve liquidity","Priority":"🔴 High"})
    if boc_rate_now < 3.0:
        actions.append({"Signal":"BoC Rate declining","Action":"Review floating-rate debt for refinancing opportunity","Priority":"🟢 Low"})
    if gscpi_now > 1.0:
        actions.append({"Signal":"GSCPI elevated","Action":"Accelerate strategic inventory build","Priority":"🟡 Medium"})
    if cad_val > 1.35:
        actions.append({"Signal":"CAD/USD > 1.35","Action":"Hedge USD-denominated input cost exposure","Priority":"🟡 Medium"})
    if not actions:
        actions.append({"Signal":"All clear","Action":"No macro alerts triggered — maintain current posture","Priority":"🟢 Low"})

    action_df = pd.DataFrame(actions)
    th = {"padding":"8px 12px","fontSize":"10px","color":SLATE,"fontWeight":"700",
          "borderBottom":f"2px solid {GREY}","textTransform":"uppercase","background":BG}
    td_s = {"padding":"7px 12px","fontSize":"11px","borderBottom":f"1px solid {GREY}"}
    tbl = html.Table([
        html.Thead(html.Tr([html.Th(c, style=th) for c in action_df.columns])),
        html.Tbody([
            html.Tr([html.Td(str(r[c]), style=td_s) for c in action_df.columns])
            for _, r in action_df.iterrows()
        ]),
    ], style={"width":"100%","borderCollapse":"collapse"})

    action_card = html.Div([
        html.Div("Prescriptive Action Engine — Live Macro Alerts",
                 style={"fontSize":"12px","fontWeight":"700","color":NAVY,"marginBottom":"10px"}),
        tbl,
    ], style={"background":CARD,"borderRadius":"10px","padding":"18px 22px",
              "boxShadow":"0 1px 3px rgba(0,0,0,0.06)","border":f"1px solid {GREY}","flex":"1"})

    return html.Div([
        header(6,"Predictive Synthesis & Scenarios",SUBTITLES["macro6"]),
        body(
            row(kpi("90-Day Cash at Risk",       f"${cfar/1e3:.0f}K",    AMBER),
                kpi("Covenant Breach Prob.",      f"{breach_prob:.1f}%",
                    GREEN if breach_prob<5 else (AMBER if breach_prob<15 else RED)),
                kpi("P50 Wk-13 Cash Balance",    f"${p50[-1]:.2f}M",     GREEN),
                kpi("Macro-Beta Score",           f"{macro_beta:.2f}",    AMBER)),
            card("Probabilistic Cash Runway — 1,000 Monte Carlo Simulations", fig1, height=300, question="What is the realistic range of cash outcomes over the next 13 weeks under macro uncertainty?"),
            row(col(card("EBITDA Stress Test — 4 Macro Scenarios", fig2, question="How much would our profitability deteriorate under stagflation, rate shock, or recession?")), action_card),
        ),
    ])

# ── ROUTING ───────────────────────────────────────────────────────────────────
BUILDERS = {
    "macro1":macro1,"macro2":macro2,"macro3":macro3,
    "macro4":macro4,"macro5":macro5,"macro6":macro6,
}

def page_from_url(pathname):
    slug = (pathname or "").strip("/")
    return slug if slug in BUILDERS else "macro1"

@app.callback(Output("url","pathname"),
              [Input({"type":"nav","index":pid},"n_clicks") for pid,_ in PAGES],
              prevent_initial_call=True)
def navigate(*_):
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
        return "/" + ctx.triggered_id["index"]
    return "/macro1"

@app.callback(
    Output("sidebar-container","children"),
    Output("page-content","children"),
    Input("url","pathname"),
)
def render_all(pathname):
    page = page_from_url(pathname)
    return sidebar(page), BUILDERS[page]()

if __name__ == "__main__":
    app.run(debug=True, port=8051)
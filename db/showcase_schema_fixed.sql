-- ============================================================
-- showcase_schema.sql
-- C-Suite Intelligence Platform — Azure SQL Schema
-- Execute this BEFORE showcase_data.sql
-- Azure SQL Basic tier (2GB) — Canada Central
-- ============================================================

SET NOCOUNT ON;

-- ── Schemas ──────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dim')   EXEC('CREATE SCHEMA dim');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'erp')   EXEC('CREATE SCHEMA erp');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'macro')  EXEC('CREATE SCHEMA macro');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'intel')  EXEC('CREATE SCHEMA intel');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'pbi')    EXEC('CREATE SCHEMA pbi');

-- ────────────────────────────────────────────────────────────
-- DIMENSIONS
-- ────────────────────────────────────────────────────────────

CREATE TABLE dim.entities (
    entity_id               CHAR(3)         NOT NULL PRIMARY KEY,
    entity_name             NVARCHAR(100)   NOT NULL,
    province                CHAR(2)         NOT NULL,
    tax_code                VARCHAR(5)      NOT NULL,
    tax_rate                DECIMAL(7,5)    NOT NULL,
    is_holdco               BIT             NOT NULL DEFAULT 0,
    fiscal_year_start_month TINYINT         NOT NULL DEFAULT 4
);

CREATE TABLE dim.chart_of_accounts (
    account_id      VARCHAR(6)      NOT NULL PRIMARY KEY,
    account_name    NVARCHAR(80)    NOT NULL,
    category        VARCHAR(20)     NOT NULL,   -- Revenue|COGS|OpEx|CapEx|Asset|Liability|Equity|Intercompany
    normal_balance  CHAR(2)         NOT NULL,   -- DR|CR
    primary_entity  CHAR(3)         NOT NULL
);

CREATE TABLE dim.cost_centres (
    cc_id       VARCHAR(5)      NOT NULL PRIMARY KEY,
    cc_name     NVARCHAR(80)    NOT NULL,
    entity_id   CHAR(3)         NOT NULL REFERENCES dim.entities(entity_id),
    department  VARCHAR(30)     NOT NULL
);

CREATE TABLE dim.customers (
    customer_id         VARCHAR(5)      NOT NULL PRIMARY KEY,
    customer_name       NVARCHAR(80)    NOT NULL,
    sector              VARCHAR(30)     NOT NULL,
    province            CHAR(2)         NOT NULL,
    payment_terms_days  SMALLINT        NOT NULL,
    credit_limit        INT             NOT NULL,
    risk_tier           VARCHAR(10)     NOT NULL,   -- Low|Medium|High
    ecl_rate_base       DECIMAL(6,4)    NOT NULL,
    entity_id           CHAR(3)         NOT NULL REFERENCES dim.entities(entity_id),
    active              BIT             NOT NULL DEFAULT 1
);

CREATE TABLE dim.vendors (
    vendor_id           VARCHAR(5)      NOT NULL PRIMARY KEY,
    vendor_name         NVARCHAR(80)    NOT NULL,
    category            VARCHAR(40)     NOT NULL,
    payment_terms_days  SMALLINT        NOT NULL,
    province            CHAR(2)         NOT NULL,
    strategic           BIT             NOT NULL DEFAULT 0
);

-- ────────────────────────────────────────────────────────────
-- ERP FACTS
-- ────────────────────────────────────────────────────────────

CREATE TABLE erp.gl_ledger (
    gl_id           INT             NOT NULL PRIMARY KEY,
    entity_id       CHAR(3)         NOT NULL REFERENCES dim.entities(entity_id),
    account_id      VARCHAR(6)      NOT NULL REFERENCES dim.chart_of_accounts(account_id),
    cc_id           VARCHAR(5)      NOT NULL REFERENCES dim.cost_centres(cc_id),
    period_start    DATE            NOT NULL,
    period_end      DATE            NOT NULL,
    fiscal_year     VARCHAR(7)      NOT NULL,
    fiscal_quarter  CHAR(2)         NOT NULL,
    debit_amount    DECIMAL(14,2)   NOT NULL DEFAULT 0,
    credit_amount   DECIMAL(14,2)   NOT NULL DEFAULT 0,
    description     NVARCHAR(120)   NULL,
    posted          BIT             NOT NULL DEFAULT 1
);

CREATE INDEX ix_gl_entity_period ON erp.gl_ledger (entity_id, period_start);
CREATE INDEX ix_gl_account       ON erp.gl_ledger (account_id);

CREATE TABLE erp.ar_invoices (
    invoice_id      VARCHAR(12)     NOT NULL PRIMARY KEY,
    customer_id     VARCHAR(5)      NOT NULL REFERENCES dim.customers(customer_id),
    entity_id       CHAR(3)         NOT NULL REFERENCES dim.entities(entity_id),
    invoice_date    DATE            NOT NULL,
    due_date        DATE            NOT NULL,
    amount          DECIMAL(14,2)   NOT NULL,
    paid            BIT             NOT NULL DEFAULT 0,
    payment_date    DATE            NULL,
    days_past_due   SMALLINT        NOT NULL DEFAULT 0,
    aging_bucket    VARCHAR(10)     NOT NULL,   -- Current|1-30|31-60|61-90|91+
    ecl_rate        DECIMAL(6,4)    NOT NULL,
    ecl_amount      DECIMAL(12,2)   NOT NULL DEFAULT 0,
    fiscal_year     VARCHAR(7)      NOT NULL,
    period_label    VARCHAR(10)     NOT NULL
);

CREATE INDEX ix_ar_customer  ON erp.ar_invoices (customer_id);
CREATE INDEX ix_ar_date      ON erp.ar_invoices (invoice_date);
CREATE INDEX ix_ar_paid      ON erp.ar_invoices (paid, due_date);

CREATE TABLE erp.ap_invoices (
    ap_id           VARCHAR(12)     NOT NULL PRIMARY KEY,
    vendor_id       VARCHAR(5)      NOT NULL REFERENCES dim.vendors(vendor_id),
    entity_id       CHAR(3)         NOT NULL REFERENCES dim.entities(entity_id),
    invoice_date    DATE            NOT NULL,
    due_date        DATE            NOT NULL,
    amount          DECIMAL(14,2)   NOT NULL,
    paid            BIT             NOT NULL DEFAULT 0,
    payment_date    DATE            NULL,
    days_from_due   SMALLINT        NOT NULL DEFAULT 0,  -- negative = paid early
    fiscal_year     VARCHAR(7)      NOT NULL,
    period_label    VARCHAR(10)     NOT NULL
);

CREATE INDEX ix_ap_vendor ON erp.ap_invoices (vendor_id);
CREATE INDEX ix_ap_date   ON erp.ap_invoices (invoice_date);

CREATE TABLE erp.budget (
    bgt_id          INT             NOT NULL PRIMARY KEY,
    entity_id       CHAR(3)         NOT NULL REFERENCES dim.entities(entity_id),
    period_start    DATE            NOT NULL,
    fiscal_year     VARCHAR(7)      NOT NULL,
    fiscal_quarter  CHAR(2)         NOT NULL,
    period_label    VARCHAR(10)     NOT NULL,
    revenue_budget  DECIMAL(14,2)   NOT NULL,
    cogs_budget     DECIMAL(14,2)   NOT NULL,
    opex_budget     DECIMAL(14,2)   NOT NULL,
    ebitda_budget   DECIMAL(14,2)   NOT NULL
);

-- ────────────────────────────────────────────────────────────
-- MACRO DATA
-- ────────────────────────────────────────────────────────────

CREATE TABLE macro.economic_indicators (
    obs_id      INT             NOT NULL PRIMARY KEY,
    obs_date    DATE            NOT NULL,
    metric_key  VARCHAR(40)     NOT NULL,
    value       DECIMAL(14,4)   NOT NULL,
    source      VARCHAR(60)     NOT NULL,
    frequency   VARCHAR(10)     NOT NULL
);

CREATE INDEX ix_macro_key_date ON macro.economic_indicators (metric_key, obs_date);

CREATE TABLE macro.macro_signals (
    sig_id              INT             NOT NULL PRIMARY KEY,
    obs_date            DATE            NOT NULL,
    yield_spread_bps    DECIMAL(8,1)    NOT NULL,   -- 10Y minus 2Y in basis points
    yield_regime        VARCHAR(15)     NOT NULL,   -- Inverted|Flat|Normal|Steep
    cycle_phase         VARCHAR(20)     NOT NULL,   -- Early Recovery|Mid Expansion|Late Expansion|Contraction
    policy_rate         DECIMAL(6,4)    NULL,
    usdcad              DECIMAL(8,4)    NULL
);

CREATE INDEX ix_signals_date ON macro.macro_signals (obs_date);

CREATE TABLE macro.sector_rotation (
    row_id          INT             NOT NULL PRIMARY KEY,
    obs_date        DATE            NOT NULL,
    ticker          VARCHAR(10)     NOT NULL,
    description     NVARCHAR(80)    NOT NULL,
    close_price     DECIMAL(10,2)   NOT NULL
);

CREATE INDEX ix_rotation_date   ON macro.sector_rotation (obs_date);
CREATE INDEX ix_rotation_ticker ON macro.sector_rotation (ticker, obs_date);

-- ────────────────────────────────────────────────────────────
-- INTELLIGENCE OUTPUTS
-- ────────────────────────────────────────────────────────────

CREATE TABLE intel.ar_predictions (
    pred_id                 INT             NOT NULL PRIMARY KEY,
    customer_id             VARCHAR(5)      NOT NULL REFERENCES dim.customers(customer_id),
    score_date              DATE            NOT NULL,
    default_prob_60d        DECIMAL(6,4)    NOT NULL,
    risk_tier_predicted     VARCHAR(10)     NOT NULL,
    total_ar_balance        DECIMAL(14,2)   NOT NULL,
    ecl_estimate            DECIMAL(12,2)   NOT NULL,
    recommended_action      NVARCHAR(200)   NOT NULL
);

CREATE TABLE intel.shap_explanations (
    shap_id         INT             NOT NULL PRIMARY KEY,
    customer_id     VARCHAR(5)      NOT NULL REFERENCES dim.customers(customer_id),
    score_date      DATE            NOT NULL,
    rank            TINYINT         NOT NULL,
    feature_name    VARCHAR(40)     NOT NULL,
    shap_value      DECIMAL(10,4)   NOT NULL,
    direction       VARCHAR(20)     NOT NULL    -- Increases Risk | Decreases Risk
);

CREATE INDEX ix_shap_customer ON intel.shap_explanations (customer_id, score_date);

CREATE TABLE intel.cash_flow_forecast (
    fc_id                   INT             NOT NULL PRIMARY KEY,
    entity_id               CHAR(3)         NOT NULL REFERENCES dim.entities(entity_id),
    forecast_date           DATE            NOT NULL,
    horizon_days            SMALLINT        NOT NULL,
    forecast_horizon_date   DATE            NOT NULL,
    p10_cash                DECIMAL(16,2)   NOT NULL,
    p50_cash                DECIMAL(16,2)   NOT NULL,
    p90_cash                DECIMAL(16,2)   NOT NULL,
    credit_facility_floor   DECIMAL(16,2)   NOT NULL DEFAULT 0,
    runway_days_p10         INT             NOT NULL,
    model                   VARCHAR(40)     NOT NULL
);

CREATE TABLE intel.demand_forecast (
    df_id               INT             NOT NULL PRIMARY KEY,
    product_category    NVARCHAR(60)    NOT NULL,
    forecast_date       DATE            NOT NULL,
    horizon_days        SMALLINT        NOT NULL,
    p10_units           DECIMAL(12,0)   NOT NULL,
    p50_units           DECIMAL(12,0)   NOT NULL,
    p90_units           DECIMAL(12,0)   NOT NULL,
    model               VARCHAR(40)     NOT NULL
);

CREATE TABLE intel.inventory_recommendations (
    inv_id                  INT             NOT NULL PRIMARY KEY,
    product_category        NVARCHAR(60)    NOT NULL,
    calc_date               DATE            NOT NULL,
    current_safety_stock    DECIMAL(10,0)   NOT NULL,
    p10_demand_30d          DECIMAL(10,0)   NOT NULL,
    recommended_safety_stock DECIMAL(10,0)  NOT NULL,
    unit_value              DECIMAL(10,2)   NOT NULL,
    monthly_holding_saving  DECIMAL(12,2)   NOT NULL,
    annual_holding_saving   DECIMAL(12,2)   NOT NULL,
    action_priority         VARCHAR(10)     NOT NULL    -- HIGH|MEDIUM|LOW
);

CREATE TABLE intel.elasticity_classification (
    elast_id                        INT             NOT NULL PRIMARY KEY,
    product_category                NVARCHAR(60)    NOT NULL,
    calc_date                       DATE            NOT NULL,
    elasticity_class                VARCHAR(15)     NOT NULL,   -- Inelastic|Elastic|Unit Elastic
    price_elasticity                DECIMAL(6,2)    NOT NULL,
    recommended_price_increase_pct  DECIMAL(5,1)    NOT NULL,
    est_annual_margin_uplift        DECIMAL(14,2)   NOT NULL,
    recommended_action              NVARCHAR(200)   NOT NULL,
    confidence                      VARCHAR(10)     NOT NULL
);

CREATE TABLE intel.decision_alerts (
    alert_id            INT             NOT NULL PRIMARY KEY,
    alert_name          NVARCHAR(80)    NOT NULL,
    department          VARCHAR(30)     NOT NULL,
    eval_date           DATE            NOT NULL,
    condition_text      NVARCHAR(120)   NOT NULL,
    threshold_value     VARCHAR(20)     NOT NULL,
    actual_value        VARCHAR(20)     NOT NULL,
    severity            VARCHAR(10)     NOT NULL,   -- RED|AMBER|GREEN
    status              VARCHAR(10)     NOT NULL DEFAULT 'ACTIVE',
    recommended_action  NVARCHAR(250)   NOT NULL,
    dollar_impact       INT             NOT NULL,
    expected_outcome    NVARCHAR(200)   NOT NULL
);

-- ────────────────────────────────────────────────────────────
-- POWER BI VIEWS  (7 views — one per dashboard section)
-- ────────────────────────────────────────────────────────────

-- 1. Executive Action Queue
GO
CREATE OR ALTER VIEW pbi.vw_executive_action_queue AS
SELECT
    a.alert_id,
    a.severity,
    a.department,
    a.alert_name,
    a.condition_text,
    a.threshold_value,
    a.actual_value,
    a.recommended_action,
    a.dollar_impact,
    a.expected_outcome,
    a.eval_date,
    CASE a.severity WHEN 'RED' THEN 1 WHEN 'AMBER' THEN 2 ELSE 3 END AS severity_sort
FROM intel.decision_alerts a
WHERE a.status = 'ACTIVE';

-- 2. Macro Intelligence
GO
CREATE OR ALTER VIEW pbi.vw_macro_intelligence AS
SELECT
    s.obs_date,
    s.yield_spread_bps,
    s.yield_regime,
    s.cycle_phase,
    s.policy_rate,
    s.usdcad,
    -- Orders/Inventory from StatCan
    ord.value  AS mfg_new_orders,
    inv.value  AS mfg_inventory,
    CASE
        WHEN inv.value > 0
        THEN ROUND(CAST(ord.value AS FLOAT) / CAST(inv.value AS FLOAT), 4)
        ELSE NULL
    END AS orders_inventory_ratio
FROM macro.macro_signals s
LEFT JOIN macro.economic_indicators ord
    ON ord.obs_date = s.obs_date AND ord.metric_key = 'STATCAN_MFG_NEW_ORDERS'
LEFT JOIN macro.economic_indicators inv
    ON inv.obs_date = s.obs_date AND inv.metric_key = 'STATCAN_MFG_INVENTORY';

-- 3. P&L Intelligence  (actuals vs. budget, variance, EBITDA)
GO
CREATE OR ALTER VIEW pbi.vw_pl_intelligence AS
WITH actuals AS (
    SELECT
        g.entity_id,
        g.period_start,
        g.fiscal_year,
        g.fiscal_quarter,
        g.period_label,
        SUM(CASE WHEN a.category = 'Revenue'  THEN g.credit_amount - g.debit_amount ELSE 0 END) AS revenue_actual,
        SUM(CASE WHEN a.category = 'COGS'     THEN g.debit_amount  - g.credit_amount ELSE 0 END) AS cogs_actual,
        SUM(CASE WHEN a.category = 'OpEx'     THEN g.debit_amount  - g.credit_amount ELSE 0 END) AS opex_actual,
        SUM(CASE WHEN a.category = 'CapEx'    THEN g.debit_amount  - g.credit_amount ELSE 0 END) AS capex_actual
    FROM erp.gl_ledger g
    JOIN dim.chart_of_accounts a ON a.account_id = g.account_id
    WHERE g.posted = 1
    GROUP BY g.entity_id, g.period_start, g.fiscal_year, g.fiscal_quarter, g.period_label
)
SELECT
    ac.entity_id,
    e.entity_name,
    ac.period_start,
    ac.fiscal_year,
    ac.fiscal_quarter,
    ac.period_label,
    ac.revenue_actual,
    b.revenue_budget,
    ac.revenue_actual - b.revenue_budget                         AS revenue_variance,
    CASE WHEN b.revenue_budget > 0
         THEN ROUND((ac.revenue_actual - b.revenue_budget) / b.revenue_budget * 100, 1)
         ELSE NULL END                                           AS revenue_variance_pct,
    ac.cogs_actual,
    b.cogs_budget,
    ac.opex_actual,
    b.opex_budget,
    ac.opex_actual - b.opex_budget                              AS opex_variance,
    ac.revenue_actual - ac.cogs_actual                          AS gross_profit_actual,
    ac.revenue_actual - ac.cogs_actual - ac.opex_actual         AS ebitda_actual,
    b.ebitda_budget,
    (ac.revenue_actual - ac.cogs_actual - ac.opex_actual)
        - b.ebitda_budget                                       AS ebitda_variance,
    ac.capex_actual
FROM actuals ac
JOIN erp.budget b
    ON b.entity_id = ac.entity_id AND b.period_start = ac.period_start
JOIN dim.entities e
    ON e.entity_id = ac.entity_id;

-- 4. Credit Risk Intelligence
GO
CREATE OR ALTER VIEW pbi.vw_credit_risk_intelligence AS
SELECT
    p.customer_id,
    c.customer_name,
    c.sector,
    c.province,
    p.default_prob_60d,
    p.risk_tier_predicted,
    p.total_ar_balance,
    p.ecl_estimate,
    p.recommended_action,
    s1.feature_name  AS shap_driver_1,
    s1.shap_value    AS shap_value_1,
    s1.direction     AS shap_direction_1,
    s2.feature_name  AS shap_driver_2,
    s2.shap_value    AS shap_value_2,
    s2.direction     AS shap_direction_2,
    -- Latest DSO from AR
    dso.avg_dso,
    dso.avg_dpd
FROM intel.ar_predictions p
JOIN dim.customers c ON c.customer_id = p.customer_id
LEFT JOIN intel.shap_explanations s1
    ON s1.customer_id = p.customer_id AND s1.score_date = p.score_date AND s1.rank = 1
LEFT JOIN intel.shap_explanations s2
    ON s2.customer_id = p.customer_id AND s2.score_date = p.score_date AND s2.rank = 2
LEFT JOIN (
    SELECT
        customer_id,
        AVG(DATEDIFF(day, invoice_date, ISNULL(payment_date, GETDATE()))) AS avg_dso,
        AVG(CAST(days_past_due AS FLOAT))                                  AS avg_dpd
    FROM erp.ar_invoices
    WHERE invoice_date >= DATEADD(month, -6, GETDATE())
    GROUP BY customer_id
) dso ON dso.customer_id = p.customer_id;

-- 5. Cash Flow Intelligence
GO
CREATE OR ALTER VIEW pbi.vw_cash_flow_intelligence AS
SELECT
    f.entity_id,
    e.entity_name,
    f.forecast_date,
    f.horizon_days,
    f.forecast_horizon_date,
    f.p10_cash,
    f.p50_cash,
    f.p90_cash,
    f.runway_days_p10,
    f.model,
    s.yield_spread_bps,
    s.yield_regime,
    s.cycle_phase,
    s.usdcad
FROM intel.cash_flow_forecast f
JOIN dim.entities e ON e.entity_id = f.entity_id
CROSS APPLY (
    SELECT TOP 1 yield_spread_bps, yield_regime, cycle_phase, usdcad
    FROM macro.macro_signals
    ORDER BY obs_date DESC
) s;

-- 6. Operations Intelligence
GO
CREATE OR ALTER VIEW pbi.vw_operations_intelligence AS
SELECT
    ir.product_category,
    ir.current_safety_stock,
    ir.p10_demand_30d,
    ir.recommended_safety_stock,
    ir.unit_value,
    ir.monthly_holding_saving,
    ir.annual_holding_saving,
    ir.action_priority,
    ec.elasticity_class,
    ec.price_elasticity,
    ec.recommended_price_increase_pct,
    ec.est_annual_margin_uplift,
    ec.recommended_action    AS pricing_action,
    ec.confidence
FROM intel.inventory_recommendations ir
LEFT JOIN intel.elasticity_classification ec
    ON ec.product_category = ir.product_category;

-- 7. Macro History (sparklines — 28 months of signal data)
GO
CREATE OR ALTER VIEW pbi.vw_macro_history AS
SELECT
    s.obs_date,
    s.yield_spread_bps,
    s.yield_regime,
    s.cycle_phase,
    s.policy_rate,
    s.usdcad,
    r60.rs_60d_vs_xiu,
    r60.ticker,
    r60.description
FROM macro.macro_signals s
LEFT JOIN (
    -- 60-day relative strength vs. XIU broad market
    SELECT
        sr.obs_date,
        sr.ticker,
        sr.description,
        ROUND(
            (sr.close_price - LAG(sr.close_price, 60) OVER (PARTITION BY sr.ticker ORDER BY sr.obs_date))
            / NULLIF(LAG(sr.close_price, 60) OVER (PARTITION BY sr.ticker ORDER BY sr.obs_date), 0) * 100
        , 2) AS rs_60d_vs_xiu
    FROM macro.sector_rotation sr
) r60 ON r60.obs_date = s.obs_date;

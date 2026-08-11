import pyodbc
import pandas as pd
import numpy as np
import torch
from chronos import BaseChronosPipeline
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=csuite-sql-server.database.windows.net;"
    "DATABASE=showcase;"
    "UID=csuite_admin;"
    "PWD=C$u1te2024xP0c#"
)
conn = pyodbc.connect(conn_str)
print("Connected to Azure SQL")

# Pull historical monthly revenue from GL
query = """
SELECT
    FORMAT(g.period_start, 'yyyy-MM') AS period,
    SUM(CASE WHEN c.category = 'Revenue' THEN g.credit_amount ELSE 0 END) AS revenue
FROM erp.gl_ledger g
JOIN dim.chart_of_accounts c ON g.account_id = c.account_id
WHERE c.category = 'Revenue'
GROUP BY FORMAT(g.period_start, 'yyyy-MM')
ORDER BY period
"""
df = pd.read_sql(query, conn)
print(f"Loaded {len(df)} months of historical revenue")
print(df.tail(6).to_string(index=False))

# Prepare time series tensor
revenue_series = torch.tensor(df["revenue"].values, dtype=torch.float32)

# Load Chronos mini model
print("Loading Chronos model...")
pipeline = BaseChronosPipeline.from_pretrained(
    "amazon/chronos-t5-mini",
    device_map="cpu",
    torch_dtype=torch.float32
)

# Forecast 12 months forward
print("Forecasting 12 months...")
forecast = pipeline.predict(
    revenue_series,
    prediction_length=12
)

# Extract P10, P50, P90
# forecast shape: (batch, prediction_length) for point; squeeze to (12,)
samples = forecast.numpy() if forecast.ndim == 2 else forecast[0].numpy()
if samples.ndim == 1:
    p10, p50, p90 = samples, samples, samples
else:
    p10 = np.percentile(samples, 10, axis=0)
    p50 = np.percentile(samples, 50, axis=0)
    p90 = np.percentile(samples, 90, axis=0)

# Build forecast dates starting from next month
last_period = pd.to_datetime(df["period"].iloc[-1] + "-01")
forecast_rows = []
for i in range(12):
    fdate = last_period + relativedelta(months=i+1)
    forecast_rows.append({
        "forecast_month": fdate.date(),
        "revenue_forecast": round(float(p50[i]), 2),
        "lower_bound": round(float(p10[i]), 2),
        "upper_bound": round(float(p90[i]), 2),
        "model": "chronos-t5-mini"
    })

# Insert into Azure SQL
cursor = conn.cursor()
cursor.execute("DELETE FROM intel.revenue_forecast_12m")
for r in forecast_rows:
    cursor.execute(
        "INSERT INTO intel.revenue_forecast_12m (forecast_month, revenue_forecast, lower_bound, upper_bound, model) VALUES (?,?,?,?,?)",
        r["forecast_month"], r["revenue_forecast"], r["lower_bound"], r["upper_bound"], r["model"]
    )
    print(f"  {r['forecast_month']}: P10={r['lower_bound']:,.0f} P50={r['revenue_forecast']:,.0f} P90={r['upper_bound']:,.0f}")

conn.commit()
conn.close()
print(f"Done. Inserted 12 forecast rows into intel.revenue_forecast_12m")

import pyodbc
import pandas as pd
from datetime import datetime, timedelta
import random

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=csuite-sql-server.database.windows.net;"
    "DATABASE=showcase;"
    "UID=csuite_admin;"
    "PWD=C$u1te2024xP0c#"
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
print("Connected to Azure SQL")

# 1. CASH BURN WEEKLY
print("Building cash_burn_weekly...")
ar_df = pd.read_sql("SELECT DATEPART(WEEK, payment_date) AS week_num, SUM(amount) AS cash_collected FROM erp.ar_invoices WHERE paid=1 AND payment_date IS NOT NULL AND payment_date >= DATEADD(WEEK,-13,GETDATE()) GROUP BY DATEPART(WEEK, payment_date)", conn)
ap_df = pd.read_sql("SELECT DATEPART(WEEK, due_date) AS week_num, SUM(amount) AS cash_burn FROM erp.ap_invoices WHERE due_date >= DATEADD(WEEK,-13,GETDATE()) GROUP BY DATEPART(WEEK, due_date)", conn)

today = datetime.today()
rows = []
running_balance = 500000.0
avg_collected = float(ar_df["cash_collected"].mean()) if not ar_df.empty else 80000.0
avg_burn = float(ap_df["cash_burn"].mean()) if not ap_df.empty else 65000.0

for i in range(1, 14):
    week_start = today + timedelta(weeks=i-1)
    random.seed(i)
    collected = avg_collected * random.uniform(0.85, 1.15)
    burn = avg_burn * random.uniform(0.90, 1.10)
    running_balance += collected - burn
    rows.append((i, f"Wk {i} ({week_start.strftime('%b %d')})", week_start.date(), round(collected,2), round(burn,2), round(running_balance,2), "base"))

cursor.execute("DELETE FROM intel.cash_burn_weekly")
for r in rows:
    cursor.execute("INSERT INTO intel.cash_burn_weekly (week_num,week_label,week_start_date,avg_cash_collected,avg_cash_burn,running_balance,scenario) VALUES (?,?,?,?,?,?,?)", r)
print(f"  Inserted {len(rows)} rows into intel.cash_burn_weekly")

# 2. COVENANT TRACKER
print("Building covenant_tracker...")
gl_query = '''
SELECT
    FORMAT(g.period_start, 'yyyy-MM') AS period,
    SUM(CASE WHEN c.category = 'Revenue' THEN g.credit_amount ELSE 0 END) AS revenue,
    SUM(CASE WHEN c.category IN ('OpEx','COGS') THEN g.debit_amount ELSE 0 END) AS opex
FROM erp.gl_ledger g
JOIN dim.chart_of_accounts c ON g.account_id = c.account_id
WHERE g.period_start >= DATEADD(MONTH, -12, GETDATE())
GROUP BY FORMAT(g.period_start, 'yyyy-MM')
ORDER BY period
'''
gl_df = pd.read_sql(gl_query, conn)

# Use unpaid AP as net_debt proxy
ap_debt_cur = conn.cursor()
ap_debt_cur.execute("SELECT SUM(amount) FROM erp.ap_invoices WHERE paid=0")
total_ap_debt = float(ap_debt_cur.fetchone()[0] or 0)

cursor.execute("DELETE FROM intel.covenant_tracker")
for _, row in gl_df.iterrows():
    ebitda = row["revenue"] - row["opex"]
    net_debt = total_ap_debt
    debt_service = max(net_debt * 0.08 / 12, 1)
    dscr = ebitda / debt_service
    debt_ebitda = net_debt / max(ebitda, 1)
    print(f"  {row['period']}: ebitda={ebitda:.0f}, net_debt={net_debt:.0f}, dscr={dscr:.2f}, d/e={debt_ebitda:.2f}")
    for scenario, rate_shock in [("base",1.0),("stress_100bps",1.08),("stress_200bps",1.16)]:
        safe_dscr = max(min(round(dscr/rate_shock,4), 9999.9999), -9999.9999)
        safe_de = max(min(round(debt_ebitda,4), 9999.9999), -9999.9999)
        cursor.execute("INSERT INTO intel.covenant_tracker (period,dscr_proxy,debt_ebitda,net_debt,total_liabilities,scenario) VALUES (?,?,?,?,?,?)", row["period"], safe_dscr, safe_de, round(net_debt,2), round(total_ap_debt,2), scenario)
print(f"  Inserted covenant data for {len(gl_df)} periods x 3 scenarios")

conn.commit()
conn.close()
print("Done.")

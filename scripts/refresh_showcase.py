"""
refresh_showcase.py
===================
Monthly refresh script — re-fetches macro data, re-scores AR predictions,
and reloads Azure SQL with fresh data.

Schedule: Run on the 1st of each month (local machine or GitHub Actions).

Usage:
    python refresh_showcase.py \
        --server  your-server.database.windows.net \
        --database showcase \
        --user    your-user \
        --password your-password

Requires:
    pip install pyodbc pandas numpy xgboost shap requests yfinance stats-can
"""

import argparse
import datetime as dt
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)


TRUNCATE_ORDER = [
    # Truncate in reverse dependency order (children before parents)
    "intel.shap_explanations",
    "intel.ar_predictions",
    "intel.decision_alerts",
    "intel.cash_flow_forecast",
    "intel.demand_forecast",
    "intel.inventory_recommendations",
    "intel.elasticity_classification",
    "macro.macro_signals",
    "macro.sector_rotation",
    "macro.economic_indicators",
    # ERP facts: only truncate if you want to rebuild from scratch
    # Leave erp.* tables in place for incremental refreshes
]


def run_generation() -> Path:
    """Re-run the data generation script to produce a fresh showcase_data.sql."""
    log.info("Running generate_showcase_data.py ...")
    result = subprocess.run(
        [sys.executable, "generate_showcase_data.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log.error("Generation failed:\n%s", result.stderr)
        raise RuntimeError("Data generation failed")
    log.info("Generation complete:\n%s", result.stdout)
    return Path("showcase_data.sql")


def reload_azure_sql(sql_file: Path, server: str, database: str, user: str, password: str):
    """
    Truncate macro + intelligence tables and reload from the generated SQL file.
    Uses sqlcmd (installed with SQL Server tools or mssql-tools on Linux/Mac).
    """
    try:
        import pyodbc
    except ImportError:
        log.error("pyodbc not installed. Install with: pip install pyodbc")
        raise

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Encrypt=yes;TrustServerCertificate=no;"
    )

    log.info("Connecting to %s / %s ...", server, database)
    conn   = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Step 1: Truncate tables
    log.info("Truncating %d tables ...", len(TRUNCATE_ORDER))
    for table in TRUNCATE_ORDER:
        cursor.execute(f"DELETE FROM {table}")   # DELETE not TRUNCATE (FK constraints)
        log.info("  Cleared %s", table)
    conn.commit()

    # Step 2: Execute the generated SQL file via sqlcmd
    # pyodbc cannot execute multi-statement SQL files efficiently;
    # sqlcmd handles batches and GO separators correctly.
    log.info("Loading %s via sqlcmd ...", sql_file)
    cmd = [
        "sqlcmd",
        "-S", server,
        "-d", database,
        "-U", user,
        "-P", password,
        "-i", str(sql_file),
        "-b",          # abort on error
        "-I",          # quoted identifiers
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("sqlcmd failed:\n%s", result.stderr)
        raise RuntimeError("SQL load failed")
    log.info("sqlcmd complete.")

    # Step 3: Verify row counts
    checks = [
        ("macro.macro_signals",        "SELECT COUNT(*) FROM macro.macro_signals"),
        ("macro.sector_rotation",       "SELECT COUNT(*) FROM macro.sector_rotation"),
        ("intel.ar_predictions",        "SELECT COUNT(*) FROM intel.ar_predictions"),
        ("intel.decision_alerts",       "SELECT COUNT(*) FROM intel.decision_alerts"),
        ("intel.cash_flow_forecast",    "SELECT COUNT(*) FROM intel.cash_flow_forecast"),
    ]
    log.info("Row count verification:")
    for label, sql in checks:
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        log.info("  %-35s %d rows", label, count)

    cursor.close()
    conn.close()
    log.info("Azure SQL refresh complete.")


def trigger_powerbi_refresh(workspace_id: str, dataset_id: str, tenant_id: str,
                             client_id: str, client_secret: str):
    """
    Trigger a Power BI dataset refresh via the REST API.
    Optional — only needed if you want programmatic refresh rather than
    the scheduled refresh in Power BI Service.
    """
    import requests

    # Get AAD token
    token_url  = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_body = {
        "grant_type":    "client_credentials",
        "client_id":     client_id,
        "client_secret": client_secret,
        "scope":         "https://analysis.windows.net/powerbi/api/.default",
    }
    token_res  = requests.post(token_url, data=token_body)
    aad_token  = token_res.json()["access_token"]

    # Trigger refresh
    refresh_url = (
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
        f"/datasets/{dataset_id}/refreshes"
    )
    headers = {"Authorization": f"Bearer {aad_token}"}
    res = requests.post(refresh_url, headers=headers)

    if res.status_code == 202:
        log.info("Power BI dataset refresh triggered successfully.")
    else:
        log.warning("Power BI refresh returned %d: %s", res.status_code, res.text)


def main():
    parser = argparse.ArgumentParser(description="Monthly showcase refresh")
    parser.add_argument("--server",   required=True)
    parser.add_argument("--database", default="showcase")
    parser.add_argument("--user",     required=True)
    parser.add_argument("--password", required=True)
    # Optional Power BI auto-refresh
    parser.add_argument("--pbi-workspace", default=None)
    parser.add_argument("--pbi-dataset",   default=None)
    parser.add_argument("--pbi-tenant",    default=None)
    parser.add_argument("--pbi-client",    default=None)
    parser.add_argument("--pbi-secret",    default=None)
    args = parser.parse_args()

    start = dt.datetime.now()
    log.info("=== Monthly refresh started: %s ===", start.isoformat())

    # 1. Regenerate data
    sql_file = run_generation()

    # 2. Reload Azure SQL
    reload_azure_sql(
        sql_file  = sql_file,
        server    = args.server,
        database  = args.database,
        user      = args.user,
        password  = args.password,
    )

    # 3. Trigger Power BI refresh (optional)
    if all([args.pbi_workspace, args.pbi_dataset, args.pbi_tenant,
            args.pbi_client, args.pbi_secret]):
        trigger_powerbi_refresh(
            workspace_id  = args.pbi_workspace,
            dataset_id    = args.pbi_dataset,
            tenant_id     = args.pbi_tenant,
            client_id     = args.pbi_client,
            client_secret = args.pbi_secret,
        )
    else:
        log.info("Power BI credentials not provided — trigger refresh manually in Power BI Service.")

    elapsed = (dt.datetime.now() - start).seconds
    log.info("=== Refresh complete in %ds ===", elapsed)


if __name__ == "__main__":
    main()
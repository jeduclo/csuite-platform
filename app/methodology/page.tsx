export default function MethodologyPage() {
  const sources = [
    { name: "Bank of Canada", url: "https://www.bankofcanada.ca", description: "Policy rate, yield curve (2Y/10Y spreads), overnight rate history" },
    { name: "Statistics Canada", url: "https://www.statcan.gc.ca", description: "CPI, PPI (IPPI), manufacturing new orders, inventory ratios" },
    { name: "Yahoo Finance / TSX ETFs", url: "https://finance.yahoo.com", description: "Sector rotation signals via XIU, XEG, XFN, XRE, XST relative strength" },
    { name: "Azure SQL", url: "https://azure.microsoft.com", description: "ERP data store — GL ledger, AR/AP invoices, budget, entities" },
    { name: "XGBoost", url: "https://xgboost.readthedocs.io", description: "AR default probability scoring, price elasticity classification" },
    { name: "SHAP", url: "https://shap.readthedocs.io", description: "Explainability layer — top 2 drivers per customer default prediction" },
    { name: "Amazon Chronos", url: "https://github.com/amazon-science/chronos-forecasting", description: "Probabilistic 90-day cash flow forecasting (P10/P50/P90)" },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-16 space-y-12">
      <section className="space-y-4">
        <h1 className="text-3xl font-bold text-slate-900">Methodology</h1>
        <p className="text-slate-600">
          This platform layers three data sources on top of ERP transactions:
          macro signals, ML scoring, and probabilistic forecasting.
          All computation runs in a monthly Python script — no real-time pipeline required.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900">Data Sources</h2>
        <div className="space-y-3">
          {sources.map((s, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-lg px-5 py-4">
              <div className="flex items-center gap-2 mb-1">
                <a href={s.url} target="_blank" rel="noopener noreferrer"
                  className="font-semibold text-slate-900 hover:text-emerald-600">
                  {s.name}
                </a>
              </div>
              <p className="text-slate-500 text-sm">{s.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900">Infrastructure</h2>
        <div className="bg-white border border-slate-200 rounded-lg px-5 py-4 text-sm text-slate-600 space-y-2">
          <p>🗄️ <strong>Azure SQL</strong> — Basic tier (~$5 CAD/month). Hosts all ERP, macro, and ML output tables.</p>
          <p>🐍 <strong>Python 3.11</strong> — Monthly refresh script re-fetches macro data, re-scores AR predictions, reloads Azure SQL.</p>
          <p>📊 <strong>Power BI</strong> — Reads from 7 pre-computed views. No DAX complexity needed.</p>
          <p>🌐 <strong>Next.js on Vercel</strong> — Embeds Power BI reports via Service Principal. Free hobby tier.</p>
          <p>💰 <strong>Total infrastructure cost</strong> — ~$35 CAD/month.</p>
        </div>
      </section>
    </div>
  );
}

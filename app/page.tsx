import Link from "next/link";
import QuestionCard from "@/components/QuestionCard";
import ROITable from "@/components/ROITable";

const QUESTIONS = [
  {
    number: 1,
    question: "Which customers will default in the next 60 days?",
    erpAnswer: "Aged AR report showing who is already late — backward-looking.",
    platformAnswer: "XGBoost probability score per customer, with SHAP explanation of the top 2 risk drivers — before they miss a single payment.",
    department: "CRO" as const,
  },
  {
    number: 2,
    question: "What is our worst-case 90-day cash position?",
    erpAnswer: "Static cash flow roll-forward from historical averages.",
    platformAnswer: "Chronos P10/P50/P90 fan chart updated daily. The P10 is the number the Treasurer needs to size the credit facility drawdown.",
    department: "CFO" as const,
  },
  {
    number: 3,
    question: "Are we in expansion, late-cycle, or contraction?",
    erpAnswer: "No answer. ERP has no macro awareness.",
    platformAnswer: "4-phase cycle classification from TSX sector rotation and the BoC yield curve. Updated daily.",
    department: "CEO" as const,
  },
  {
    number: 4,
    question: "Should we lock in fixed-rate debt now or wait?",
    erpAnswer: "No answer. GL postings do not contain yield curve data.",
    platformAnswer: "Yield curve spread + BoC policy trajectory → plain-English recommendation with estimated annual saving.",
    department: "CFO" as const,
  },
  {
    number: 5,
    question: "Which product lines can absorb a price increase?",
    erpAnswer: "Historical revenue by SKU — no demand sensitivity analysis.",
    platformAnswer: "XGBoost elasticity classification per category. Inelastic categories show estimated annual margin uplift if price is increased.",
    department: "COO" as const,
  },
  {
    number: 6,
    question: "How much cash is trapped in excess safety stock?",
    erpAnswer: "On-hand inventory value at cost — no forward demand signal.",
    platformAnswer: "Moirai P10 demand forecast → dynamic safety stock target → dollar saving per category at current holding cost rate.",
    department: "COO" as const,
  },
  {
    number: 7,
    question: "Which macro signals should trigger a credit policy change?",
    erpAnswer: "No answer. ERP credit modules respond to individual customer transactions, not market-wide signals.",
    platformAnswer: "Automated alert engine: 9 threshold rules evaluated nightly against BoC, StatCan, and TSX data. Fires before defaults appear.",
    department: "CRO" as const,
  },
  {
    number: 8,
    question: "What is our credit loss exposure if spreads widen 50 bps?",
    erpAnswer: "Allowance for doubtful accounts uses a static historical write-off percentage.",
    platformAnswer: "ECL × macro stress multiplier from the What-If slider. Portfolio-level impact under any spread scenario.",
    department: "CRO" as const,
  },
  {
    number: 9,
    question: "Are we paying vendors on time and what does the DPO trend signal?",
    erpAnswer: "AP aging report — partially. Cannot contextualise DPO against macro regime.",
    platformAnswer: "DPO trend + Cash Conversion Cycle + Orders/Inventory ratio. In a contraction, stretching payables is a liquidity tool, not a failure.",
    department: "COO" as const,
  },
  {
    number: 10,
    question: "What do equity markets think our industry faces next quarter?",
    erpAnswer: "No answer. ERP has no connection to public market data.",
    platformAnswer: "TSX sector ETF relative strength rotation: Staples and Utilities leading signals consumer weakness 1–2 quarters ahead.",
    department: "CEO" as const,
  },
];

export default function LandingPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-16 space-y-20">
      <section className="text-center space-y-6">
        <p className="text-sm font-semibold text-emerald-600 uppercase tracking-widest">
          C-Suite Intelligence Platform
        </p>
        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 leading-tight">
          What Your ERP<br />Cannot Tell You
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          ERP systems answer one question: <em>what happened</em>.
          This platform answers ten questions your ERP cannot:
          what will happen, and what to do about it — before the cash has left the building.
        </p>
        <Link
          href="/dashboard"
          className="inline-block bg-slate-900 text-white px-8 py-3 rounded-lg font-medium hover:bg-slate-700 transition-colors"
        >
          See it live →
        </Link>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-bold text-slate-900">The 10 Questions</h2>
        <p className="text-slate-500 text-sm">
          Click any question to compare what your ERP reports vs. what this platform delivers.
        </p>
        <div className="space-y-2 mt-4">
          {QUESTIONS.map(q => (
            <QuestionCard key={q.number} {...q} />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">How It Works</h2>
        <div className="bg-white border border-slate-200 rounded-xl p-6 text-sm text-slate-600 space-y-2">
          <div className="flex items-center gap-3">
            <span className="bg-slate-100 px-3 py-1 rounded font-mono text-xs">Your ERP data</span>
            <span className="text-slate-300">→</span>
            <span className="bg-slate-100 px-3 py-1 rounded font-mono text-xs">Azure SQL</span>
            <span className="text-slate-300">→</span>
            <span className="bg-slate-100 px-3 py-1 rounded font-mono text-xs">ML scoring + macro signals</span>
            <span className="text-slate-300">→</span>
            <span className="bg-emerald-100 px-3 py-1 rounded font-mono text-xs text-emerald-800">Decisions</span>
          </div>
          <p className="text-slate-400 text-xs">
            No ADF. No real-time pipeline. A Python script runs monthly, loads Azure SQL,
            and Power BI serves the intelligence layer. Infrastructure cost: ~$35 CAD/month.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-900">Conservative Annual ROI</h2>
        <ROITable />
      </section>
    </div>
  );
}

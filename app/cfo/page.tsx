"use client";
import { useState } from "react";
import PowerBIEmbed from "@/components/PowerBIEmbed";

const CFO_PAGES = [
  { key: "cfo1", label: "Financial Velocity",    page: "b16ab6f653eb3c8d0c48", description: "Is the business generating cash efficiently?" },
  { key: "cfo2", label: "Working Capital",        page: "2171f80e8d0a3bc655d2", description: "How efficiently are we managing the cash conversion cycle?" },
  { key: "cfo3", label: "Solvency & Debt",        page: "993f735a1ec814ee0181", description: "Are we solvent and within our covenants?" },
  { key: "cfo4", label: "Unit Economics",         page: "2725032e3aeb9970cab2", description: "Are our margins healthy and how close are we to break-even?" },
  { key: "cfo5", label: "13-Week Cash Forecast",  page: "f99c20b581ba42b59808", description: "Do we have a cash problem in the next quarter?" },
  { key: "cfo6", label: "Strategic Model",        page: "47fb05827cb80bd0ea14", description: "Is the business structurally healthy for the next 12 months?" },
  { key: "cfo7", label: "Macro Environment",      page: "fa08fc0a07b87073e252", description: "What is the external environment doing to us?" },
  { key: "cfo8", label: "Sector Rotation",        page: "199118ccde367e02148c", description: "What are institutional investors telling us about the economy?" },
];

export default function CFOPage() {
  const [active, setActive] = useState("cfo1");
  const current = CFO_PAGES.find(p => p.key === active)!;
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">CFO Intelligence App</h1>
        <p className="text-slate-400 text-sm mt-1 italic">
          &quot;Your ERP is a rearview mirror. This app is the windshield.&quot;
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {CFO_PAGES.map(p => (
          <button
            key={p.key}
            onClick={() => setActive(p.key)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              active === p.key
                ? "bg-blue-900 text-white shadow-md"
                : "bg-white text-slate-600 border border-slate-200 hover:border-slate-400"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
        <p className="text-blue-800 text-sm font-medium">{current.description}</p>
      </div>
      <PowerBIEmbed persona="cfo_intel" pageName={current.page} />
    </div>
  );
}

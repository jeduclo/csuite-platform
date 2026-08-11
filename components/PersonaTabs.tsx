"use client";

import { useState } from "react";
import PowerBIEmbed from "./PowerBIEmbed";

const PERSONAS = [
  { key: "action_queue", label: "Action Queue", description: "All active alerts across the portfolio — severity-sorted by financial impact", icon: "🚨", page: "b492d195802336a0808b" },
  { key: "ceo",          label: "CEO — Macro",  description: "Business cycle phase, sector rotation, capital allocation posture", icon: "📊", page: "53abf809c19081243abc" },
  { key: "cfo",          label: "CFO — Cash",   description: "Probabilistic 90-day cash outlook, yield curve treasury action, FX sensitivity", icon: "💰", page: "b9463130108c2850bad6" },
  { key: "cro",          label: "CRO — Credit", description: "60-day default probabilities, SHAP drivers, ECL stress scenarios", icon: "⚠️", page: "59350ee4040a00059203" },
  { key: "coo",          label: "COO — Ops",    description: "Inventory optimisation, price elasticity, DPO trend, cash conversion cycle", icon: "⚙️", page: "96081fb3e525094068d0" },
];

export default function PersonaTabs() {
  const [active, setActive] = useState("action_queue");
  const current = PERSONAS.find(p => p.key === active)!;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {PERSONAS.map(p => (
          <button
            key={p.key}
            onClick={() => setActive(p.key)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              active === p.key
                ? "bg-slate-900 text-white shadow-md"
                : "bg-white text-slate-600 border border-slate-200 hover:border-slate-400"
            }`}
          >
            {p.icon} {p.label}
          </button>
        ))}
      </div>
      <p className="text-slate-500 text-sm">{current.description}</p>
      <PowerBIEmbed persona={current.key} pageName={current.page} />
    </div>
  );
}

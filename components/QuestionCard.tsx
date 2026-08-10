"use client";

import { useState } from "react";

interface Props {
  number:         number;
  question:       string;
  erpAnswer:      string;
  platformAnswer: string;
  department:     "CEO" | "CFO" | "CRO" | "COO";
}

const DEPT_COLORS: Record<string, string> = {
  CEO: "bg-blue-100 text-blue-800",
  CFO: "bg-purple-100 text-purple-800",
  CRO: "bg-red-100 text-red-800",
  COO: "bg-green-100 text-green-800",
};

export default function QuestionCard({
  number, question, erpAnswer, platformAnswer, department
}: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-slate-200 rounded-lg bg-white shadow-sm overflow-hidden">
      <button
        className="w-full px-6 py-4 text-left flex items-start gap-4"
        onClick={() => setOpen(o => !o)}
      >
        <span className="text-2xl font-bold text-slate-300 w-8 shrink-0">
          {String(number).padStart(2, "0")}
        </span>
        <div className="flex-1">
          <p className="font-medium text-slate-800">{question}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${DEPT_COLORS[department]}`}>
            {department}
          </span>
          <span className="text-slate-400">{open ? "▲" : "▼"}</span>
        </div>
      </button>

      {open && (
        <div className="px-6 pb-5 grid md:grid-cols-2 gap-4 border-t border-slate-100">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">
              What your ERP says
            </p>
            <p className="text-slate-600 text-sm">{erpAnswer}</p>
          </div>
          <div className="bg-emerald-50 rounded-lg p-4">
            <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-1">
              What this platform says
            </p>
            <p className="text-slate-700 text-sm">{platformAnswer}</p>
          </div>
        </div>
      )}
    </div>
  );
}

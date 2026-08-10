export default function ROITable() {
  const rows = [
    ["AR default prevention (20% reduction on $1.2M bad debt pool)", "$240,000"],
    ["DSO reduction — 3 days at 7% cost of capital",                "$57,000"],
    ["Inventory holding cost reduction",                             "$60,000"],
    ["Pricing optimisation (inelastic categories)",                  "$150,000–$500,000"],
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 border-b border-slate-200">
          <tr>
            <th className="text-left px-6 py-3 text-slate-500 font-medium">Intelligence layer</th>
            <th className="text-right px-6 py-3 text-slate-500 font-medium">Conservative annual value</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([label, value], i) => (
            <tr key={i} className="border-b border-slate-100">
              <td className="px-6 py-3 text-slate-700">{label}</td>
              <td className="px-6 py-3 text-right font-mono text-emerald-700">{value}</td>
            </tr>
          ))}
          <tr className="bg-slate-50 font-semibold">
            <td className="px-6 py-3 text-slate-900">Total annual benefit</td>
            <td className="px-6 py-3 text-right font-mono text-emerald-800">~$507,000+</td>
          </tr>
          <tr>
            <td className="px-6 py-3 text-slate-500">Infrastructure cost</td>
            <td className="px-6 py-3 text-right font-mono text-slate-500">~$5,000/year</td>
          </tr>
          <tr className="bg-emerald-50 font-bold">
            <td className="px-6 py-3 text-slate-900">Net ROI</td>
            <td className="px-6 py-3 text-right font-mono text-emerald-700">&gt;100×</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

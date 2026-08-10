import PersonaTabs from "@/components/PersonaTabs";

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Executive Intelligence Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">
          Select a persona to load the relevant embedded report.
          All reports refresh monthly from live BoC and StatCan data.
        </p>
      </div>
      <PersonaTabs />
    </div>
  );
}

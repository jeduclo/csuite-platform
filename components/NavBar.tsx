import Link from "next/link";

export default function NavBar() {
  return (
    <nav className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
      <Link href="/" className="text-slate-900 font-bold text-lg">
        C-Suite Intelligence
      </Link>
      <div className="flex gap-6 text-sm text-slate-600">
        <Link href="/" className="hover:text-slate-900">Home</Link>
        <Link href="/dashboard" className="hover:text-slate-900">Dashboard</Link>
        <Link href="/methodology" className="hover:text-slate-900">Methodology</Link>
      </div>
    </nav>
  );
}

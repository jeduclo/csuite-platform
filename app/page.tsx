"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const signals = [
  { label: "Cash Position — Week 13", values: ["$6.97M", "$7.2M", "$6.8M"], status: "healthy" },
  { label: "DSCR vs Covenant Floor", values: ["−5.33×", "−4.1×", "−6.2×"], status: "breach" },
  { label: "Revenue Forecast P50", values: ["$1.06M", "$1.1M", "$0.99M"], status: "watch" },
];

function LiveSignal({ label, values, status }: { label: string; values: string[]; status: string }) {
  const [idx, setIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIdx(i => (i + 1) % values.length);
        setVisible(true);
      }, 300);
    }, 2200 + Math.random() * 800);
    return () => clearInterval(interval);
  }, [values.length]);

  const color =
    status === "healthy" ? "#10B981" :
    status === "breach" ? "#F59E0B" : "#60A5FA";

  return (
    <div style={{
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: "12px",
      padding: "20px 24px",
      minWidth: "200px",
      flex: 1,
    }}>
      <div style={{ fontSize: "11px", color: "#94A3B8", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "10px" }}>
        {label}
      </div>
      <div style={{
        fontSize: "28px",
        fontWeight: "700",
        color,
        fontFamily: "monospace",
        opacity: visible ? 1 : 0,
        transition: "opacity 0.3s ease",
        letterSpacing: "-0.02em",
      }}>
        {values[idx]}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "8px" }}>
        <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: color, boxShadow: `0 0 6px ${color}` }} />
        <span style={{ fontSize: "11px", color: "#64748B" }}>Live signal</span>
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <main style={{ fontFamily: "'Inter', -apple-system, sans-serif", background: "#F8FAFC" }}>

      {/* ── HERO ─────────────────────────────────────────── */}
      <section style={{
        background: "linear-gradient(160deg, #0A1628 0%, #0F2347 60%, #0A1628 100%)",
        padding: "80px 24px 100px",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Grid background */}
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: "linear-gradient(rgba(37,99,235,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(37,99,235,0.06) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }} />

        <div style={{ maxWidth: "1100px", margin: "0 auto", position: "relative" }}>
          {/* Eyebrow */}
          <div style={{
            display: "inline-flex", alignItems: "center", gap: "8px",
            background: "rgba(37,99,235,0.15)", border: "1px solid rgba(37,99,235,0.3)",
            borderRadius: "100px", padding: "6px 16px", marginBottom: "36px",
          }}>
            <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#2563EB" }} />
            <span style={{ fontSize: "12px", color: "#93C5FD", letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 500 }}>
              Decision Intelligence for the C-Suite
            </span>
          </div>

          {/* Headline */}
          <h1 style={{
            fontSize: "clamp(36px, 5vw, 64px)",
            fontWeight: "800",
            color: "#F8FAFC",
            lineHeight: "1.1",
            letterSpacing: "-0.03em",
            maxWidth: "820px",
            marginBottom: "24px",
          }}>
            Your ERP tells you<br />
            <span style={{ color: "#2563EB" }}>what happened.</span><br />
            We tell you what&apos;s coming —<br />
            and what to do about it.
          </h1>

          <p style={{
            fontSize: "18px", color: "#94A3B8", lineHeight: "1.7",
            maxWidth: "560px", marginBottom: "44px",
          }}>
            We connect your internal ERP data with external macro signals and predictive models
            to give your CFO, CEO and CRO answers they cannot get anywhere else — in under 60 seconds.
          </p>

          {/* CTAs */}
          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", marginBottom: "72px" }}>
            <Link href="/cfo" style={{
              background: "#2563EB", color: "#fff",
              padding: "14px 28px", borderRadius: "8px",
              fontWeight: "600", fontSize: "15px",
              textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "8px",
            }}>
              See the CFO Demo
              <span style={{ fontSize: "18px" }}>→</span>
            </Link>
            <a href="mailto:contact@csuite.ai" style={{
              background: "transparent", color: "#CBD5E1",
              padding: "14px 28px", borderRadius: "8px",
              fontWeight: "500", fontSize: "15px",
              textDecoration: "none", border: "1px solid rgba(255,255,255,0.12)",
              display: "inline-flex", alignItems: "center", gap: "8px",
            }}>
              Book a Discovery Call
            </a>
          </div>

          {/* Live signal strip */}
          <div style={{ marginBottom: "12px" }}>
            <p style={{ fontSize: "11px", color: "#475569", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "16px" }}>
              Platform signals — updating live
            </p>
            <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
              {signals.map(s => <LiveSignal key={s.label} {...s} />)}
            </div>
          </div>
        </div>
      </section>

      {/* ── PROBLEM ──────────────────────────────────────── */}
      <section style={{ padding: "96px 24px", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
            The Gap
          </p>
          <h2 style={{ fontSize: "clamp(28px, 3.5vw, 44px)", fontWeight: "800", color: "#0A1628", letterSpacing: "-0.02em", lineHeight: "1.2", maxWidth: "600px", marginBottom: "64px" }}>
            Every CFO knows the answers aren&apos;t in the ERP.
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px" }}>
            {[
              {
                q: "What will our cash position be in 90 days?",
                erp: "A static roll-forward built in Excel — already stale.",
                us: "Probabilistic P10/P50/P90 forecast, updated weekly from your AP/AR data.",
              },
              {
                q: "Are we heading toward a covenant breach?",
                erp: "DSCR from last month's close. No trend. No alert.",
                us: "Live DSCR trend vs your covenant floor, stress-tested at +100 and +200bps.",
              },
              {
                q: "Which customers will default before they miss a payment?",
                erp: "An AR aging report. Useful only after the damage is done.",
                us: "XGBoost 60-day default probability with SHAP-explained drivers per customer.",
              },
            ].map((item, i) => (
              <div key={i} style={{
                background: "#fff",
                border: "1px solid #E2E8F0",
                borderRadius: "16px",
                padding: "32px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
              }}>
                <p style={{ fontSize: "17px", fontWeight: "700", color: "#0F172A", lineHeight: "1.4", marginBottom: "24px" }}>
                  &ldquo;{item.q}&rdquo;
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div style={{ background: "#FEF2F2", borderRadius: "8px", padding: "14px 16px" }}>
                    <p style={{ fontSize: "11px", color: "#DC2626", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "6px" }}>Your ERP today</p>
                    <p style={{ fontSize: "14px", color: "#7F1D1D", lineHeight: "1.5" }}>{item.erp}</p>
                  </div>
                  <div style={{ background: "#EFF6FF", borderRadius: "8px", padding: "14px 16px" }}>
                    <p style={{ fontSize: "11px", color: "#2563EB", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "6px" }}>With our platform</p>
                    <p style={{ fontSize: "14px", color: "#1E3A8A", lineHeight: "1.5" }}>{item.us}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── APPROACH ─────────────────────────────────────── */}
      <section style={{ padding: "96px 24px", background: "#0A1628" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
            Our Approach
          </p>
          <h2 style={{ fontSize: "clamp(28px, 3.5vw, 44px)", fontWeight: "800", color: "#F8FAFC", letterSpacing: "-0.02em", lineHeight: "1.2", maxWidth: "700px", marginBottom: "16px" }}>
            Platform-agnostic. Built on the medallion architecture. Designed to minimise cost.
          </h2>
          <p style={{ fontSize: "16px", color: "#64748B", maxWidth: "580px", lineHeight: "1.7", marginBottom: "64px" }}>
            We meet you where you are. Whether you run SAP, Oracle, Dynamics or a custom ERP —
            we layer Azure Data Factory, Data Lake, Azure SQL and Power BI on top, and introduce
            Microsoft Fabric only when the economics justify it.
          </p>

          {/* Pipeline diagram */}
          <div style={{ display: "flex", alignItems: "center", gap: "0", flexWrap: "wrap", marginBottom: "64px" }}>
            {[
              { label: "Your ERP", sub: "SAP · Oracle · Dynamics · Custom", icon: "🗄️" },
              { label: "Azure ADF", sub: "Ingest & orchestrate", icon: "⚙️" },
              { label: "Data Lake", sub: "Bronze · Silver · Gold", icon: "🏔️" },
              { label: "Azure SQL", sub: "Serving layer", icon: "🛢️" },
              { label: "Power BI", sub: "Embedded dashboards", icon: "📊" },
            ].map((step, i, arr) => (
              <div key={i} style={{ display: "flex", alignItems: "center" }}>
                <div style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "12px",
                  padding: "20px 24px",
                  textAlign: "center",
                  minWidth: "140px",
                }}>
                  <div style={{ fontSize: "28px", marginBottom: "8px" }}>{step.icon}</div>
                  <div style={{ fontSize: "14px", fontWeight: "700", color: "#F1F5F9", marginBottom: "4px" }}>{step.label}</div>
                  <div style={{ fontSize: "11px", color: "#64748B" }}>{step.sub}</div>
                </div>
                {i < arr.length - 1 && (
                  <div style={{ padding: "0 8px", color: "#1D4ED8", fontSize: "20px", fontWeight: "300" }}>→</div>
                )}
              </div>
            ))}
          </div>

          {/* 4 pillars */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "24px" }}>
            {[
              { title: "Know where you stand", desc: "Real-time financial health across cash, margin, covenant, and credit risk — in one view.", accent: "#2563EB" },
              { title: "See what's coming", desc: "Chronos and XGBoost models give you probabilistic forecasts, not point estimates.", accent: "#7C3AED" },
              { title: "Know what to do", desc: "Every dashboard surfaces a recommended action — not just a number.", accent: "#059669" },
              { title: "Macro-aware", desc: "BoC rates, yield curve, StatCan data, and TSX sector rotation baked in — for free.", accent: "#F59E0B" },
            ].map((p, i) => (
              <div key={i} style={{
                borderTop: `3px solid ${p.accent}`,
                padding: "28px 0 0",
              }}>
                <h3 style={{ fontSize: "16px", fontWeight: "700", color: "#F1F5F9", marginBottom: "10px" }}>{p.title}</h3>
                <p style={{ fontSize: "14px", color: "#64748B", lineHeight: "1.6" }}>{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── DEMOS ────────────────────────────────────────── */}
      <section style={{ padding: "96px 24px", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
            Live Demos
          </p>
          <h2 style={{ fontSize: "clamp(28px, 3.5vw, 44px)", fontWeight: "800", color: "#0A1628", letterSpacing: "-0.02em", lineHeight: "1.2", marginBottom: "16px" }}>
            See it running on real data.
          </h2>
          <p style={{ fontSize: "16px", color: "#64748B", maxWidth: "520px", lineHeight: "1.7", marginBottom: "56px" }}>
            Built on a live Azure SQL database. Every number you see is computed from actual ERP transactions, macro API feeds, and ML models running in production.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px" }}>
            {/* CFO Demo */}
            <div style={{
              background: "#0A1628",
              borderRadius: "20px",
              padding: "40px",
              position: "relative",
              overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", top: 0, right: 0, width: "200px", height: "200px",
                background: "radial-gradient(circle, rgba(37,99,235,0.2) 0%, transparent 70%)",
                pointerEvents: "none",
              }} />
              <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
                Available Now
              </p>
              <h3 style={{ fontSize: "24px", fontWeight: "800", color: "#F8FAFC", marginBottom: "16px", lineHeight: "1.3" }}>
                CFO Intelligence App
              </h3>
              <p style={{ fontSize: "14px", color: "#64748B", lineHeight: "1.7", marginBottom: "32px" }}>
                8 pages. 12 questions your ERP cannot answer. Cash forecasting, covenant tracking,
                customer default scoring, macro signals — all embedded in one dashboard.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "36px" }}>
                {["13-week probabilistic cash forecast", "DSCR trend vs covenant floor", "60-day customer default probability", "TSX sector rotation signal"].map(f => (
                  <div key={f} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: "rgba(37,99,235,0.2)", border: "1px solid #2563EB", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#2563EB" }} />
                    </div>
                    <span style={{ fontSize: "13px", color: "#94A3B8" }}>{f}</span>
                  </div>
                ))}
              </div>
              <Link href="/cfo" style={{
                background: "#2563EB", color: "#fff",
                padding: "13px 24px", borderRadius: "8px",
                fontWeight: "600", fontSize: "14px",
                textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "8px",
              }}>
                Launch CFO Demo →
              </Link>
            </div>

            {/* Macro Demo */}
            <div style={{
              background: "#fff",
              border: "1px solid #E2E8F0",
              borderRadius: "20px",
              padding: "40px",
              position: "relative",
            }}>
              <p style={{ fontSize: "12px", color: "#F59E0B", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
                Coming Soon
              </p>
              <h3 style={{ fontSize: "24px", fontWeight: "800", color: "#0F172A", marginBottom: "16px", lineHeight: "1.3" }}>
                Macro Intelligence Dashboard
              </h3>
              <p style={{ fontSize: "14px", color: "#64748B", lineHeight: "1.7", marginBottom: "32px" }}>
                BoC policy trajectory, yield curve analysis, CPI vs IPPI compression, TSX sector rotation —
                translated into a capital allocation posture your board can act on.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "36px" }}>
                {["Bank of Canada rate trajectory", "Yield curve recession signal", "Cyclical vs defensive rotation", "Macro cycle phase classification"].map(f => (
                  <div key={f} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: "#FEF9C3", border: "1px solid #F59E0B", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#F59E0B" }} />
                    </div>
                    <span style={{ fontSize: "13px", color: "#64748B" }}>{f}</span>
                  </div>
                ))}
              </div>
              <div style={{
                background: "#F8FAFC", border: "1px solid #E2E8F0",
                borderRadius: "8px", padding: "13px 24px",
                fontSize: "14px", color: "#94A3B8", fontWeight: "500",
                display: "inline-block",
              }}>
                In Development
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── ROI STRIP ────────────────────────────────────── */}
      <section style={{ padding: "80px 24px", background: "#2563EB" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "48px", alignItems: "center" }}>
            <div>
              <h2 style={{ fontSize: "clamp(24px, 3vw, 36px)", fontWeight: "800", color: "#fff", lineHeight: "1.3", letterSpacing: "-0.02em" }}>
                The ROI case writes itself.
              </h2>
              <p style={{ fontSize: "15px", color: "#BFDBFE", lineHeight: "1.6", marginTop: "12px" }}>
                Enterprise BI platforms charge for what we deliver at infrastructure cost.
              </p>
            </div>
            {[
              { number: "~$150", unit: "CAD/month", label: "Full infrastructure cost — ADF, Data Lake, Azure SQL, Power BI Pro" },
              { number: "$200K–$500K", unit: "per year", label: "Comparable enterprise platform cost (Anaplan, Adaptive, SAP Analytics)" },
              { number: "60 sec", unit: "or less", label: "Time for a CFO to answer any of 12 questions the ERP cannot touch" },
            ].map((stat, i) => (
              <div key={i} style={{ borderLeft: "3px solid rgba(255,255,255,0.2)", paddingLeft: "28px" }}>
                <div style={{ fontSize: "clamp(32px, 4vw, 48px)", fontWeight: "800", color: "#fff", letterSpacing: "-0.03em", lineHeight: "1" }}>
                  {stat.number}
                </div>
                <div style={{ fontSize: "13px", color: "#93C5FD", fontWeight: 500, marginBottom: "8px" }}>{stat.unit}</div>
                <div style={{ fontSize: "13px", color: "#BFDBFE", lineHeight: "1.5" }}>{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────── */}
      <section style={{ padding: "96px 24px", background: "#0A1628", textAlign: "center" }}>
        <div style={{ maxWidth: "640px", margin: "0 auto" }}>
          <h2 style={{ fontSize: "clamp(28px, 3.5vw, 44px)", fontWeight: "800", color: "#F8FAFC", letterSpacing: "-0.02em", lineHeight: "1.2", marginBottom: "20px" }}>
            Ready to see what your data can tell you?
          </h2>
          <p style={{ fontSize: "16px", color: "#64748B", lineHeight: "1.7", marginBottom: "44px" }}>
            We start with a 45-minute discovery call. No slides. We connect to your data and show you three insights your team has never seen before.
          </p>
          <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
            <a href="mailto:contact@csuite.ai" style={{
              background: "#2563EB", color: "#fff",
              padding: "16px 36px", borderRadius: "8px",
              fontWeight: "700", fontSize: "16px",
              textDecoration: "none",
            }}>
              Book a Discovery Call
            </a>
            <Link href="/cfo" style={{
              background: "transparent", color: "#CBD5E1",
              padding: "16px 36px", borderRadius: "8px",
              fontWeight: "500", fontSize: "16px",
              textDecoration: "none", border: "1px solid rgba(255,255,255,0.12)",
            }}>
              Explore the Demo
            </Link>
          </div>
        </div>
      </section>

    </main>
  );
}

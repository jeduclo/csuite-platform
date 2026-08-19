"use client";
import Link from "next/link";

export default function AboutPage() {
  return (
    <main style={{ fontFamily: "'Inter', -apple-system, sans-serif", background: "#F8FAFC" }}>

      {/* HERO */}
      <section style={{
        background: "linear-gradient(160deg, #0A1628 0%, #0F2347 60%, #0A1628 100%)",
        padding: "80px 24px 100px",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: "linear-gradient(rgba(37,99,235,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(37,99,235,0.06) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }} />
        <div style={{ maxWidth: "1100px", margin: "0 auto", position: "relative" }}>
          <div style={{ display: "flex", gap: "64px", alignItems: "flex-start", flexWrap: "wrap" }}>
            <div style={{
              width: "160px", height: "160px", borderRadius: "50%", flexShrink: 0,
              background: "linear-gradient(135deg, #1D4ED8, #7C3AED)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "56px", fontWeight: "800", color: "#fff",
              border: "4px solid rgba(255,255,255,0.1)",
            }}>
              JD
            </div>
            <div style={{ flex: 1, minWidth: "280px" }}>
              <div style={{
                display: "inline-flex", alignItems: "center", gap: "8px",
                background: "rgba(37,99,235,0.15)", border: "1px solid rgba(37,99,235,0.3)",
                borderRadius: "100px", padding: "6px 16px", marginBottom: "20px",
              }}>
                <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#2563EB" }} />
                <span style={{ fontSize: "12px", color: "#93C5FD", letterSpacing: "0.06em", textTransform: "uppercase", fontWeight: 500 }}>
                  Founder & Principal Architect
                </span>
              </div>
              <h1 style={{
                fontSize: "clamp(36px, 4vw, 56px)", fontWeight: "800",
                color: "#F8FAFC", lineHeight: "1.1", letterSpacing: "-0.03em", marginBottom: "16px",
              }}>
                Jean Duclos
              </h1>
              <p style={{ fontSize: "18px", color: "#94A3B8", lineHeight: "1.7", maxWidth: "600px", marginBottom: "32px" }}>
                BI Architect and Principal Consultant with 16+ years building analytical platforms
                that turn raw ERP data into decisions C-suite executives can act on — in minutes, not months.
              </p>
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                {["PhD · Environmental Economics", "MSc · Big Data Analytics", "Bilingual EN/FR"].map(tag => (
                  <div key={tag} style={{
                    background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "100px", padding: "6px 16px",
                    fontSize: "13px", color: "#CBD5E1", fontWeight: 500,
                  }}>{tag}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* STORY */}
      <section style={{ padding: "96px 24px", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "780px", margin: "0 auto" }}>
          <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
            Why I Built This
          </p>
          <h2 style={{ fontSize: "clamp(28px, 3vw, 40px)", fontWeight: "800", color: "#0A1628", letterSpacing: "-0.02em", lineHeight: "1.2", marginBottom: "32px" }}>
            Every CFO I&apos;ve worked with had the same problem.
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "20px", fontSize: "17px", color: "#334155", lineHeight: "1.8" }}>
            <p>
              After 16 years designing analytical platforms for mid-market companies across the UK and Canada,
              I kept seeing the same gap: finance teams drowning in ERP reports that told them what happened last month,
              while the questions that actually mattered — cash in 90 days, which customers will default, are we heading for a covenant breach —
              had no answer.
            </p>
            <p>
              I built C-Suite Intelligence to close that gap. Not with another dashboard layer on top of Power BI,
              but with a platform that connects your ERP transactions to external macro signals, runs probabilistic forecasts,
              and surfaces a recommended action — in under 60 seconds.
            </p>
            <p>
              The architecture is designed to be deployed at a fraction of the cost of enterprise alternatives like Anaplan or Adaptive,
              using the medallion pattern on Azure infrastructure your team already understands.
            </p>
          </div>
        </div>
      </section>

      {/* CREDENTIALS */}
      <section style={{ padding: "96px 24px", background: "#0A1628" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
            Background
          </p>
          <h2 style={{ fontSize: "clamp(28px, 3vw, 40px)", fontWeight: "800", color: "#F8FAFC", letterSpacing: "-0.02em", lineHeight: "1.2", marginBottom: "56px" }}>
            Built on 16 years of enterprise delivery.
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "32px" }}>
            {[
              { icon: "🏗️", title: "Architecture-First", desc: "Every engagement starts with structured discovery workshops with the CFO, CRO, and DPO — before a single line of code is written. The architecture is co-designed with the client." },
              { icon: "📊", title: "End-to-End Delivery", desc: "From ingestion (Salesforce, SAP, ERP REST APIs) to governed semantic models in Microsoft Fabric and Power BI — with RLS, OLS, and Purview lineage throughout." },
              { icon: "🤖", title: "Predictive Modelling", desc: "XGBoost, Random Forest, and time-series forecasting with SHAP explainability — translating ML outputs into narratives executives can present to their board." },
              { icon: "🔒", title: "Governance & Compliance", desc: "Microsoft Purview implementations covering GDPR right-to-erasure, DLP, sensitivity labels, and ICO-ready audit trails. Clients have passed external audits with zero findings." },
              { icon: "🌎", title: "Macro Intelligence", desc: "PhD-level grounding in economics applied to real business problems — BoC rate trajectories, yield curve signals, and TSX sector rotation translated into capital allocation decisions." },
              { icon: "🤝", title: "Board-Level Communication", desc: "Experienced presenting architecture and compliance postures to executive committees and boards. Bilingual delivery in English and French." },
            ].map((item, i) => (
              <div key={i} style={{
                background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "16px", padding: "32px",
              }}>
                <div style={{ fontSize: "32px", marginBottom: "16px" }}>{item.icon}</div>
                <h3 style={{ fontSize: "17px", fontWeight: "700", color: "#F1F5F9", marginBottom: "10px" }}>{item.title}</h3>
                <p style={{ fontSize: "14px", color: "#64748B", lineHeight: "1.7" }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* OUTCOMES */}
      <section style={{ padding: "96px 24px", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
            Selected Outcomes
          </p>
          <h2 style={{ fontSize: "clamp(28px, 3vw, 40px)", fontWeight: "800", color: "#0A1628", letterSpacing: "-0.02em", lineHeight: "1.2", marginBottom: "56px" }}>
            What this looks like in practice.
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {[
              {
                client: "Multi-Site Retail Chain · 14 Locations · UK",
                outcome: "Markdown decisions moved from a two-week lag to same-day. Overstock write-downs fell 18%. Client passed its ICO-facing GDPR audit with zero findings.",
                tags: ["Microsoft Fabric", "Power BI", "Purview", "GDPR"],
              },
              {
                client: "B2B National Distributor · 6 Regions · UK",
                outcome: "Cross-regional pipeline consolidation reduced from 5 days to hours. XGBoost churn model with SHAP explanations surfaced directly in account-manager reports.",
                tags: ["Salesforce Integration", "XGBoost", "SHAP", "RLS/OLS"],
              },
              {
                client: "C-Suite Intelligence Platform · Canada",
                outcome: "File-based architecture delivering 12 CFO-grade answers — 13-week cash forecast, covenant breach alerts, customer default probability — at ~$150/month infrastructure cost.",
                tags: ["Dash", "Python", "Parquet", "Next.js"],
              },
            ].map((item, i) => (
              <div key={i} style={{
                background: "#fff", border: "1px solid #E2E8F0", borderRadius: "16px",
                padding: "32px", display: "flex", gap: "32px", flexWrap: "wrap",
                boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
              }}>
                <div style={{ flex: 1, minWidth: "200px" }}>
                  <p style={{ fontSize: "12px", color: "#64748B", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: "8px" }}>
                    {item.client}
                  </p>
                  <p style={{ fontSize: "16px", color: "#0F172A", lineHeight: "1.7" }}>{item.outcome}</p>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "flex-start", minWidth: "200px" }}>
                  {item.tags.map(tag => (
                    <div key={tag} style={{
                      background: "#EFF6FF", border: "1px solid #BFDBFE",
                      borderRadius: "100px", padding: "4px 12px",
                      fontSize: "12px", color: "#1D4ED8", fontWeight: 500,
                    }}>{tag}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "96px 24px", background: "#0A1628", textAlign: "center" }}>
        <div style={{ maxWidth: "640px", margin: "0 auto" }}>
          <h2 style={{ fontSize: "clamp(28px, 3.5vw, 44px)", fontWeight: "800", color: "#F8FAFC", letterSpacing: "-0.02em", lineHeight: "1.2", marginBottom: "20px" }}>
            Let&apos;s talk about your data.
          </h2>
          <p style={{ fontSize: "16px", color: "#64748B", lineHeight: "1.7", marginBottom: "44px" }}>
            A 45-minute discovery call. No slides. We connect to your data and show you three insights your team has never seen before.
          </p>
          <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
            <a href="mailto:contact@csuite.ai" style={{
              background: "#2563EB", color: "#fff",
              padding: "16px 36px", borderRadius: "8px",
              fontWeight: "700", fontSize: "16px", textDecoration: "none",
            }}>
              Book a Discovery Call
            </a>
            <Link href="/cfo" style={{
              background: "transparent", color: "#CBD5E1",
              padding: "16px 36px", borderRadius: "8px",
              fontWeight: "500", fontSize: "16px",
              textDecoration: "none", border: "1px solid rgba(255,255,255,0.12)",
            }}>
              See the Demo
            </Link>
          </div>
        </div>
      </section>

    </main>
  );
}

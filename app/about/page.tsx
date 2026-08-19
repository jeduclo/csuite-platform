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
                Jean Duclos, PhD
              </h1>
              <p style={{ fontSize: "18px", color: "#94A3B8", lineHeight: "1.7", maxWidth: "600px", marginBottom: "32px" }}>
                BI Architect and Principal Consultant with 16+ years building analytical platforms
                that turn raw ERP data into decisions C-suite executives can act on — in minutes, not months.
                Professor of Macroeconomics and Computational Macro-Strategy at Dawson College, Montréal.
              </p>
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                {["PhD · Environmental Economics", "MSc · Big Data Analytics", "Professor · Dawson College", "Bilingual EN/FR"].map(tag => (
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
              Teaching macroeconomics and computational macro-strategy at Dawson College sharpened my conviction
              that the tools to answer these questions already exist — they just haven&apos;t been assembled for the mid-market CFO.
              I built C-Suite Intelligence to close that gap.
            </p>
            <p>
              The architecture selects the right tool for each layer of the problem — dlt for schema-resilient ingestion,
              DuckDB for cost-efficient transformation, dbt for governed Gold models, XGBoost and Chronos for prediction —
              and introduces Microsoft Fabric or ADF only when the economics justify it.
              The result is enterprise-grade decision intelligence at infrastructure cost.
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
              { icon: "📊", title: "End-to-End Delivery", desc: "From ingestion (Salesforce, SAP, ERP REST APIs) through Bronze/Silver/Gold medallion layers to governed Power BI semantic models — with RLS, OLS, and full lineage throughout." },
              { icon: "🤖", title: "Predictive Modelling", desc: "XGBoost, Random Forest, and Chronos time-series forecasting with SHAP explainability — translating ML outputs into narratives executives can present to their board." },
              { icon: "🔒", title: "Governance & Compliance", desc: "Microsoft Purview implementations covering GDPR right-to-erasure, DLP, sensitivity labels, and ICO-ready audit trails. Clients have passed external audits with zero findings." },
              { icon: "🌎", title: "Macro Intelligence", desc: "PhD-level grounding in economics applied to real business problems — BoC rate trajectories, yield curve signals, and TSX sector rotation translated into capital allocation decisions." },
              { icon: "🎓", title: "Academic Rigour", desc: "Professor of Macroeconomics and Computational Macro-Strategy at Dawson College, Montréal. Every model delivered to clients is grounded in the same rigour taught in the classroom." },
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

      {/* HOW WE ANSWER THE QUESTIONS */}
      <section style={{ padding: "96px 24px", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <p style={{ fontSize: "12px", color: "#2563EB", letterSpacing: "0.1em", textTransform: "uppercase", fontWeight: 600, marginBottom: "16px" }}>
            How We Answer the Questions
          </p>
          <h2 style={{ fontSize: "clamp(28px, 3vw, 40px)", fontWeight: "800", color: "#0A1628", letterSpacing: "-0.02em", lineHeight: "1.2", marginBottom: "16px" }}>
            The right tool for each layer. No over-engineering.
          </h2>
          <p style={{ fontSize: "16px", color: "#64748B", lineHeight: "1.7", maxWidth: "680px", marginBottom: "56px" }}>
            We select the architecture based on what the question requires — not on vendor relationships.
            ADF and Microsoft Fabric are introduced only when the volume or governance requirements justify the cost.
          </p>

          {/* Pipeline visual */}
          <div style={{
            background: "#0A1628", borderRadius: "20px", padding: "48px",
            marginBottom: "56px", overflowX: "auto",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0", minWidth: "700px", justifyContent: "center" }}>
              {[
                { label: "ERP / Macro APIs", sub: "Your source systems", icon: "🗄️", color: "#2563EB" },
                { label: "ADLS Gen2 Bronze", sub: "dlt · schema auto-detect", icon: "📥", color: "#7C3AED" },
                { label: "ADLS Gen2 Silver", sub: "DuckDB · ACI compute", icon: "⚙️", color: "#059669" },
                { label: "Gold Lakehouse", sub: "dbt · models & tests", icon: "🏔️", color: "#F59E0B" },
                { label: "Power BI", sub: "XGBoost · Chronos · ML", icon: "📊", color: "#2563EB" },
              ].map((step, i, arr) => (
                <div key={i} style={{ display: "flex", alignItems: "center" }}>
                  <div style={{
                    background: "rgba(255,255,255,0.04)", border: `1px solid ${step.color}40`,
                    borderRadius: "12px", padding: "20px", textAlign: "center", minWidth: "130px",
                  }}>
                    <div style={{ fontSize: "24px", marginBottom: "8px" }}>{step.icon}</div>
                    <div style={{ fontSize: "12px", fontWeight: "700", color: step.color, marginBottom: "4px" }}>{step.label}</div>
                    <div style={{ fontSize: "10px", color: "#64748B" }}>{step.sub}</div>
                  </div>
                  {i < arr.length - 1 && (
                    <div style={{ padding: "0 6px", color: "#334155", fontSize: "18px" }}>→</div>
                  )}
                </div>
              ))}
            </div>
            <p style={{ textAlign: "center", fontSize: "12px", color: "#475569", marginTop: "24px" }}>
              ADF replaces dlt · Microsoft Fabric replaces ADLS + DuckDB + Azure SQL — when volume or governance economics justify it
            </p>
          </div>

          {/* Questions answered */}
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {[
              {
                q: "What will our cash position be in 90 days?",
                how: "AP/AR transactions ingested via dlt into Bronze, cleaned in DuckDB Silver, modelled in dbt Gold. Chronos runs probabilistic P10/P50/P90 forecasts on the Gold layer. Output surfaced in Power BI in under 60 seconds.",
                tags: ["dlt", "DuckDB", "dbt", "Chronos", "Power BI"],
              },
              {
                q: "Are we heading toward a covenant breach?",
                how: "DSCR computed from Gold financial models updated on each ERP ingestion cycle. Stress-tested at +100 and +200bps using scenario parameters stored in dbt. Alert threshold breaches trigger Power Automate notifications before the close.",
                tags: ["dbt", "Azure SQL", "Power BI", "Power Automate"],
              },
              {
                q: "Which customers will default before they miss a payment?",
                how: "AR aging, payment history, and sector macro signals joined in the Gold layer. XGBoost ensemble scores every active account weekly with SHAP waterfall explanations surfaced directly in the account-manager view.",
                tags: ["XGBoost", "SHAP", "dbt Gold", "Macro APIs"],
              },
              {
                q: "Where is macro risk entering our cost structure?",
                how: "BoC rate trajectory, CPI/IPPI compression, and TSX sector rotation ingested from public APIs alongside your ERP data. dbt models link external signals to your margin and covenant metrics — no manual Excel overlays.",
                tags: ["BoC API", "StatCan", "FRED", "dbt", "Power BI"],
              },
            ].map((item, i) => (
              <div key={i} style={{
                background: "#fff", border: "1px solid #E2E8F0", borderRadius: "16px",
                padding: "32px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
              }}>
                <p style={{ fontSize: "17px", fontWeight: "700", color: "#0F172A", lineHeight: "1.4", marginBottom: "12px" }}>
                  &ldquo;{item.q}&rdquo;
                </p>
                <p style={{ fontSize: "15px", color: "#334155", lineHeight: "1.7", marginBottom: "16px" }}>{item.how}</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
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

"use client";

// Replace DASH_URL with your Render app URL once deployed
// e.g. https://cfo-intelligence-dash.onrender.com
const DASH_URL = process.env.NEXT_PUBLIC_DASH_URL || "https://cfo-intelligence-dash.onrender.com";

export default function CFOPage() {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0A1628" }}>
      {/* Header */}
      <div style={{
        padding: "16px 32px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div>
          <h1 style={{ fontSize: "18px", fontWeight: "800", color: "#F8FAFC", margin: 0 }}>
            CFO Intelligence App
          </h1>
          <p style={{ fontSize: "12px", color: "#64748B", margin: "4px 0 0", fontStyle: "italic" }}>
            &quot;Your ERP is a rearview mirror. This is the windshield.&quot;
          </p>
        </div>
        <a
          href="mailto:contact@csuite.ai"
          style={{
            background: "#2563EB", color: "#fff",
            padding: "10px 20px", borderRadius: "8px",
            fontWeight: "600", fontSize: "13px",
            textDecoration: "none",
          }}
        >
          Book a Demo →
        </a>
      </div>

      {/* Dash app iframe */}
      <iframe
        src={DASH_URL}
        style={{ flex: 1, border: "none", width: "100%" }}
        title="CFO Intelligence Dashboard"
        loading="eager"
      />
    </div>
  );
}

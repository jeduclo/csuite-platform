"use client";

const DASH_URL = "https://csuite-platform-production.up.railway.app";

export default function CFOPage() {
  return (
    <iframe
      src={DASH_URL}
      style={{
        position: "fixed",
        top: "53px",
        left: 0,
        width: "100vw",
        height: "calc(100vh - 53px)",
        border: "none",
        display: "block",
      }}
      title="CFO Intelligence Dashboard"
      loading="eager"
    />
  );
}

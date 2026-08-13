"use client";

const DASH_URL = "https://csuite-platform-production.up.railway.app";

export default function CFOPage() {
  return (
    <iframe
      src={DASH_URL}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        border: "none",
        display: "block",
      }}
      title="CFO Intelligence Dashboard"
      loading="eager"
    />
  );
}

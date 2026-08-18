"use client";

const MACRO_URL = "https://blissful-celebration-production-39c2.up.railway.app";

export default function MacroPage() {
  return (
    <iframe
      src={MACRO_URL}
      style={{
        position: "fixed",
        top: "53px",
        left: 0,
        width: "100vw",
        height: "calc(100vh - 53px)",
        border: "none",
        display: "block",
      }}
      title="Macro Intelligence Dashboard"
      loading="eager"
    />
  );
}

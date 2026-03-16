import React from "react";

export default function Spinner() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "48px 0" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
        <div style={{
          width: 36, height: 36, borderRadius: "50%",
          border: "3px solid #E2E8F0",
          borderTopColor: "#3B5BDB",
          animation: "spin 0.7s linear infinite",
        }} />
        <span style={{ fontSize: 13, color: "#94A3B8", fontWeight: 500 }}>Загружаем…</span>
      </div>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

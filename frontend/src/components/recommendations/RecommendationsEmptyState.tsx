import React from "react";
import { Link } from "react-router-dom";
import { IconBriefcase } from "./RecIcons";

export default function RecommendationsEmptyState() {
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "2px dashed #D7E0EE",
        borderRadius: 28,
        padding: 40,
        textAlign: "center",
        maxWidth: 560,
        margin: "0 auto",
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 18,
          background: "#F8FAFF",
          border: "1px solid #E6EAF2",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 20px",
          color: "#5B5CEB",
        }}
      >
        <IconBriefcase size={28} />
      </div>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: "#0F172A", margin: "0 0 10px" }}>Рекомендации пока не готовы</h2>
      <p style={{ fontSize: 16, lineHeight: "24px", color: "#64748B", margin: "0 0 28px" }}>
        Заполните профиль и навыки, чтобы получить персональный подбор вакансий
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
        <Link
          to="/profile"
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "12px 22px",
            background: "#5B5CEB",
            color: "#fff",
            borderRadius: 18,
            fontWeight: 600,
            fontSize: 15,
            textDecoration: "none",
            boxShadow: "0 8px 20px rgba(91, 92, 235, 0.22)",
          }}
        >
          Обновить профиль
        </Link>
        <Link
          to="/vacancies"
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "12px 22px",
            background: "#FFFFFF",
            color: "#4F46E5",
            border: "1px solid #E6EAF2",
            borderRadius: 18,
            fontWeight: 600,
            fontSize: 15,
            textDecoration: "none",
          }}
        >
          Посмотреть вакансии
        </Link>
      </div>
    </div>
  );
}

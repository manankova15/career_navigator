import React from "react";
import { IconSparkles } from "./RecIcons";

interface Props {
  recommendationCount: number;
  bestMatchPercent: number | null;
  loading?: boolean;
}

export default function RecommendationsIntroHero({ recommendationCount, bestMatchPercent, loading }: Props) {
  const showTopMatch = bestMatchPercent != null && recommendationCount > 0;

  return (
    <section
      className="recommendations-intro-hero"
      style={{
        position: "relative",
        overflow: "hidden",
        background: "linear-gradient(135deg, #FFFFFF 0%, #F7FAFF 100%)",
        border: "1px solid #E6EAF2",
        borderRadius: 30,
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.05)",
        padding: 30,
      }}
    >
      <div
        aria-hidden
        style={{
          position: "absolute",
          top: "-40%",
          right: "-15%",
          width: "55%",
          height: "120%",
          background: "radial-gradient(circle, rgba(91,92,235,0.10) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        aria-hidden
        style={{
          position: "absolute",
          bottom: "-30%",
          left: "-10%",
          width: "50%",
          height: "100%",
          background: "radial-gradient(circle, rgba(6,182,212,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div
        className="recommendations-intro-grid"
        style={{
          position: "relative",
          zIndex: 1,
        }}
      >
        <div>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              background: "#EEF2FF",
              color: "#4338CA",
              border: "1px solid #C7D2FE",
              borderRadius: 999,
              padding: "8px 14px",
              fontSize: 13,
              fontWeight: 600,
              marginBottom: 18,
            }}
          >
            <IconSparkles size={16} />
            AI-подбор вакансий
          </span>
          <h1
            className="recommendations-page-title"
            style={{
              fontSize: 44,
              fontWeight: 700,
              lineHeight: "50px",
              color: "#0F172A",
              margin: "0 0 14px",
              letterSpacing: "-0.5px",
            }}
          >
            Рекомендации, подобранные под ваш профиль
          </h1>
          <p
            style={{
              fontSize: 18,
              fontWeight: 400,
              lineHeight: "28px",
              color: "#64748B",
              margin: "0 0 22px",
              maxWidth: 640,
            }}
          >
            Мы подобрали вакансии на основе ваших навыков, интересов и карьерного направления. Следите за совпадением и закрывайте пробелы, чтобы получать еще более точные предложения.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {["Персональный match", "Актуальные роли", "Анализ навыков"].map(label => (
              <span
                key={label}
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #E6EAF2",
                  color: "#64748B",
                  borderRadius: 999,
                  padding: "10px 14px",
                  fontSize: 14,
                  fontWeight: 500,
                }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>

        <div
          style={{
            background: "rgba(255,255,255,0.80)",
            backdropFilter: "blur(10px)",
            WebkitBackdropFilter: "blur(10px)",
            border: "1px solid rgba(230,234,242,0.92)",
            borderRadius: 24,
            padding: 22,
            display: "flex",
            flexDirection: "column",
            gap: 18,
            justifyContent: "center",
            alignSelf: "stretch",
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Ваш карьерный фокус
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {showTopMatch && (
              <div
                style={{
                  background: "#F8FAFF",
                  border: "1px solid #E6EAF2",
                  borderRadius: 18,
                  padding: 16,
                }}
              >
                <div style={{ fontSize: 13, color: "#64748B", fontWeight: 500, marginBottom: 6 }}>Топ match</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: "#0F172A" }}>
                  {loading ? "—" : `${bestMatchPercent}%`}
                </div>
              </div>
            )}
            <div
              style={{
                background: "#F8FAFF",
                border: "1px solid #E6EAF2",
                borderRadius: 18,
                padding: 16,
                gridColumn: showTopMatch ? undefined : "1 / -1",
              }}
            >
              <div style={{ fontSize: 13, color: "#64748B", fontWeight: 500, marginBottom: 6 }}>Рекомендаций</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#0F172A" }}>{loading ? "—" : recommendationCount}</div>
            </div>
          </div>
          <p style={{ fontSize: 14, lineHeight: "22px", color: "#64748B", margin: 0 }}>
            Чем выше совпадение, тем ближе вакансия к вашему текущему профилю
          </p>
        </div>
      </div>
    </section>
  );
}

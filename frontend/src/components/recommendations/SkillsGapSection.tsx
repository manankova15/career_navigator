import React from "react";
import { Link } from "react-router-dom";
import { SkillGap } from "../../api/recommendations";
import SkillGapItem from "./SkillGapItem";
import { IconBarChart3, IconTarget } from "./RecIcons";

const FILL_ROTATION = ["#5B5CEB", "#06B6D4", "#10B981"];

interface Props {
  gaps: SkillGap[];
}

export default function SkillsGapSection({ gaps }: Props) {
  if (gaps.length === 0) return null;

  const maxImportance = Math.max(...gaps.map(s => s.importance_score), 1);
  const topGap = gaps[0];

  return (
    <section
      className="skills-gap-analytics"
      style={{
        marginTop: 36,
        position: "relative",
        overflow: "hidden",
        background: "linear-gradient(180deg, #FFFFFF 0%, #FCFCFF 100%)",
        border: "1px solid #E6EAF2",
        borderRadius: 30,
        padding: 28,
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.05)",
      }}
    >
      <div
        aria-hidden
        style={{
          position: "absolute",
          top: "-20%",
          right: "-10%",
          width: "45%",
          height: "80%",
          background: "radial-gradient(circle, rgba(91,92,235,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        aria-hidden
        style={{
          position: "absolute",
          bottom: "-25%",
          left: "-5%",
          width: "40%",
          height: "70%",
          background: "radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div style={{ position: "relative", zIndex: 1 }}>
        <div style={{ marginBottom: 24 }}>
          <h2
            style={{
              fontSize: 30,
              fontWeight: 700,
              lineHeight: "36px",
              color: "#0F172A",
              margin: "0 0 8px",
              letterSpacing: "-0.3px",
            }}
          >
            Анализ пробелов в навыках
          </h2>
          <p style={{ fontSize: 18, fontWeight: 400, lineHeight: "28px", color: "#64748B", margin: 0, maxWidth: 720 }}>
            Навыки, которые чаще всего встречаются в рекомендованных вакансиях и помогут повысить ваш успех при найме, при этом не указаны в вашем профиле
          </p>
        </div>

        <div className="skills-gap-grid">
          <div
            style={{
              background: "#F8FAFF",
              border: "1px solid #E6EAF2",
              borderRadius: 24,
              padding: 22,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
              <span style={{ color: "#5B5CEB", display: "flex" }}>
                <IconTarget size={22} />
              </span>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Куда расти дальше
              </span>
            </div>

            {topGap && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#64748B", marginBottom: 6 }}>Топ навык</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: "#0F172A" }}>{topGap.skill_name}</div>
              </div>
            )}

            {topGap && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#64748B", marginBottom: 6 }}>Чаще всего встречается</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#4F46E5" }}>
                  в {topGap.frequency} {topGap.frequency === 1 ? "вакансии" : "вакансиях"} из подборки
                </div>
              </div>
            )}

            {gaps.length > 1 && (() => {
              const n = Math.min(gaps.length, 10) - 1;
              const word = n === 1 ? "навык" : n >= 2 && n <= 4 ? "навыка" : "навыков";
              return (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#64748B", marginBottom: 6 }}>Потенциал роста</div>
                  <div style={{ fontSize: 15, fontWeight: 500, color: "#0F172A", lineHeight: 1.5 }}>
                    Ещё {n} {word} в приоритете ниже
                  </div>
                </div>
              );
            })()}

            <Link
              to="/assessments"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "12px 20px",
                background: "#FFFFFF",
                border: "1px solid #E6EAF2",
                borderRadius: 16,
                color: "#4F46E5",
                fontWeight: 600,
                fontSize: 14,
                textDecoration: "none",
                boxShadow: "0 4px 14px rgba(15, 23, 42, 0.04)",
                transition: "background 0.2s ease, border-color 0.2s ease",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = "#F8FAFF";
                e.currentTarget.style.borderColor = "#C7D2FE";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = "#FFFFFF";
                e.currentTarget.style.borderColor = "#E6EAF2";
              }}
            >
              Перейти к заданиям
            </Link>
          </div>

          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <IconBarChart3 size={20} />
              <span style={{ fontSize: 14, fontWeight: 600, color: "#64748B" }}>Детализация по навыкам</span>
            </div>
            {gaps.slice(0, 10).map((sg, i) => (
              <SkillGapItem
                key={sg.skill_name}
                gap={sg}
                index={i}
                barWidthPercent={(sg.importance_score / maxImportance) * 100}
                fillColor={FILL_ROTATION[Math.min(i, FILL_ROTATION.length - 1)]}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listAssessments, AssessmentSummary, myAttempts, AttemptResult } from "../api/assessments";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";

const DIFF_CONFIG: Record<string, { label: string; bg: string; color: string }> = {
  easy:   { label: "Лёгкий",  bg: "#ECFDF5", color: "#059669" },
  medium: { label: "Средний", bg: "#FFFBEB", color: "#D97706" },
  hard:   { label: "Сложный", bg: "#FEF2F2", color: "#DC2626" },
};

export default function AssessmentsPage() {
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [attempts, setAttempts] = useState<AttemptResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([listAssessments(), myAttempts().catch(() => [])])
      .then(([a, att]) => { setAssessments(a); setAttempts(att); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function lastAttempt(id: string) {
    return attempts
      .filter(a => a.assessment_id === id)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "#0F172A", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
          Задания
        </h1>
        <p style={{ color: "#64748B", margin: 0, fontSize: 15 }}>
          Проверьте и прокачайте свои знания перед интервью
        </p>
      </div>

      {error && <ErrorBanner message={error} />}
      {loading && <Spinner />}

      {!loading && assessments.length === 0 && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "48px", textAlign: "center" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#0F172A" }}>Опубликованных заданий пока нет</div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
        {assessments.map(a => {
          const last = lastAttempt(a.id);
          const diff = DIFF_CONFIG[a.difficulty] ?? { label: a.difficulty, bg: "#F1F5F9", color: "#64748B" };

          return (
            <div key={a.id} className="hoverable-card" style={{
              background: "#fff",
              border: "1.5px solid #E2E8F0",
              borderRadius: 20,
              padding: "22px",
              display: "flex",
              flexDirection: "column",
              gap: 12,
              boxShadow: "0 1px 3px rgba(15,23,42,0.05)",
            }}>
              {/* Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                <div style={{ fontWeight: 700, color: "#0F172A", fontSize: 15, lineHeight: 1.3, flex: 1 }}>{a.title}</div>
                <span style={{ background: diff.bg, color: diff.color, fontSize: 11, fontWeight: 600, borderRadius: 999, padding: "3px 10px", whiteSpace: "nowrap", flexShrink: 0, marginLeft: 8 }}>
                  {diff.label}
                </span>
              </div>

              {/* Description */}
              {a.description && (
                <div style={{ fontSize: 13, color: "#64748B", lineHeight: 1.55 }}>{a.description}</div>
              )}

              {/* Tags */}
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <span style={{ background: "#EEF2FF", color: "#3B5BDB", fontSize: 11, fontWeight: 500, borderRadius: 999, padding: "3px 10px" }}>
                  {a.topic}
                </span>
                <span style={{ background: "#F1F5F9", color: "#64748B", fontSize: 11, borderRadius: 999, padding: "3px 10px" }}>
                  {a.item_count} вопросов
                </span>
                {a.related_skills.slice(0, 2).map(s => (
                  <span key={s} style={{ background: "#F1F5F9", color: "#64748B", fontSize: 11, borderRadius: 999, padding: "3px 10px" }}>
                    {s}
                  </span>
                ))}
              </div>

              {/* Last attempt result */}
              {last && (
                <div style={{
                  fontSize: 12, borderRadius: 10, padding: "8px 12px",
                  background: last.status === "in_progress" ? "#F0F4FF" : last.passed ? "#ECFDF5" : "#FFFBEB",
                  color: last.status === "in_progress" ? "#3B5BDB" : last.passed ? "#059669" : "#D97706",
                  border: "1.5px solid",
                  borderColor: last.status === "in_progress" ? "#C7D2FE" : last.passed ? "#A7F3D0" : "#FDE68A",
                  fontWeight: 500,
                }}>
                  {last.status === "in_progress"
                    ? "⏳ В процессе"
                    : `${last.passed ? "✓" : "○"} Последняя попытка: ${last.percentage.toFixed(0)}% — ${last.passed ? "Пройдено" : "Не пройдено"}`}
                </div>
              )}

              {/* Action button */}
              <button
                onClick={() => navigate(`/assessments/${a.id}`)}
                style={{
                  padding: "11px", background: "#3B5BDB", color: "#fff",
                  border: "none", borderRadius: 12, cursor: "pointer",
                  fontWeight: 700, fontSize: 14, marginTop: 4,
                  transition: "all 0.15s",
                  boxShadow: "0 2px 8px rgba(59,91,219,0.2)",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "#2F4AC2"; e.currentTarget.style.boxShadow = "0 4px 16px rgba(59,91,219,0.3)"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#3B5BDB"; e.currentTarget.style.boxShadow = "0 2px 8px rgba(59,91,219,0.2)"; }}
              >
                {last?.status === "in_progress" ? "Продолжить" : last ? "Пройти снова" : "Начать →"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

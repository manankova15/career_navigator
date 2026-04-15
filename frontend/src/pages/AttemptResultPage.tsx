import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAttempt, getAssessment, AttemptResult, AssessmentDetail, AssessmentItem, AnswerResult } from "../api/assessments";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";

const btnPrimary: React.CSSProperties = {
  padding: "11px 24px", background: "#3B5BDB", color: "#fff",
  border: "none", borderRadius: 12, cursor: "pointer", fontWeight: 700, fontSize: 14,
  boxShadow: "0 2px 8px rgba(59,91,219,0.25)", transition: "all 0.15s",
};
const btnSecondary: React.CSSProperties = {
  padding: "11px 24px", background: "#F1F5F9", color: "#334155",
  border: "1.5px solid #E2E8F0", borderRadius: 12, cursor: "pointer", fontWeight: 600, fontSize: 14,
  transition: "all 0.15s",
};

export default function AttemptResultPage() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState<AttemptResult | null>(null);
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [expandedHints, setExpandedHints] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!attemptId) return;
    getAttempt(attemptId)
      .then((a) => {
        setAttempt(a);
        if (a.status === "in_progress") {
          setError("Попытка ещё не завершена. Продолжить можно со страницы задания.");
          return;
        }
        return getAssessment(a.assessment_id).then(setAssessment);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [attemptId]);

  function toggleHint(itemId: string) {
    setExpandedHints((prev) => {
      const next = new Set(prev);
      next.has(itemId) ? next.delete(itemId) : next.add(itemId);
      return next;
    });
  }

  function expandAllHints() {
    if (assessment) setExpandedHints(new Set(assessment.items.map((i) => i.id)));
  }

  if (loading) return <Spinner />;
  if (error && !attempt) return <div><ErrorBanner message={error} /></div>;
  if (!attempt || !assessment || attempt.status === "in_progress") {
    return (
      <div>
        {attempt?.status === "in_progress" && (
          <button onClick={() => navigate(`/assessments/${attempt.assessment_id}`)} style={btnPrimary}>
            Продолжить тест →
          </button>
        )}
        {error && <ErrorBanner message={error} />}
      </div>
    );
  }

  const answersByItemId: Record<string, AnswerResult> = {};
  (attempt.answers ?? []).forEach((a) => { answersByItemId[a.item_id] = a; });
  const sortedItems = [...assessment.items].sort(
    (a, b) => (a.position ?? a.order ?? 0) - (b.position ?? b.order ?? 0)
  );

  return (
    <div style={{ maxWidth: 720 }}>
      <button
        onClick={() => navigate("/")}
        style={{ background: "none", border: "none", color: "#3B5BDB", cursor: "pointer", fontSize: 14, fontWeight: 500, marginBottom: 20, padding: 0, display: "flex", alignItems: "center", gap: 6 }}
      >
        ← На главную
      </button>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: "#0F172A", letterSpacing: "-0.4px" }}>Разбор ответов</h2>
          <div style={{ color: "#64748B", marginTop: 4, fontSize: 14 }}>
            {assessment.title} — {attempt.percentage.toFixed(0)}% ({attempt.earned_score.toFixed(1)}/{attempt.max_score.toFixed(1)} баллов)
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button onClick={expandAllHints} style={btnSecondary}>Раскрыть все</button>
          <button onClick={() => navigate(`/assessments/${assessment.id}`)} style={btnPrimary}>Повторить</button>
        </div>
      </div>

      {sortedItems.map((item, idx) => {
        const ans = answersByItemId[item.id];
        const isCorrect = ans?.is_correct;
        const hintOpen = expandedHints.has(item.id);
        const feedback = ans?.auto_feedback ?? "";
        const feedbackParts = feedback.split("\n\n");
        const correctAnswerLine = feedbackParts[0] ?? "";
        const explanationText = feedbackParts.slice(1).join("\n\n") || item.explanation || "";
        const correctIdMatch = correctAnswerLine.match(/Правильный ответ:\s*([A-D])\)/);
        const correctOptId = correctIdMatch?.[1] ?? null;

        return (
          <div key={item.id} style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "22px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 14 }}>
              <div style={{
                flexShrink: 0, width: 30, height: 30, borderRadius: "50%",
                background: isCorrect === true ? "#ECFDF5" : isCorrect === false ? "#FEF2F2" : "#F1F5F9",
                border: "2px solid",
                borderColor: isCorrect === true ? "#059669" : isCorrect === false ? "#DC2626" : "#CBD5E1",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 13, fontWeight: 700,
                color: isCorrect === true ? "#059669" : isCorrect === false ? "#DC2626" : "#94A3B8",
              }}>
                {isCorrect === true ? "✓" : isCorrect === false ? "✗" : "—"}
              </div>
              <div style={{ fontWeight: 600, color: "#0F172A", lineHeight: 1.5, fontSize: 15 }}>
                {idx + 1}. {item.prompt}
              </div>
            </div>

            {item.options && item.options.length > 0 && (
              <div style={{ display: "grid", gap: 8, marginBottom: 14, paddingLeft: 42 }}>
                {item.options.map((opt) => {
                  const wasSelected = ans?.selected_option_ids?.includes(opt.id);
                  const isCorrectOpt = correctOptId ? opt.id === correctOptId : false;
                  let bg = "transparent";
                  let borderColor = "#E2E8F0";
                  let icon: string | null = null;
                  let iconColor = "#059669";
                  if (isCorrectOpt) { bg = "#ECFDF5"; borderColor = "#059669"; icon = "✓"; iconColor = "#059669"; }
                  else if (wasSelected && !isCorrect) { bg = "#FEF2F2"; borderColor = "#DC2626"; icon = "✗"; iconColor = "#DC2626"; }

                  return (
                    <div key={opt.id} style={{ padding: "9px 14px", borderRadius: 10, border: `1.5px solid ${borderColor}`, background: bg, fontSize: 14, display: "flex", alignItems: "center", gap: 8 }}>
                      {icon && <span style={{ fontSize: 12, fontWeight: 700, color: iconColor, flexShrink: 0 }}>{icon}</span>}
                      <span style={{ color: "#334155" }}>{opt.text}</span>
                    </div>
                  );
                })}
              </div>
            )}

            {(correctAnswerLine || explanationText) && (
              <div style={{ paddingLeft: 42 }}>
                <button onClick={() => toggleHint(item.id)} style={{ background: "none", border: "none", cursor: "pointer", color: "#3B5BDB", fontSize: 13, fontWeight: 600, padding: "4px 0", display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ display: "inline-block", transform: hintOpen ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.15s", fontSize: 10 }}>▶</span>
                  Пояснение
                </button>
                {hintOpen && (
                  <div style={{ marginTop: 8, padding: "14px 16px", background: "#F0F4FF", borderRadius: 10, border: "1.5px solid #C7D2FE", fontSize: 13, lineHeight: 1.65 }}>
                    {correctAnswerLine && <div style={{ fontWeight: 700, color: "#334155", marginBottom: explanationText ? 8 : 0 }}>{correctAnswerLine}</div>}
                    {explanationText && <div style={{ color: "#475569" }}>{explanationText}</div>}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      <div style={{ display: "flex", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
        <button onClick={() => navigate(`/assessments/${assessment.id}`)} style={btnPrimary}>Повторить</button>
        <button onClick={() => navigate("/")} style={btnSecondary}>На главную</button>
      </div>
    </div>
  );
}

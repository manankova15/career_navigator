import React, { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getAssessment,
  AssessmentDetail,
  AssessmentItem,
  submitAttempt,
  startAttempt,
  saveAttemptProgress,
  myAttempts,
  AttemptResult,
  AnswerResult,
} from "../api/assessments";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";

type ReviewMode = "none" | "review";

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

export default function AssessmentTakePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, { selected: string[]; text: string }>>({});
  const [currentAttemptId, setCurrentAttemptId] = useState<string | null>(null);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [reviewMode, setReviewMode] = useState<ReviewMode>("none");
  const [expandedHints, setExpandedHints] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const answersRef = useRef(answers);
  const attemptIdRef = useRef(currentAttemptId);
  const assessmentRef = useRef(assessment);
  answersRef.current = answers;
  attemptIdRef.current = currentAttemptId;
  assessmentRef.current = assessment;

  useEffect(() => {
    if (!id) return;
    getAssessment(id)
      .then((a) => {
        setAssessment(a);
        const init: Record<string, { selected: string[]; text: string }> = {};
        a.items.forEach((i) => { init[i.id] = { selected: [], text: "" }; });
        setAnswers(init);
        return myAttempts(id).then((attempts) => {
          const inProg = attempts.find((t) => t.status === "in_progress");
          if (inProg?.progress_answers?.length) {
            setCurrentAttemptId(inProg.id);
            setAnswers((prev) => {
              const next = { ...prev };
              inProg.progress_answers!.forEach((p) => {
                next[p.item_id] = {
                  selected: p.selected_option_ids ?? [],
                  text: p.text_answer ?? "",
                };
              });
              return next;
            });
          } else if (inProg) {
            setCurrentAttemptId(inProg.id);
          } else {
            return startAttempt(id).then((att) => setCurrentAttemptId(att.id));
          }
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!attemptIdRef.current || !assessmentRef.current || result) return;
    const onBeforeUnload = () => {
      const a = assessmentRef.current;
      const ans = answersRef.current;
      const aid = attemptIdRef.current;
      if (!a || !aid) return;
      const payload = a.items.map((i) => ({
        item_id: i.id,
        selected_option_ids: ans[i.id]?.selected ?? [],
        text_answer: ans[i.id]?.text || undefined,
      }));
      saveAttemptProgress(aid, payload).catch(() => {});
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [currentAttemptId, assessment, result]);

  function toggleOption(itemId: string, optId: string, multi: boolean) {
    setAnswers(prev => {
      const cur = prev[itemId]?.selected ?? [];
      const next = multi
        ? cur.includes(optId) ? cur.filter(x => x !== optId) : [...cur, optId]
        : [optId];
      return { ...prev, [itemId]: { ...prev[itemId], selected: next } };
    });
  }

  async function handleSubmit() {
    if (!assessment) return;
    setSubmitting(true); setError("");
    try {
      const payload = assessment.items.map((i) => ({
        item_id: i.id,
        selected_option_ids: answers[i.id]?.selected ?? [],
        text_answer: answers[i.id]?.text || undefined,
      }));
      const res = await submitAttempt(assessment.id, payload, currentAttemptId);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setSubmitting(false); }
  }

  function handleRetry() {
    setResult(null);
    setReviewMode("none");
    setExpandedHints(new Set());
    setCurrentAttemptId(null);
    if (assessment) {
      const init: typeof answers = {};
      assessment.items.forEach((i) => { init[i.id] = { selected: [], text: "" }; });
      setAnswers(init);
    }
  }

  function toggleHint(itemId: string) {
    setExpandedHints(prev => {
      const next = new Set(prev);
      next.has(itemId) ? next.delete(itemId) : next.add(itemId);
      return next;
    });
  }

  function expandAllHints() {
    if (!assessment) return;
    setExpandedHints(new Set(assessment.items.map(i => i.id)));
  }

  if (loading) return <Spinner />;
  if (error && !assessment) return <div><ErrorBanner message={error} /></div>;
  if (!assessment) return null;

  // ── Results screen ───────────────────────────────────────────────────────────
  if (result && reviewMode === "none") {
    const passed = result.passed;
    return (
      <div style={{ maxWidth: 560 }}>
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 24, padding: "40px", textAlign: "center", boxShadow: "0 4px 24px rgba(15,23,42,0.06)" }}>
          <div style={{ fontSize: 64, marginBottom: 20 }}>{passed ? "🎉" : "📚"}</div>
          <div style={{ fontSize: 72, fontWeight: 900, letterSpacing: "-2px", lineHeight: 1, color: passed ? "#059669" : "#DC2626", marginBottom: 8 }}>
            {result.percentage.toFixed(0)}%
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: passed ? "#059669" : "#DC2626", marginBottom: 8 }}>
            {passed ? "Тест пройден!" : "Можно лучше"}
          </div>
          <div style={{ fontSize: 15, color: "#64748B", marginBottom: 32 }}>
            Баллы: {result.earned_score.toFixed(1)} / {result.max_score.toFixed(1)}
          </div>

          {/* Score bar */}
          <div style={{ background: "#F1F5F9", borderRadius: 999, height: 8, marginBottom: 32, overflow: "hidden" }}>
            <div style={{ width: `${result.percentage}%`, background: passed ? "linear-gradient(90deg, #059669, #34D399)" : "linear-gradient(90deg, #DC2626, #F87171)", height: "100%", borderRadius: 999, transition: "width 0.5s ease" }} />
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
            <button onClick={handleRetry} style={btnPrimary} className="primary-btn">
              Попробовать снова
            </button>
            <button onClick={() => setReviewMode("review")} style={btnSecondary} className="primary-btn">
              Посмотреть ответы
            </button>
            <button onClick={() => navigate("/assessments")} style={btnSecondary} className="primary-btn">
              Все задания
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Review mode ──────────────────────────────────────────────────────────────
  if (result && reviewMode === "review") {
    const answersByItemId: Record<string, AnswerResult> = {};
    (result.answers ?? []).forEach(a => { answersByItemId[a.item_id] = a; });
    const sortedItems = [...assessment.items].sort(
      (a, b) => (a.position ?? a.order ?? 0) - (b.position ?? b.order ?? 0)
    );

    return (
      <div style={{ maxWidth: 720 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28, flexWrap: "wrap", gap: 12 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: "#0F172A", letterSpacing: "-0.4px" }}>Разбор ответов</h2>
            <div style={{ color: "#64748B", marginTop: 4, fontSize: 14 }}>
              {assessment.title} — {result.percentage.toFixed(0)}% ({result.earned_score.toFixed(1)}/{result.max_score.toFixed(1)} баллов)
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button onClick={expandAllHints} style={btnSecondary} className="primary-btn">
              Раскрыть все
            </button>
            <button onClick={handleRetry} style={btnPrimary} className="primary-btn">
              Повторить
            </button>
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
                  {item.options.map(opt => {
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
                      {correctAnswerLine && (
                        <div style={{ fontWeight: 700, color: "#334155", marginBottom: explanationText ? 8 : 0 }}>{correctAnswerLine}</div>
                      )}
                      {explanationText && <div style={{ color: "#475569" }}>{explanationText}</div>}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        <div style={{ display: "flex", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
          <button onClick={handleRetry} style={btnPrimary} className="primary-btn">Повторить</button>
          <button onClick={() => navigate("/assessments")} style={btnSecondary} className="primary-btn">Все задания</button>
        </div>
      </div>
    );
  }

  // ── Taking the test ──────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: 720 }}>
      <button
        onClick={() => navigate("/assessments")}
        style={{ background: "none", border: "none", color: "#3B5BDB", cursor: "pointer", fontSize: 14, fontWeight: 500, marginBottom: 20, padding: 0, display: "flex", alignItems: "center", gap: 6 }}
      >
        ← Назад к заданиям
      </button>

      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: "0 0 6px", fontSize: 24, fontWeight: 800, color: "#0F172A", letterSpacing: "-0.4px" }}>{assessment.title}</h1>
        {assessment.description && (
          <p style={{ color: "#64748B", marginTop: 0, marginBottom: 0, fontSize: 14 }}>{assessment.description}</p>
        )}
      </div>

      {error && <ErrorBanner message={error} />}

      {[...assessment.items].sort((a, b) => (a.position ?? a.order ?? 0) - (b.position ?? b.order ?? 0)).map((item, idx) => (
        <ItemBlock key={item.id} item={item} index={idx}
          answer={answers[item.id] ?? { selected: [], text: "" }}
          onToggle={toggleOption}
          onText={(itemId, t) => setAnswers(prev => ({ ...prev, [itemId]: { ...prev[itemId], text: t } }))} />
      ))}

      <button onClick={handleSubmit} disabled={submitting} style={{ ...btnPrimary, marginTop: 8 }} className="primary-btn">
        {submitting ? "Отправляем…" : "Отправить ответы →"}
      </button>
    </div>
  );
}

function ItemBlock({ item, index, answer, onToggle, onText }: {
  item: AssessmentItem; index: number;
  answer: { selected: string[]; text: string };
  onToggle: (itemId: string, optId: string, multi: boolean) => void;
  onText: (itemId: string, text: string) => void;
}) {
  const isMulti = item.mode === "multi_select";
  const isText = item.mode === "short_text" || item.mode === "case";

  return (
    <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "22px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
      <div style={{ fontWeight: 700, marginBottom: 14, color: "#0F172A", fontSize: 15, lineHeight: 1.5 }}>
        {index + 1}. {item.prompt}
      </div>
      {isText && (
        <textarea
          value={answer.text}
          onChange={e => onText(item.id, e.target.value)}
          rows={item.mode === "case" ? 5 : 2}
          placeholder="Введите ваш ответ…"
          style={{ width: "100%", border: "1.5px solid #E2E8F0", borderRadius: 12, padding: "10px 14px", fontSize: 14, boxSizing: "border-box", resize: "vertical", outline: "none", fontFamily: "inherit", transition: "border-color 0.15s" }}
          onFocus={e => { e.currentTarget.style.borderColor = "#3B5BDB"; }}
          onBlur={e => { e.currentTarget.style.borderColor = "#E2E8F0"; }}
        />
      )}
      {!isText && item.options && (
        <div style={{ display: "grid", gap: 10 }}>
          {item.options.map(opt => {
            const selected = answer.selected.includes(opt.id);
            return (
              <label key={opt.id} style={{
                display: "flex", alignItems: "center", gap: 12, cursor: "pointer",
                padding: "10px 14px",
                borderRadius: 12,
                border: "1.5px solid",
                borderColor: selected ? "#3B5BDB" : "#E2E8F0",
                background: selected ? "#EEF2FF" : "#F8FAFC",
                transition: "all 0.15s",
              }}>
                <input
                  type={isMulti ? "checkbox" : "radio"}
                  checked={selected}
                  onChange={() => onToggle(item.id, opt.id, isMulti)}
                  style={{ accentColor: "#3B5BDB", width: 16, height: 16, flexShrink: 0 }}
                />
                <span style={{ fontSize: 14, color: "#334155" }}>{opt.text}</span>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

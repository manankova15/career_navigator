import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getVacancy, Vacancy, recordVacancyInterest } from "../api/vacancies";
import { listAssessments, AssessmentSummary } from "../api/assessments";
import { prepareDescription } from "../utils/formatDescription";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";

const SENIORITY_LABELS: Record<string, string> = {
  junior: "Junior",
  middle: "Middle",
  senior: "Senior",
  lead: "Lead",
  principal: "Principal",
};

const STATUS_LABELS: Record<string, string> = {
  active: "Активна",
  expired: "Истекла",
  archived: "В архиве",
  blocked: "Заблокирована",
};

function jaccardRelevance(vacancySkills: string[], assessmentSkills: string[]): number {
  if (!vacancySkills.length || !assessmentSkills.length) return 0;
  const vs = new Set(vacancySkills.map(s => s.toLowerCase()));
  const as = new Set(assessmentSkills.map(s => s.toLowerCase()));
  const intersection = [...vs].filter(s => as.has(s)).length;
  const union = new Set([...vs, ...as]).size;
  return union === 0 ? 0 : intersection / union;
}

export default function VacancyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [vacancy, setVacancy] = useState<Vacancy | null>(null);
  const [error, setError] = useState("");
  const [relevantAssessments, setRelevantAssessments] = useState<(AssessmentSummary & { relevance: number })[]>([]);
  const [interestSubmitted, setInterestSubmitted] = useState(false);
  const [interestAnswer, setInterestAnswer] = useState<boolean | null>(null);

  useEffect(() => {
    if (!id) return;
    getVacancy(id)
      .then(v => {
        setVacancy(v);
        listAssessments()
          .then(all => {
            const scored = all
              .map(a => ({ ...a, relevance: jaccardRelevance(v.skills ?? [], a.related_skills) }))
              .filter(a => a.relevance > 0)
              .sort((a, b) => b.relevance - a.relevance)
              .slice(0, 4);
            setRelevantAssessments(scored);
          })
          .catch(() => {});
      })
      .catch(e => setError(e.message));
  }, [id]);

  async function handleInterest(interested: boolean) {
    setInterestAnswer(interested);
    setInterestSubmitted(true);
    if (id) await recordVacancyInterest(id, interested);
  }

  if (error) return <div><ErrorBanner message={error} /></div>;
  if (!vacancy) return <Spinner />;

  function salary() {
    if (!vacancy!.salary_from && !vacancy!.salary_to) return "Не указана";
    const parts = [vacancy!.salary_from, vacancy!.salary_to]
      .filter(Boolean)
      .map(n => n!.toLocaleString("ru-RU"));
    return `${parts.join(" – ")} ${vacancy!.currency ?? "₽"}`.trim();
  }

  return (
    <div style={{ maxWidth: 780 }}>
      {/* Back link */}
      <Link to="/vacancies" className="text-link" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "#3B5BDB", fontSize: 14, textDecoration: "none", fontWeight: 500, marginBottom: 24 }}>
        ← Все вакансии
      </Link>

      {/* Title block */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: "#0F172A", margin: "0 0 8px", letterSpacing: "-0.5px", lineHeight: 1.2 }}>
          {vacancy.title}
        </h1>
        <div style={{ fontSize: 16, color: "#3B5BDB", fontWeight: 600, marginBottom: 6 }}>{vacancy.company}</div>
        {vacancy.location && (
          <div style={{ display: "flex", alignItems: "center", gap: 5, color: "#64748B", fontSize: 14 }}>
            <span>📍</span> {vacancy.location}
          </div>
        )}
      </div>

      {/* Meta card */}
      <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 20 }}>
          <StatItem icon="💰" label="Зарплата" value={salary()} accent="#059669" />
          <StatItem icon="📋" label="Статус" value={STATUS_LABELS[vacancy.status] ?? vacancy.status} accent="#3B5BDB" />
          {vacancy.seniority && (
            <StatItem icon="🎯" label="Уровень" value={SENIORITY_LABELS[vacancy.seniority] ?? vacancy.seniority} accent="#7C3AED" />
          )}
          {vacancy.employment_type && (
            <StatItem icon="⏱" label="Тип занятости" value={vacancy.employment_type} accent="#D97706" />
          )}
        </div>
      </div>

      {/* Skills */}
      {vacancy.skills && vacancy.skills.length > 0 && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>Требуемые навыки</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {vacancy.skills.map(s => (
              <span key={s} style={{ background: "#EEF2FF", color: "#3B5BDB", fontSize: 12, fontWeight: 500, borderRadius: 999, padding: "5px 12px" }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Description */}
      {vacancy.description && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>Описание</h3>
          <div
            className="vacancy-description"
            dangerouslySetInnerHTML={{ __html: prepareDescription(vacancy.description) }}
          />
        </div>
      )}

      {/* Interest survey */}
      <div style={{ background: "#F8FAFC", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16 }}>
        {!interestSubmitted ? (
          <>
            <h3 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>
              Эта вакансия вас заинтересовала?
            </h3>
            <p style={{ margin: "0 0 16px", fontSize: 13, color: "#64748B" }}>
              Ваш ответ поможет улучшить рекомендации
            </p>
            <div style={{ display: "flex", gap: 10 }}>
              <button
                onClick={() => handleInterest(true)}
                style={{ padding: "10px 20px", background: "#ECFDF5", color: "#059669", border: "1.5px solid #A7F3D0", borderRadius: 12, cursor: "pointer", fontWeight: 600, fontSize: 14, transition: "all 0.15s" }}
                onMouseEnter={e => { e.currentTarget.style.background = "#059669"; e.currentTarget.style.color = "#fff"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#ECFDF5"; e.currentTarget.style.color = "#059669"; }}
              >
                👍 Да, интересно
              </button>
              <button
                onClick={() => handleInterest(false)}
                style={{ padding: "10px 20px", background: "#F8FAFC", color: "#64748B", border: "1.5px solid #E2E8F0", borderRadius: 12, cursor: "pointer", fontWeight: 600, fontSize: 14, transition: "all 0.15s" }}
                onMouseEnter={e => { e.currentTarget.style.background = "#F1F5F9"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#F8FAFC"; }}
              >
                👎 Нет, не подходит
              </button>
            </div>
          </>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              width: 36, height: 36, borderRadius: "50%",
              background: interestAnswer ? "#ECFDF5" : "#F1F5F9",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
            }}>
              {interestAnswer ? "✓" : "✗"}
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: interestAnswer ? "#059669" : "#64748B" }}>
                {interestAnswer ? "Отлично! Мы учтём это в ваших рекомендациях." : "Понятно, мы учтём это при подборе вакансий."}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Relevant assessments */}
      {relevantAssessments.length > 0 && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 24, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <h3 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>
            Подготовьтесь к собеседованию
          </h3>
          <p style={{ margin: "0 0 16px", fontSize: 13, color: "#64748B" }}>
            Задания, подобранные по навыкам из этой вакансии
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {relevantAssessments.map(a => (
              <div key={a.id} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "12px 16px",
                background: "#F8FAFC",
                borderRadius: 12,
                border: "1.5px solid #E2E8F0",
              }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: "#0F172A" }}>{a.title}</div>
                  <div style={{ fontSize: 12, color: "#64748B", marginTop: 2 }}>
                    {a.topic} · {a.related_skills.slice(0, 3).join(", ")}
                  </div>
                  <div style={{ fontSize: 11, color: "#3B5BDB", marginTop: 2, fontWeight: 500 }}>
                    Совпадение: {(a.relevance * 100).toFixed(0)}%
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/assessments/${a.id}`)}
                  style={{ padding: "8px 16px", background: "#3B5BDB", color: "#fff", border: "none", borderRadius: 10, cursor: "pointer", fontWeight: 600, fontSize: 13, whiteSpace: "nowrap", flexShrink: 0, transition: "all 0.15s" }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#2F4AC2"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "#3B5BDB"; }}
                >
                  Пройти →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Apply button */}
      {vacancy.canonical_url && (
        <a
          href={vacancy.canonical_url}
          target="_blank"
          rel="noreferrer"
          style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            background: "#3B5BDB", color: "#fff",
            padding: "13px 28px", borderRadius: 12,
            textDecoration: "none", fontWeight: 700, fontSize: 15,
            boxShadow: "0 4px 16px rgba(59,91,219,0.3)",
            transition: "all 0.15s",
          }}
          onMouseEnter={e => { e.currentTarget.style.background = "#2F4AC2"; e.currentTarget.style.boxShadow = "0 6px 24px rgba(59,91,219,0.4)"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "#3B5BDB"; e.currentTarget.style.boxShadow = "0 4px 16px rgba(59,91,219,0.3)"; }}
        >
          Откликнуться на источнике →
        </a>
      )}
    </div>
  );
}

function StatItem({ icon, label, value, accent }: { icon: string; label: string; value: string; accent: string }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
      <div style={{ fontSize: 18, marginTop: 1 }}>{icon}</div>
      <div>
        <div style={{ fontSize: 12, color: "#94A3B8", fontWeight: 500, marginBottom: 2 }}>{label}</div>
        <div style={{ fontSize: 15, fontWeight: 700, color: "#0F172A" }}>{value}</div>
      </div>
    </div>
  );
}

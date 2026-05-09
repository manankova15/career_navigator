import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import { getVacancy, Vacancy, recordVacancyInterest, vacancySalaryCurrency } from "../api/vacancies";
import { useLikedVacancies } from "../hooks/useLikedVacancies";
import { listAssessments, AssessmentSummary } from "../api/assessments";
import { recordEvent } from "../api/analytics";
import { prepareDescription } from "../utils/formatDescription";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";
import {
  EDUCATION_LEVELS,
  EMPLOYMENT_LABEL,
  ENGLISH_LEVELS,
  EXPERIENCE_LEVEL_LABEL,
  PROFESSION_AREA_LABEL,
  SALARY_GROSS_LABEL,
  SALARY_PERIOD_LABEL,
  SCHEDULE_LABEL,
  SPECIALIZATION_OPTIONS,
  WORK_FORMAT_LABEL,
} from "../components/vacancies/vacanciesConstants";

const SENIORITY_LABELS: Record<string, string> = {
  intern: "Стажёр",
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

const SPEC_LABEL = Object.fromEntries(SPECIALIZATION_OPTIONS.map(o => [o.value, o.label]));

function jaccardRelevance(vacancySkills: string[], assessmentSkills: string[]): number {
  if (!vacancySkills.length || !assessmentSkills.length) return 0;
  const vs = new Set(vacancySkills.map(s => s.toLowerCase()));
  const as = new Set(assessmentSkills.map(s => s.toLowerCase()));
  const intersection = [...vs].filter(s => as.has(s)).length;
  const union = new Set([...vs, ...as]).size;
  return union === 0 ? 0 : intersection / union;
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        display: "inline-block",
        background: "#F1F5F9",
        color: "#334155",
        fontSize: 12,
        fontWeight: 600,
        borderRadius: 999,
        padding: "4px 10px",
      }}
    >
      {children}
    </span>
  );
}

function formatEmployment(et: string[] | string | null | undefined): string | null {
  if (!et) return null;
  const arr = Array.isArray(et) ? et : [et];
  return arr.map(x => EMPLOYMENT_LABEL[x] ?? x).join(", ") || null;
}

export default function VacancyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const returnTo = (location.state as { returnTo?: string } | null)?.returnTo ?? "";
  const backHref = returnTo.startsWith("/") ? returnTo : `/vacancies${returnTo}`;
  const backLabel = returnTo.startsWith("/recommendations")
    ? "Все рекомендации"
    : "Все вакансии";
  const [vacancy, setVacancy] = useState<Vacancy | null>(null);
  const [error, setError] = useState("");
  const [relevantAssessments, setRelevantAssessments] = useState<(AssessmentSummary & { relevance: number })[]>([]);
  const [interestSubmitted, setInterestSubmitted] = useState(false);
  const [interestAnswer, setInterestAnswer] = useState<boolean | null>(null);
  const { isLiked, toggleLike } = useLikedVacancies();

  useEffect(() => {
    if (!id) return;
    getVacancy(id)
      .then(v => {
        setVacancy(v);
        recordEvent("vacancy_viewed", "vacancy", id);
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
    if (id) {
      await recordVacancyInterest(id, interested, {
        vacancyTitle: vacancy?.title ?? null,
        vacancySkills: vacancy?.skills ?? [],
      });
    }
  }

  if (error) return <div><ErrorBanner message={error} /></div>;
  if (!vacancy) return <Spinner />;

  function salaryBlock(): string {
    if (!vacancy!.salary_from && !vacancy!.salary_to) return "Не указана";
    const parts = [vacancy!.salary_from, vacancy!.salary_to]
      .filter(Boolean)
      .map(n => n!.toLocaleString("ru-RU"));
    const cur = vacancySalaryCurrency(vacancy!);
    const sym = cur === "RUB" ? "₽" : cur;
    const period = vacancy!.salary_period
      ? SALARY_PERIOD_LABEL[vacancy!.salary_period] ?? vacancy!.salary_period
      : "";
    const gross = vacancy!.salary_gross_type
      ? SALARY_GROSS_LABEL[vacancy!.salary_gross_type] ?? ""
      : "";
    const tail = [sym, period, gross].filter(Boolean).join(" · ");
    return `${parts.join(" – ")} ${tail}`.trim();
  }

  const locationLine = [vacancy.location_city, vacancy.location_country].filter(Boolean).join(", ")
    || vacancy.location
    || null;

  const englishLabel = vacancy.english_level
    ? ENGLISH_LEVELS.find(e => e.value === vacancy.english_level)?.label ?? vacancy.english_level
    : null;
  const eduLabel = vacancy.education_level
    ? EDUCATION_LEVELS.find(e => e.value === vacancy.education_level)?.label ?? vacancy.education_level
    : null;

  const workFormats = (vacancy.work_format ?? []).map(w => WORK_FORMAT_LABEL[w] ?? w);
  const scheduleLabel = vacancy.schedule_type
    ? SCHEDULE_LABEL[vacancy.schedule_type] ?? vacancy.schedule_type
    : null;
  const experienceLabel = vacancy.experience_level
    ? EXPERIENCE_LEVEL_LABEL[vacancy.experience_level] ?? vacancy.experience_level
    : null;
  const employmentStr = formatEmployment(vacancy.employment_type);

  const professionLabel = vacancy.profession_area
    ? PROFESSION_AREA_LABEL[vacancy.profession_area] ?? vacancy.profession_area
    : null;
  const specLabel = vacancy.specialization
    ? SPEC_LABEL[vacancy.specialization] ?? vacancy.specialization
    : null;

  const conditionsChips: React.ReactNode[] = [];
  if (employmentStr) conditionsChips.push(<Chip key="et">{employmentStr}</Chip>);
  workFormats.forEach((w, i) => conditionsChips.push(<Chip key={`wf${i}`}>{w}</Chip>));
  if (scheduleLabel) conditionsChips.push(<Chip key="sch">{scheduleLabel}</Chip>);
  if (experienceLabel) conditionsChips.push(<Chip key="exp">{experienceLabel}</Chip>);
  if (englishLabel) conditionsChips.push(<Chip key="en">{englishLabel}</Chip>);
  if (eduLabel) conditionsChips.push(<Chip key="edu">{eduLabel}</Chip>);

  return (
    <div style={{ maxWidth: 780 }}>
      <Link to={backHref} className="text-link" style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "#3B5BDB", fontSize: 14, textDecoration: "none", fontWeight: 500, marginBottom: 24 }}>
        ← {backLabel}
      </Link>

      <div style={{ marginBottom: 24, display: "flex", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: "#0F172A", margin: "0 0 8px", letterSpacing: "-0.5px", lineHeight: 1.2 }}>
            {vacancy.title}
          </h1>
          <div style={{ fontSize: 16, color: "#3B5BDB", fontWeight: 600, marginBottom: 6 }}>{vacancy.company}</div>
          {locationLine && (
            <div style={{ display: "flex", alignItems: "center", gap: 5, color: "#64748B", fontSize: 14 }}>
              <span>📍</span> {locationLine}
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={() => toggleLike(vacancy)}
          aria-label={isLiked(vacancy.id) ? "Убрать из понравившихся" : "Добавить в понравившиеся"}
          style={{
            flexShrink: 0,
            width: 48,
            height: 48,
            borderRadius: 14,
            border: "1px solid #E6EAF2",
            background: isLiked(vacancy.id) ? "#FFF1F2" : "#FFFFFF",
            color: isLiked(vacancy.id) ? "#E11D48" : "#94A3B8",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "color 0.2s ease, background 0.2s ease",
          }}
        >
          <svg width={24} height={24} viewBox="0 0 24 24" fill={isLiked(vacancy.id) ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </button>
      </div>

      <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
        <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>Условия</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
          <StatItem icon="💰" label="Зарплата" value={salaryBlock()} />
          <StatItem icon="📋" label="Статус" value={STATUS_LABELS[vacancy.status] ?? vacancy.status} />
          {vacancy.seniority && (
            <StatItem
              icon="🎯"
              label="Уровень (legacy)"
              value={(vacancy.seniority.split(/\s*,\s*/).map(s => SENIORITY_LABELS[s.trim().toLowerCase()] ?? s.trim()).filter(Boolean).join(", "))}
            />
          )}
        </div>
        {conditionsChips.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14 }}>
            {conditionsChips}
          </div>
        )}
      </div>

      {(professionLabel || specLabel || vacancy.company_industry) && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>Категория</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 14, color: "#334155" }}>
            {professionLabel && <div><strong>Область:</strong> {professionLabel}</div>}
            {specLabel && <div><strong>Специализация:</strong> {specLabel}</div>}
            {vacancy.company_industry && <div><strong>Индустрия:</strong> {vacancy.company_industry}</div>}
            {vacancy.source_name && <div style={{ fontSize: 13, color: "#64748B" }}>Источник: {vacancy.source_name}</div>}
          </div>
        </div>
      )}

      {vacancy.skills && vacancy.skills.length > 0 && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>Навыки</h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {vacancy.skills.map(s => (
              <span key={s} style={{ background: "#EEF2FF", color: "#3B5BDB", fontSize: 12, fontWeight: 500, borderRadius: 999, padding: "5px 12px" }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {vacancy.description && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700, color: "#0F172A" }}>Описание</h3>
          <div
            className="vacancy-description"
            dangerouslySetInnerHTML={{ __html: prepareDescription(vacancy.description) }}
          />
        </div>
      )}

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

function StatItem({ icon, label, value }: { icon: string; label: string; value: string }) {
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

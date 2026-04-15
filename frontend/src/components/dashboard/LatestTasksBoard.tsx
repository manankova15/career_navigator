import { Link, useNavigate } from "react-router-dom";
import { AttemptResult } from "../../api/assessments";

export interface LatestTasksBoardProps {
  attempts: AttemptResult[];
  loading?: boolean;
}

function IconClipboard({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    </svg>
  );
}

export default function LatestTasksBoard({ attempts, loading }: LatestTasksBoardProps) {
  const navigate = useNavigate();
  const hasTasks = attempts.length > 0;
  const inProgressCount = attempts.filter(a => a.status === "in_progress").length;
  const completedCount = attempts.filter(a => a.status !== "in_progress").length;
  const completedWithScore = attempts.filter(a => a.status !== "in_progress" && a.percentage != null);
  const avgScore = completedWithScore.length > 0
    ? Math.round(completedWithScore.reduce((s, a) => s + a.percentage, 0) / completedWithScore.length)
    : 60;

  const featuredAttempt = attempts.find(a => a.status === "in_progress") ?? attempts[0] ?? null;
  const otherAttempts = featuredAttempt
    ? attempts.filter(a => a.id !== featuredAttempt.id).slice(0, 3)
    : attempts.slice(0, 3);

  function formatDate(s: string | null | undefined) {
    if (!s) return "";
    return new Date(s).toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
  }

  return (
    <section
      style={{
        background: "linear-gradient(180deg, #FFFFFF 0%, #FCFCFF 100%)",
        border: "1px solid #E6EAF2",
        borderRadius: 30,
        padding: 28,
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.05)",
        position: "relative",
        overflow: "hidden",
      }}
      role="region"
      aria-label="Последние задания"
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 16 }}>
        <div>
          <h2 style={{ fontSize: 30, fontWeight: 700, lineHeight: "36px", color: "#0F172A", margin: "0 0 8px" }}>
            Последние задания
          </h2>
          <p style={{ fontSize: 18, fontWeight: 400, lineHeight: "28px", color: "#64748B", margin: 0 }}>
            Ваш прогресс и текущие шаги
          </p>
        </div>
        <Link
          to="/assessments"
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "#5B5CEB",
            textDecoration: "none",
            transition: "opacity 0.2s ease",
            flexShrink: 0,
          }}
          onMouseEnter={e => (e.currentTarget.style.opacity = "0.8")}
          onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
        >
          Все →
        </Link>
      </div>

      {loading && !hasTasks && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 200, color: "#94A3B8", fontSize: 16 }}>
          Загрузка…
        </div>
      )}

      {!loading && !hasTasks && (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: 240,
            textAlign: "center",
            padding: 24,
            position: "relative",
          }}
        >
          <img
            src="/pictures/professional-career-growth-dashboard.webp"
            alt=""
            role="presentation"
            className="dashboard-tasks-illustration"
            style={{
              width: 200,
              maxWidth: "100%",
              height: "auto",
              opacity: 0.85,
              marginBottom: 20,
              objectFit: "contain",
            }}
          />
          <h3 style={{ fontSize: 20, fontWeight: 600, color: "#0F172A", margin: "0 0 8px" }}>
            Заданий пока нет
          </h3>
          <p style={{ fontSize: 16, color: "#64748B", lineHeight: 1.5, maxWidth: 320, margin: "0 0 24px" }}>
            Начните с первого задания, чтобы получить персональные карьерные рекомендации
          </p>
          <Link
            to="/assessments"
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "14px 22px",
              background: "#5B5CEB",
              color: "#fff",
              borderRadius: 16,
              fontWeight: 600,
              fontSize: 16,
              textDecoration: "none",
              transition: "background 0.2s ease",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "#4F46E5")}
            onMouseLeave={e => (e.currentTarget.style.background = "#5B5CEB")}
          >
            Начать сейчас
          </Link>
        </div>
      )}

      {!loading && hasTasks && (
        <>
          {/* Summary chips */}
          <div className="dashboard-tasks-chips" style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 18 }}>
            {inProgressCount > 0 && (
              <span
                style={{
                  background: "#FFF7E8",
                  color: "#B45309",
                  borderRadius: 999,
                  padding: "8px 12px",
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {inProgressCount} в процессе
              </span>
            )}
            {completedCount > 0 && (
              <span
                style={{
                  background: "#ECFDF5",
                  color: "#047857",
                  borderRadius: 999,
                  padding: "8px 12px",
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {completedCount} завершено
              </span>
            )}
            <span
              style={{
                background: "#EEF2FF",
                color: "#4338CA",
                borderRadius: 999,
                padding: "8px 12px",
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              Средний балл {avgScore}%
            </span>
          </div>

          {/* Featured task card */}
          {featuredAttempt && (
            <div
              style={{
                borderRadius: 22,
                background: "linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 100%)",
                border: "1px solid #E6EAF2",
                padding: 20,
                marginBottom: 16,
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  background: featuredAttempt.status === "in_progress" ? "#FFF7E8" : "#ECFDF5",
                  color: featuredAttempt.status === "in_progress" ? "#B45309" : "#047857",
                  borderRadius: 999,
                  padding: "6px 12px",
                  fontSize: 13,
                  fontWeight: 600,
                  marginBottom: 12,
                }}
              >
                {featuredAttempt.status === "in_progress" ? "В процессе" : "Завершено"}
              </span>
              <div style={{ fontSize: 18, fontWeight: 700, color: "#0F172A", marginBottom: 4 }}>
                {featuredAttempt.assessment_title ?? "Задание"}
              </div>
              <div style={{ fontSize: 14, color: "#64748B", marginBottom: 14 }}>
                {formatDate(featuredAttempt.created_at)} · {featuredAttempt.percentage != null ? `${Math.round(featuredAttempt.percentage)}%` : "в процессе"}
              </div>
              <div
                style={{
                  height: 8,
                  borderRadius: 999,
                  background: "#E9EEF7",
                  overflow: "hidden",
                  marginBottom: 14,
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${featuredAttempt.percentage ?? 60}%`,
                    background: "#5B5CEB",
                    borderRadius: 999,
                    transition: "width 0.2s ease",
                  }}
                />
              </div>
              <button
                type="button"
                onClick={() =>
                  featuredAttempt.status === "in_progress"
                    ? navigate(`/assessments/${featuredAttempt.assessment_id}`)
                    : navigate(`/attempts/${featuredAttempt.id}`)
                }
                style={{
                  background: "#5B5CEB",
                  color: "#fff",
                  border: "none",
                  borderRadius: 14,
                  padding: "12px 18px",
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "background 0.2s ease",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "#4F46E5")}
                onMouseLeave={e => (e.currentTarget.style.background = "#5B5CEB")}
              >
                {featuredAttempt.status === "in_progress" ? "Продолжить" : "Смотреть результат"}
              </button>
            </div>
          )}

          {/* Compact task rows */}
          {otherAttempts.length > 0 && (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 12 }}>
              {otherAttempts.map(a => {
                const title = a.assessment_title ?? "Задание";
                const isInProgress = a.status === "in_progress";
                const metaLine = `${a.percentage != null ? Math.round(a.percentage) + "%" : "—"} · ${formatDate(a.created_at)}`;
                const buttonStyle = isInProgress
                  ? { background: "#FFF7E8", color: "#B45309", border: "1px solid #FDE68A" }
                  : { background: "#ECFDF5", color: "#047857", border: "1px solid #A7F3D0" };
                return (
                  <li
                    key={a.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 16,
                      background: "#FFFFFF",
                      border: "1px solid #E6EAF2",
                      borderRadius: 18,
                      padding: "16px 18px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 16, minWidth: 0, flex: 1 }}>
                      <div
                        style={{
                          width: 40,
                          height: 40,
                          borderRadius: 12,
                          background: "#F8FAFF",
                          border: "1px solid #E6EAF2",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          flexShrink: 0,
                        }}
                      >
                        <IconClipboard size={22} />
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 16, fontWeight: 600, color: "#0F172A" }}>{title}</div>
                        <div style={{ fontSize: 14, color: "#94A3B8", marginTop: 2 }}>{metaLine}</div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        isInProgress ? navigate(`/assessments/${a.assessment_id}`) : navigate(`/attempts/${a.id}`)
                      }
                      style={{
                        padding: "8px 14px",
                        borderRadius: 999,
                        fontSize: 13,
                        fontWeight: 600,
                        cursor: "pointer",
                        flexShrink: 0,
                        transition: "opacity 0.2s ease",
                        ...buttonStyle,
                      }}
                      onMouseEnter={e => (e.currentTarget.style.opacity = "0.9")}
                      onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
                    >
                      {isInProgress ? "Продолжить" : "Смотреть результат"}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          {/* Mini helper panel when few tasks */}
          {attempts.length <= 2 && (
            <div
              style={{
                marginTop: 18,
                background: "#F8FAFF",
                border: "1px dashed #D7E0EE",
                borderRadius: 18,
                padding: 16,
                fontSize: 14,
                color: "#64748B",
                lineHeight: 1.5,
                display: "flex",
                alignItems: "center",
                gap: 16,
              }}
            >
              <img
                src="/pictures/professional-career-growth-dashboard.webp"
                alt=""
                role="presentation"
                style={{
                  width: 180,
                  maxWidth: "100%",
                  height: "auto",
                  opacity: 0.75,
                  objectFit: "contain",
                  flexShrink: 0,
                }}
              />
              <span>
                Совет: завершите текущее задание, чтобы получить точнее рекомендации по вакансиям
              </span>
            </div>
          )}
        </>
      )}
    </section>
  );
}

import { Link, useNavigate } from "react-router-dom";
import { AttemptResult } from "../../api/assessments";

export interface LatestTasksCardProps {
  attempts: AttemptResult[];
  loading?: boolean;
}

function IconClipboard({ size = 64 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#C7D2FE" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    </svg>
  );
}

export default function LatestTasksCard({ attempts, loading }: LatestTasksCardProps) {
  const navigate = useNavigate();
  const hasTasks = attempts.length > 0;
  const displayAttempts = attempts.slice(0, 3);

  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E2E8F0",
        borderRadius: 28,
        padding: 28,
        minHeight: 340,
        boxShadow: "var(--shadow-card)",
      }}
      role="region"
      aria-label="Последние задания"
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, lineHeight: "34px", color: "#0F172A", margin: 0 }}>
          Последние задания
        </h2>
        <Link
          to="/assessments"
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "#4F46E5",
            textDecoration: "none",
            transition: "opacity 0.2s ease",
          }}
          onMouseEnter={e => (e.currentTarget.style.opacity = "0.8")}
          onMouseLeave={e => (e.currentTarget.style.opacity = "1")}
        >
          Все →
        </Link>
      </div>

      {loading && !hasTasks && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 200, color: "#94A3B8" }}>
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
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: 20,
              background: "#EEF2FF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 20,
            }}
          >
            <IconClipboard size={32} />
          </div>
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
              background: "#4F46E5",
              color: "#fff",
              borderRadius: 16,
              fontWeight: 600,
              fontSize: 16,
              textDecoration: "none",
              transition: "background 0.2s ease",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "#4338CA")}
            onMouseLeave={e => (e.currentTarget.style.background = "#4F46E5")}
          >
            Начать сейчас
          </Link>
        </div>
      )}

      {!loading && hasTasks && (
        <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
          {displayAttempts.map((a, i) => {
            const title = a.assessment_title ?? "Задание";
            const dateStr = a.created_at
              ? new Date(a.created_at).toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" })
              : "";
            const isInProgress = a.status === "in_progress";
            return (
              <li
                key={a.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                  padding: "16px 0",
                  borderBottom: i < displayAttempts.length - 1 ? "1px solid #F1F5F9" : "none",
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 16, fontWeight: 600, color: "#0F172A" }}>{title}</div>
                  <div style={{ fontSize: 14, color: "#94A3B8", marginTop: 4 }}>
                    {isInProgress ? "В процессе" : `${a.percentage.toFixed(0)}% · ${dateStr}`}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    isInProgress ? navigate(`/assessments/${a.assessment_id}`) : navigate(`/attempts/${a.id}`)
                  }
                  style={{
                    padding: "8px 16px",
                    borderRadius: 999,
                    border: "none",
                    cursor: "pointer",
                    fontWeight: 600,
                    fontSize: 13,
                    background: isInProgress ? "#FFFBEB" : "#ECFDF5",
                    color: isInProgress ? "#D97706" : "#059669",
                    flexShrink: 0,
                    transition: "opacity 0.2s ease",
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
    </div>
  );
}

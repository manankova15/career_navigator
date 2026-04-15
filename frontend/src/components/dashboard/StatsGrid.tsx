import { UserProgress } from "../../api/analytics";

export interface StatsGridProps {
  progress: UserProgress | null;
  loading?: boolean;
}

const STATS_CONFIG = [
  {
    label: "Пройдено тестов",
    getValue: (p: UserProgress | null) => (p != null ? String(p.assessments_taken) : "—"),
    iconBg: "#EEF2FF",
    iconPath: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01",
  },
  {
    label: "Лучший результат",
    getValue: (p: UserProgress | null) => (p != null ? `${p.best_score.toFixed(0)}%` : "—"),
    iconBg: "#ECFDF5",
    iconPath: "M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z",
  },
  {
    label: "Средний результат",
    getValue: (p: UserProgress | null) => (p != null ? `${p.avg_score.toFixed(0)}%` : "—"),
    iconBg: "#ECFEFF",
    iconPath: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  },
  {
    label: "Просмотрено вакансий",
    getValue: (p: UserProgress | null) => (p != null ? String(p.vacancy_views) : "—"),
    iconBg: "#FFF1F2",
    iconPath: "M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z",
  },
];

function StatIcon({ path, bg }: { path: string; bg: string }) {
  return (
    <div
      style={{
        width: 44,
        height: 44,
        borderRadius: 14,
        background: bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <svg width={22} height={22} viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <path d={path} />
      </svg>
    </div>
  );
}

export default function StatsGrid({ progress, loading }: StatsGridProps) {
  const metaText = progress != null ? "Данные обновлены сегодня" : "Начните с первого шага";

  return (
    <div
      style={{ gap: 20 }}
      className="dashboard-stats-grid"
      role="region"
      aria-label="Статистика"
    >
      {STATS_CONFIG.map(({ label, getValue, iconBg, iconPath }) => (
        <div
          key={label}
          style={{
            background: "#FFFFFF",
            border: "1px solid #E2E8F0",
            borderRadius: 22,
            padding: 24,
            minHeight: 150,
            boxShadow: "var(--shadow-card)",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = "translateY(-2px)";
            e.currentTarget.style.boxShadow = "var(--shadow-card-hover)";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.boxShadow = "var(--shadow-card)";
          }}
        >
          <StatIcon path={iconPath} bg={iconBg} />
          <div style={{ fontSize: 40, fontWeight: 700, color: "#0F172A", letterSpacing: "-0.02em", lineHeight: 1, marginTop: 14 }}>
            {loading ? <span style={{ fontSize: 16, color: "#94A3B8" }}>—</span> : getValue(progress)}
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#0F172A", marginTop: 8 }}>{label}</div>
          <div style={{ fontSize: 13, color: "#94A3B8", marginTop: 4 }}>{metaText}</div>
        </div>
      ))}
    </div>
  );
}

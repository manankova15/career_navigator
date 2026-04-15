import { Link } from "react-router-dom";

const ACTIONS = [
  {
    to: "/vacancies",
    title: "Найти вакансии",
    description: "Поиск по 50 000+ позициям",
    gradient: "linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%)",
    iconPath: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z M10 7v3m0 0v3m0-3h3m-3 0H7",
  },
  {
    to: "/recommendations",
    title: "Рекомендации",
    description: "AI-подбор под ваш опыт и цели",
    gradient: "linear-gradient(135deg, #ECFEFF 0%, #DFF7F8 100%)",
    iconPath: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  },
  {
    to: "/assessments",
    title: "Задания",
    description: "Подготовьтесь к интервью и оценке",
    gradient: "linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)",
    iconPath: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
  },
  {
    to: "/profile",
    title: "Профиль",
    description: "Обновите навыки и карьерные данные",
    gradient: "linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)",
    iconPath: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  },
];

export default function QuickActions() {
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E2E8F0",
        borderRadius: 28,
        padding: 28,
        boxShadow: "var(--shadow-card)",
      }}
      role="region"
      aria-label="Быстрые действия"
    >
      <h2 style={{ fontSize: 28, fontWeight: 700, lineHeight: "34px", color: "#0F172A", margin: "0 0 8px" }}>
        Быстрые действия
      </h2>
      <p style={{ fontSize: 16, color: "#64748B", margin: "0 0 24px" }}>
        Начните с самого важного шага уже сейчас
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 18,
        }}
        className="dashboard-quick-actions-grid"
      >
        {ACTIONS.map(({ to, title, description, gradient, iconPath }) => (
          <Link
            key={to}
            to={to}
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div
              style={{
                background: gradient,
                borderRadius: 22,
                padding: 22,
                minHeight: 170,
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                border: "1px solid transparent",
                cursor: "pointer",
                transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = "translateY(-3px)";
                e.currentTarget.style.boxShadow = "var(--shadow-card-hover)";
                e.currentTarget.style.borderColor = "rgba(79, 70, 229, 0.3)";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "none";
                e.currentTarget.style.borderColor = "transparent";
              }}
            >
              <div>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 14,
                    background: "rgba(255,255,255,0.8)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: 14,
                  }}
                >
                  <svg width={22} height={22} viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    <path d={iconPath} />
                  </svg>
                </div>
                <div style={{ fontSize: 20, fontWeight: 600, color: "#0F172A", marginBottom: 6 }}>{title}</div>
                <div style={{ fontSize: 14, color: "#64748B", lineHeight: 1.4 }}>{description}</div>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#4F46E5", marginTop: 12 }}>
                Перейти →
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

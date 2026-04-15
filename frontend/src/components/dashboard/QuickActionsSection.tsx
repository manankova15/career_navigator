import { Link } from "react-router-dom";

const ACTIONS = [
  {
    to: "/vacancies",
    title: "Найти вакансии",
    description: "Поиск по 50 000+ позициям",
    gradient: "linear-gradient(135deg, #EEF2FF 0%, #DDE7FF 100%)",
    iconAccent: "#5B5CEB",
    iconPath: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z M10 7v3m0 0v3m0-3h3m-3 0H7",
  },
  {
    to: "/recommendations",
    title: "Рекомендации",
    description: "AI-подбор под ваш опыт и цели",
    gradient: "linear-gradient(135deg, #ECFEFF 0%, #DDF8F7 100%)",
    iconAccent: "#06B6D4",
    iconPath: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  },
  {
    to: "/assessments",
    title: "Задания",
    description: "Подготовьтесь к интервью и оценке",
    gradient: "linear-gradient(135deg, #FFF7E8 0%, #FCECC8 100%)",
    iconAccent: "#F59E0B",
    iconPath: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
  },
  {
    to: "/profile",
    title: "Профиль",
    description: "Обновите навыки и карьерные данные",
    gradient: "linear-gradient(135deg, #F5F0FF 0%, #E8DEFF 100%)",
    iconAccent: "#8B5CF6",
    iconPath: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  },
];

function IconArrowRight() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

export default function QuickActionsSection() {
  return (
    <section
      className="dashboard-quick-actions-section"
      style={{
        background: "linear-gradient(180deg, #FFFFFF 0%, #F7FAFF 100%)",
        border: "1px solid #E6EAF2",
        borderRadius: 30,
        padding: 28,
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.05)",
      }}
      role="region"
      aria-label="Быстрые действия"
    >
      {/* Subtle background image */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "url(/pictures/abstract-background-for-saas%20(1).webp)",
          backgroundSize: "cover",
          backgroundPosition: "center",
          opacity: 0.06,
          pointerEvents: "none",
        }}
        aria-hidden
      />
      {/* Decorative blur elements */}
      <div
        style={{
          position: "absolute",
          top: -60,
          right: -60,
          width: 240,
          height: 240,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(91,92,235,0.10) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: -80,
          left: -80,
          width: 280,
          height: 280,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(6,182,212,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div style={{ position: "relative", zIndex: 1 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 30, fontWeight: 700, lineHeight: "36px", color: "#0F172A", margin: "0 0 8px" }}>
              Быстрые действия
            </h2>
            <p style={{ fontSize: 18, fontWeight: 400, lineHeight: "28px", color: "#64748B", margin: 0 }}>
              Начните с самого важного шага уже сейчас
            </p>
          </div>
          <span
            style={{
              background: "#EEF2FF",
              color: "#4F46E5",
              border: "1px solid #C7D2FE",
              borderRadius: 999,
              padding: "8px 12px",
              fontSize: 14,
              fontWeight: 600,
              flexShrink: 0,
            }}
          >
            4 направления
          </span>
        </div>

        <div className="dashboard-quick-actions-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          {ACTIONS.map(({ to, title, description, gradient, iconAccent, iconPath }) => (
            <Link key={to} to={to} style={{ textDecoration: "none", color: "inherit" }}>
              <div
                className="dashboard-action-card"
                style={{
                  background: gradient,
                  borderRadius: 24,
                  minHeight: 210,
                  padding: 22,
                  position: "relative",
                  overflow: "hidden",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  border: "1px solid rgba(255,255,255,0.55)",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.55), 0 10px 26px rgba(15,23,42,0.05)",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = "translateY(-4px)";
                  e.currentTarget.style.boxShadow = "0 18px 32px rgba(91,92,235,0.12)";
                  e.currentTarget.style.borderColor = "rgba(91,92,235,0.25)";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = "none";
                  e.currentTarget.style.boxShadow = "inset 0 1px 0 rgba(255,255,255,0.55), 0 10px 26px rgba(15,23,42,0.05)";
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.55)";
                }}
              >
                {/* Soft radial highlight top-right */}
                <div
                  style={{
                    position: "absolute",
                    top: -40,
                    right: -40,
                    width: 140,
                    height: 140,
                    borderRadius: "50%",
                    background: "radial-gradient(circle, rgba(255,255,255,0.5) 0%, transparent 70%)",
                    pointerEvents: "none",
                  }}
                />
                <div style={{ position: "relative", zIndex: 1 }}>
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
                    <div
                      style={{
                        width: 48,
                        height: 48,
                        borderRadius: 16,
                        background: "rgba(255,255,255,0.72)",
                        backdropFilter: "blur(8px)",
                        WebkitBackdropFilter: "blur(8px)",
                        border: "1px solid rgba(255,255,255,0.5)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <svg width={24} height={24} viewBox="0 0 24 24" fill="none" stroke={iconAccent} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                        <path d={iconPath} />
                      </svg>
                    </div>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        background: "rgba(255,255,255,0.68)",
                        color: "#0F172A",
                        borderRadius: 999,
                        padding: "8px 10px",
                        fontSize: 13,
                        fontWeight: 500,
                      }}
                    >
                      <IconArrowRight />
                    </span>
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "#0F172A", marginBottom: 6 }}>{title}</div>
                  <div style={{ fontSize: 16, fontWeight: 400, lineHeight: "24px", color: "#64748B" }}>{description}</div>
                </div>
                <div style={{ fontSize: 16, fontWeight: 600, color: "#5B5CEB", marginTop: 12, position: "relative", zIndex: 1 }}>
                  Перейти →
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

import { Link } from "react-router-dom";

export interface DashboardHeroProps {
  firstName: string;
  heroImageSrc?: string;
}

export default function DashboardHero({ firstName, heroImageSrc = "/pictures/professionals-in-modern-office.webp" }: DashboardHeroProps) {
  return (
    <section
      className="dashboard-hero-glow"
      style={{ position: "relative" }}
      aria-label="Главный блок"
    >
      <div
        className="dashboard-hero-grid"
        style={{
          background: "#FFFFFF",
          border: "1px solid #E6EAF2",
          borderRadius: 32,
          padding: 32,
          minHeight: 420,
          boxShadow: "0 18px 40px rgba(15, 23, 42, 0.06)",
        }}
      >
        {/* Left column */}
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", minWidth: 0 }}>
          <span
            style={{
              display: "inline-block",
              width: "fit-content",
              padding: "8px 14px",
              background: "#EEF2FF",
              color: "#4338CA",
              fontSize: 14,
              fontWeight: 500,
              borderRadius: 999,
              marginBottom: 20,
            }}
          >
            Персональный карьерный навигатор
          </span>
          <h1
            className="dashboard-hero-title"
            style={{
              fontSize: 48,
              fontWeight: 700,
              lineHeight: "56px",
              color: "#0F172A",
              margin: "0 0 16px",
              letterSpacing: "-0.02em",
            }}
          >
            Привет, {firstName}!<br />
            Построй следующий шаг в карьере
          </h1>
          <p
            style={{
              fontSize: 18,
              fontWeight: 400,
              lineHeight: "28px",
              color: "#64748B",
              maxWidth: 560,
              margin: "0 0 28px",
            }}
          >
            Вакансии, AI-рекомендации, задания и развитие навыков — в одном пространстве для карьерного роста
          </p>
          <div className="dashboard-cta-row" style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 24 }}>
            <Link
              to="/vacancies"
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
                boxShadow: "0 4px 14px rgba(79, 70, 229, 0.25)",
                transition: "background 0.2s ease, box-shadow 0.2s ease",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = "#4338CA";
                e.currentTarget.style.boxShadow = "0 6px 20px rgba(79, 70, 229, 0.35)";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = "#4F46E5";
                e.currentTarget.style.boxShadow = "0 4px 14px rgba(79, 70, 229, 0.25)";
              }}
            >
              Найти вакансии
            </Link>
            <Link
              to="/recommendations"
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "14px 22px",
                background: "#FFFFFF",
                color: "#0F172A",
                border: "1px solid #CBD5E1",
                borderRadius: 16,
                fontWeight: 600,
                fontSize: 16,
                textDecoration: "none",
                transition: "background 0.2s ease, border-color 0.2s ease",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = "#F8FAFF";
                e.currentTarget.style.borderColor = "#94A3B8";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = "#FFFFFF";
                e.currentTarget.style.borderColor = "#CBD5E1";
              }}
            >
              Получить рекомендации
            </Link>
          </div>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {["50 000+ вакансий", "AI-рекомендации", "Подготовка к интервью"].map(text => (
              <span
                key={text}
                style={{
                  padding: "6px 12px",
                  background: "#F8FAFF",
                  color: "#64748B",
                  fontSize: 14,
                  fontWeight: 500,
                  borderRadius: 999,
                  border: "1px solid #E2E8F0",
                }}
              >
                {text}
              </span>
            ))}
          </div>
        </div>

        {/* Right column: image card with floating cards */}
        <div
          style={{
            position: "relative",
            minHeight: 360,
            borderRadius: 24,
            overflow: "hidden",
            background: "linear-gradient(135deg, #E0E7FF 0%, #F5F3FF 100%)",
          }}
        >
          <img
            src={heroImageSrc}
            alt="Команда профессионалов у доски в современном офисе"
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center center",
              position: "absolute",
              inset: 0,
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: "linear-gradient(to top, rgba(15,23,42,0.28) 0%, transparent 40%)",
              pointerEvents: "none",
            }}
          />
          {/* Floating card: top right */}
          <div
            style={{
              position: "absolute",
              top: 20,
              right: 20,
              padding: "14px 16px",
              background: "rgba(255,255,255,0.9)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
              borderRadius: 18,
              boxShadow: "0 8px 24px rgba(15,23,42,0.1)",
              minWidth: 160,
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 600, color: "#64748B", marginBottom: 4 }}>AI-рекомендации</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#0F172A" }}>Обновлены сегодня</div>
          </div>
        </div>
      </div>
    </section>
  );
}

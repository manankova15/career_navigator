interface VacanciesIntroHeroProps {
  totalCount: number | null;
}

export default function VacanciesIntroHero({ totalCount }: VacanciesIntroHeroProps) {
  const displayTotal = totalCount != null ? totalCount.toLocaleString("ru-RU") : "—";

  return (
    <section
      className="vacancies-intro-hero"
      style={{
        background: "linear-gradient(135deg, #FFFFFF 0%, #F7FAFF 100%)",
        border: "1px solid #E6EAF2",
        borderRadius: 30,
        padding: "22px 28px",
        position: "relative",
        overflow: "hidden",
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.05)",
      }}
      aria-label="Введение"
    >
      {/* Decorative glows */}
      <div
        style={{
          position: "absolute",
          top: -40,
          right: -40,
          width: 220,
          height: 220,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(91,92,235,0.10) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: -60,
          left: -60,
          width: 260,
          height: 260,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(6,182,212,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div className="vacancies-intro-grid" style={{ position: "relative", zIndex: 1, display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 24, alignItems: "start" }}>
        {/* Left column */}
        <div>
          <span
            style={{
              display: "inline-block",
              background: "#EEF2FF",
              color: "#4338CA",
              border: "1px solid #C7D2FE",
              borderRadius: 999,
              padding: "8px 14px",
              fontSize: 14,
              fontWeight: 600,
              marginBottom: 16,
            }}
          >
            Карьерные возможности
          </span>
          <h1
            className="vacancies-intro-title"
            style={{
              fontSize: 44,
              fontWeight: 700,
              lineHeight: "50px",
              color: "#0F172A",
              margin: "0 0 14px",
              letterSpacing: "-0.02em",
            }}
          >
            Вакансии, которые двигают карьеру вперед
          </h1>
          <p
            style={{
              fontSize: 18,
              fontWeight: 400,
              lineHeight: "28px",
              color: "#64748B",
              margin: "0 0 20px",
              maxWidth: 520,
            }}
          >
            Подбирайте подходящие роли, фильтруйте по навыкам и сохраняйте лучшие возможности в одном карьерном пространстве
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <span
              style={{
                background: "#FFFFFF",
                border: "1px solid #E6EAF2",
                color: "#64748B",
                borderRadius: 999,
                padding: "10px 14px",
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              {displayTotal} вакансий
            </span>
            <span
              style={{
                background: "#FFFFFF",
                border: "1px solid #E6EAF2",
                color: "#64748B",
                borderRadius: 999,
                padding: "10px 14px",
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              AI-подбор
            </span>
            <span
              style={{
                background: "#FFFFFF",
                border: "1px solid #E6EAF2",
                color: "#64748B",
                borderRadius: 999,
                padding: "10px 14px",
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              Подготовка к интервью
            </span>
          </div>
        </div>

        {/* Right column: insight card + illustration */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16, alignItems: "stretch", width: "100%" }}>
          <div
            style={{
              background: "rgba(255,255,255,0.78)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
              border: "1px solid rgba(230,234,242,0.9)",
              borderRadius: 24,
              padding: 20,
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            <div style={{ fontSize: 13, fontWeight: 500, color: "#64748B" }}>
              Сегодня
            </div>
            <div style={{ fontSize: 42, fontWeight: 700, lineHeight: 1, color: "#0F172A", letterSpacing: "-0.02em" }}>
              {displayTotal}
            </div>
            <div style={{ fontSize: 15, color: "#64748B", lineHeight: 1.4 }}>
              актуальных вакансий
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "flex-end" }}>
            <img
              src="/pictures/network-diagram-on-white-bg.png"
              alt=""
              role="presentation"
              className="vacancies-intro-illustration"
              style={{
                maxWidth: 380,
                width: "100%",
                height: "auto",
                opacity: 0.72,
                objectFit: "contain",
              }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

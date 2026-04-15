export interface VacanciesEmptyStateProps {
  onResetFilters: () => void;
  onShowAll: () => void;
}

function IconSearch() {
  return (
    <svg width={40} height={40} viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.35-4.35" />
    </svg>
  );
}

export default function VacanciesEmptyState({ onResetFilters, onShowAll }: VacanciesEmptyStateProps) {
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px dashed #D7E0EE",
        borderRadius: 28,
        padding: 40,
        textAlign: "center",
        maxWidth: 480,
        margin: "0 auto",
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 20,
          background: "#F8FAFF",
          border: "1px solid #E6EAF2",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 20px",
        }}
      >
        <IconSearch />
      </div>
      <h3
        style={{
          fontSize: 22,
          fontWeight: 700,
          color: "#0F172A",
          margin: "0 0 10px",
          lineHeight: 1.35,
        }}
      >
        Подходящих вакансий пока не найдено
      </h3>
      <p
        style={{
          fontSize: 16,
          color: "#64748B",
          lineHeight: 1.5,
          margin: "0 0 24px",
        }}
      >
        Попробуйте изменить запрос или сбросить часть фильтров
      </p>
      <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={onResetFilters}
          style={{
            padding: "14px 22px",
            background: "#F8FAFF",
            border: "1px solid #D8E0EE",
            color: "#0F172A",
            borderRadius: 16,
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
            transition: "background 0.2s ease, border-color 0.2s ease",
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = "#EEF2FF";
            e.currentTarget.style.borderColor = "#C7D2FE";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = "#F8FAFF";
            e.currentTarget.style.borderColor = "#D8E0EE";
          }}
        >
          Сбросить фильтры
        </button>
        <button
          type="button"
          onClick={onShowAll}
          style={{
            padding: "14px 22px",
            background: "#5B5CEB",
            border: "none",
            color: "#fff",
            borderRadius: 16,
            fontSize: 15,
            fontWeight: 600,
            cursor: "pointer",
            transition: "background 0.2s ease",
          }}
          onMouseEnter={e => (e.currentTarget.style.background = "#4F46E5")}
          onMouseLeave={e => (e.currentTarget.style.background = "#5B5CEB")}
        >
          Показать все вакансии
        </button>
      </div>
    </div>
  );
}

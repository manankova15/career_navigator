import React from "react";

const QUICK_FILTERS = [
  { id: "", label: "Все" },
  { id: "Frontend", label: "Frontend" },
  { id: "Backend", label: "Backend" },
  { id: "Python", label: "Python" },
  { id: "React", label: "React" },
  { id: "Удаленно", label: "Удаленно" },
  { id: "Senior", label: "Senior" },
];

export interface VacanciesToolbarProps {
  total: number;
  quickFilterValue: string;
  onQuickFilter: (value: string) => void;
  sortValue: string;
  onSortChange: (value: string) => void;
}

export default function VacanciesToolbar({
  total,
  quickFilterValue,
  onQuickFilter,
  sortValue,
  onSortChange,
}: VacanciesToolbarProps) {
  return (
    <div
      className="vacancies-toolbar"
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 16,
        flexWrap: "wrap",
        marginBottom: 24,
      }}
    >
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
        {QUICK_FILTERS.map(({ id, label }) => {
          const isActive = quickFilterValue === id;
          return (
            <button
              key={id || "all"}
              type="button"
              onClick={() => onQuickFilter(id)}
              style={{
                background: isActive ? "#EEF2FF" : "#FFFFFF",
                border: `1px solid ${isActive ? "#C7D2FE" : "#E6EAF2"}`,
                color: isActive ? "#4338CA" : "#475569",
                borderRadius: 999,
                padding: "10px 14px",
                fontSize: 14,
                fontWeight: 500,
                cursor: "pointer",
                transition: "background 0.2s ease, border-color 0.2s ease, color 0.2s ease",
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.background = "#F8FAFF";
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.background = "#FFFFFF";
                }
              }}
            >
              {label}
            </button>
          );
        })}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <span style={{ fontSize: 14, color: "#64748B", fontWeight: 500 }}>
          Найдено {total.toLocaleString("ru-RU")} вакансий
        </span>
        <select
          value={sortValue}
          onChange={e => onSortChange(e.target.value)}
          style={{
            background: "#FFFFFF",
            border: "1px solid #E6EAF2",
            borderRadius: 16,
            height: 44,
            padding: "0 14px",
            fontSize: 14,
            color: "#0F172A",
            fontWeight: 500,
            cursor: "pointer",
            appearance: "none",
            minWidth: 180,
          }}
          aria-label="Сортировка"
        >
          <option value="relevance">Сначала подходящие</option>
          <option value="date">По дате</option>
          <option value="salary">По зарплате</option>
        </select>
      </div>
    </div>
  );
}

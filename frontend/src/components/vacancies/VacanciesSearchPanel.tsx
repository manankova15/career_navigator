import React from "react";
import {
  EMPLOYMENT_TYPES,
  EXPERIENCE_LEVELS,
  PAGE_SIZE_OPTIONS,
  PROFESSION_AREAS,
  SALARY_CURRENCIES,
  SCHEDULE_TYPES,
  SPECIALIZATION_OPTIONS,
  WORK_FORMATS,
} from "./vacanciesConstants";

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: 11,
  fontWeight: 600,
  color: "#94A3B8",
  textTransform: "uppercase",
  letterSpacing: "0.6px",
  marginBottom: 6,
};

const sectionTitle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 700,
  color: "#0F172A",
  marginBottom: 12,
  marginTop: 4,
};

export interface VacancySearchDraft {
  query: string;
  profession_area: string[];
  specialization: string;
  city: string;
  country: string;
  work_format: string[];
  employment_type: string[];
  schedule_type: string[];
  experience_level: string;
  salary_from: string;
  salary_currency: string;
  has_salary: boolean;
  pageSize: number;
}

export interface VacanciesSearchPanelProps {
  draft: VacancySearchDraft;
  setDraft: React.Dispatch<React.SetStateAction<VacancySearchDraft>>;
  onSearch: (e: React.FormEvent) => void;
  filtersOpen: boolean;
  setFiltersOpen: (v: boolean) => void;
  filtersActive: boolean;
  onApplyFilters: () => void;
}

function IconSearch() {
  return (
    <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.35-4.35" />
    </svg>
  );
}

function IconSliders() {
  return (
    <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <line x1="4" y1="21" x2="4" y2="14" />
      <line x1="4" y1="10" x2="4" y2="3" />
      <line x1="12" y1="21" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12" y2="3" />
      <line x1="20" y1="21" x2="20" y2="16" />
      <line x1="20" y1="12" x2="20" y2="3" />
      <line x1="1" y1="14" x2="7" y2="14" />
      <line x1="9" y1="8" x2="15" y2="8" />
      <line x1="17" y1="16" x2="23" y2="16" />
    </svg>
  );
}

function toggleListValue(list: string[], value: string): string[] {
  if (list.includes(value)) return list.filter(v => v !== value);
  return [...list, value];
}

const inputBase: React.CSSProperties = {
  width: "100%",
  height: 44,
  border: "1px solid #D8E0EE",
  borderRadius: 14,
  padding: "0 14px",
  fontSize: 15,
};

function CheckboxRow({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: () => void;
}) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        cursor: "pointer",
        fontSize: 14,
        color: "#334155",
        marginBottom: 6,
      }}
    >
      <input type="checkbox" checked={checked} onChange={onChange} />
      {label}
    </label>
  );
}

export default function VacanciesSearchPanel({
  draft,
  setDraft,
  onSearch,
  filtersOpen,
  setFiltersOpen,
  filtersActive,
  onApplyFilters,
}: VacanciesSearchPanelProps) {
  return (
    <div
      className="vacancies-search-panel"
      style={{
        marginTop: 18,
        position: "relative",
        zIndex: 3,
        background: "rgba(255,255,255,0.96)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        border: "1px solid rgba(230,234,242,0.95)",
        borderRadius: 24,
        padding: 20,
        boxShadow: "0 16px 32px rgba(15, 23, 42, 0.06)",
      }}
    >
      <form onSubmit={onSearch}>
        <div className="vacancies-search-row" style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "stretch" }}>
          <div style={{ flex: "1 1 220px", minWidth: 0 }}>
            <input
              type="text"
              placeholder="Название, компания, описание или навыки…"
              value={draft.query}
              onChange={e => setDraft(d => ({ ...d, query: e.target.value }))}
              style={{
                width: "100%",
                height: 56,
                border: "1px solid #D8E0EE",
                background: "#FFFFFF",
                borderRadius: 18,
                paddingLeft: 18,
                fontSize: 16,
                color: "#0F172A",
                outline: "none",
                transition: "border-color 0.2s ease, box-shadow 0.2s ease",
              }}
              onFocus={e => {
                e.currentTarget.style.borderColor = "#5B5CEB";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(91,92,235,0.15)";
              }}
              onBlur={e => {
                e.currentTarget.style.borderColor = "#D8E0EE";
                e.currentTarget.style.boxShadow = "none";
              }}
              aria-label="Поиск вакансий"
            />
          </div>
          <button
            type="submit"
            style={{
              height: 56,
              background: "#5B5CEB",
              color: "#fff",
              border: "none",
              borderRadius: 18,
              padding: "0 22px",
              fontSize: 16,
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "0 4px 14px rgba(91,92,235,0.25)",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <IconSearch />
            Найти
          </button>
          <button
            type="button"
            onClick={() => setFiltersOpen(!filtersOpen)}
            style={{
              height: 56,
              background: filtersOpen ? "#EEF2FF" : "#F8FAFF",
              border: "1px solid #D8E0EE",
              color: "#0F172A",
              borderRadius: 18,
              padding: "0 22px",
              fontSize: 16,
              fontWeight: 600,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <IconSliders />
            Фильтры
            {filtersActive && (
              <span
                style={{
                  background: "#5B5CEB",
                  color: "#fff",
                  borderRadius: 999,
                  width: 20,
                  height: 20,
                  fontSize: 11,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                }}
              >
                •
              </span>
            )}
          </button>
        </div>

        {filtersOpen && (
          <div style={{ marginTop: 20, paddingTop: 20, borderTop: "1px solid #E6EAF2" }}>
            <div style={sectionTitle}>Категория и специализация</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 20 }}>
              <div style={{ gridColumn: "1 / -1" }}>
                <label style={labelStyle}>Профессиональная область</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 16px" }}>
                  {PROFESSION_AREAS.map(o => (
                    <CheckboxRow
                      key={o.value}
                      checked={draft.profession_area.includes(o.value)}
                      label={o.label}
                      onChange={() =>
                        setDraft(d => ({
                          ...d,
                          profession_area: toggleListValue(d.profession_area, o.value),
                        }))
                      }
                    />
                  ))}
                </div>
              </div>
              <div>
                <label style={labelStyle}>Специализация</label>
                <select
                  value={draft.specialization}
                  onChange={e => setDraft(d => ({ ...d, specialization: e.target.value }))}
                  style={{ ...inputBase, appearance: "none", background: "#fff" }}
                >
                  <option value="">Любая</option>
                  {SPECIALIZATION_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={sectionTitle}>Локация</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 20 }}>
              <div>
                <label style={labelStyle}>Город</label>
                <input
                  type="text"
                  placeholder="Москва, Санкт-Петербург…"
                  value={draft.city}
                  onChange={e => setDraft(d => ({ ...d, city: e.target.value }))}
                  style={inputBase}
                />
              </div>
              <div>
                <label style={labelStyle}>Страна</label>
                <input
                  type="text"
                  placeholder="Россия…"
                  value={draft.country}
                  onChange={e => setDraft(d => ({ ...d, country: e.target.value }))}
                  style={inputBase}
                />
              </div>
            </div>

            <div style={sectionTitle}>Условия работы</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 20 }}>
              <div>
                <label style={labelStyle}>Формат работы</label>
                {WORK_FORMATS.map(o => (
                  <CheckboxRow
                    key={o.value}
                    checked={draft.work_format.includes(o.value)}
                    label={o.label}
                    onChange={() =>
                      setDraft(d => ({
                        ...d,
                        work_format: toggleListValue(d.work_format, o.value),
                      }))
                    }
                  />
                ))}
              </div>
              <div>
                <label style={labelStyle}>Тип занятости</label>
                {EMPLOYMENT_TYPES.map(o => (
                  <CheckboxRow
                    key={o.value}
                    checked={draft.employment_type.includes(o.value)}
                    label={o.label}
                    onChange={() =>
                      setDraft(d => ({
                        ...d,
                        employment_type: toggleListValue(d.employment_type, o.value),
                      }))
                    }
                  />
                ))}
              </div>
              <div>
                <label style={labelStyle}>График</label>
                {SCHEDULE_TYPES.map(o => (
                  <CheckboxRow
                    key={o.value}
                    checked={draft.schedule_type.includes(o.value)}
                    label={o.label}
                    onChange={() =>
                      setDraft(d => ({
                        ...d,
                        schedule_type: toggleListValue(d.schedule_type, o.value),
                      }))
                    }
                  />
                ))}
              </div>
              <div>
                <label style={labelStyle}>Опыт</label>
                <select
                  value={draft.experience_level}
                  onChange={e => setDraft(d => ({ ...d, experience_level: e.target.value }))}
                  style={{ ...inputBase, appearance: "none", background: "#fff" }}
                >
                  {EXPERIENCE_LEVELS.map(o => (
                    <option key={o.value || "any"} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={sectionTitle}>Зарплата</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16, marginBottom: 20 }}>
              <div>
                <label style={labelStyle}>Зарплата от (в месяц)</label>
                <input
                  type="number"
                  min={0}
                  placeholder="Не важно"
                  value={draft.salary_from}
                  onChange={e => setDraft(d => ({ ...d, salary_from: e.target.value }))}
                  style={inputBase}
                />
              </div>
              <div>
                <label style={labelStyle}>Валюта</label>
                <select
                  value={draft.salary_currency}
                  onChange={e => setDraft(d => ({ ...d, salary_currency: e.target.value }))}
                  style={{ ...inputBase, appearance: "none", background: "#fff" }}
                >
                  {SALARY_CURRENCIES.map(o => (
                    <option key={o.value || "any"} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: "flex", alignItems: "flex-end", paddingBottom: 4 }}>
                <CheckboxRow
                  checked={draft.has_salary}
                  label="Только с указанной зарплатой"
                  onChange={() => setDraft(d => ({ ...d, has_salary: !d.has_salary }))}
                />
              </div>
            </div>

            <div
              style={{
                display: "flex",
                gap: 16,
                alignItems: "flex-end",
                flexWrap: "wrap",
                justifyContent: "space-between",
                marginTop: 4,
              }}
            >
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={onApplyFilters}
                  style={{
                    padding: "12px 22px",
                    background: "#5B5CEB",
                    color: "#fff",
                    border: "none",
                    borderRadius: 16,
                    cursor: "pointer",
                    fontWeight: 600,
                    fontSize: 15,
                  }}
                >
                  Применить фильтры
                </button>
                <button
                  type="button"
                  onClick={() => setFiltersOpen(false)}
                  style={{
                    padding: "12px 22px",
                    background: "#FFFFFF",
                    color: "#0F172A",
                    border: "1px solid #D8E0EE",
                    borderRadius: 16,
                    cursor: "pointer",
                    fontWeight: 600,
                    fontSize: 15,
                  }}
                >
                  Закрыть
                </button>
              </div>
              <div style={{ minWidth: 220 }}>
                <label style={labelStyle}>Показывать на странице</label>
                <select
                  value={draft.pageSize}
                  onChange={e => setDraft(d => ({ ...d, pageSize: Number(e.target.value) }))}
                  style={{ ...inputBase, appearance: "none", background: "#fff" }}
                >
                  {PAGE_SIZE_OPTIONS.map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}

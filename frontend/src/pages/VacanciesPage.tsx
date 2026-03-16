import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getVacancies, Vacancy, VacanciesPage as VPage } from "../api/vacancies";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";

const SENIORITY_OPTIONS = [
  { value: "", label: "Любой уровень" },
  { value: "junior", label: "Junior" },
  { value: "middle", label: "Middle" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead / Principal" },
];

export default function VacanciesPage() {
  const [data, setData] = useState<VPage | null>(null);
  const [query, setQuery] = useState("");
  const [inputVal, setInputVal] = useState("");
  const [locationVal, setLocationVal] = useState("");
  const [seniority, setSeniority] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function load(p: number, q: string, loc: string, sen: string) {
    setLoading(true); setError("");
    getVacancies(p, q, loc, sen)
      .then(d => { setData(d); setPage(p); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(1, "", "", ""); }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setQuery(inputVal);
    load(1, inputVal, locationVal, seniority);
  }

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;

  function salary(v: Vacancy) {
    if (!v.salary_from && !v.salary_to) return null;
    const parts = [v.salary_from, v.salary_to].filter(Boolean).map(n => n!.toLocaleString("ru-RU"));
    return `${parts.join(" – ")} ${v.currency ?? "₽"}`.trim();
  }

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "#0F172A", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
          Вакансии
        </h1>
        <p style={{ color: "#64748B", margin: 0, fontSize: 15 }}>
          {data ? `Найдено ${data.total.toLocaleString("ru-RU")} вакансий` : "Ищем подходящие вакансии…"}
        </p>
      </div>

      {/* Search form */}
      <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px", marginBottom: 28, boxShadow: "0 2px 8px rgba(15,23,42,0.04)" }}>
        <form onSubmit={handleSearch}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
            <div style={{ flex: "2 1 220px" }}>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 6 }}>Должность или навык</label>
              <input
                className="form-input"
                placeholder="Python, React, Product Manager…"
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
              />
            </div>
            <div style={{ flex: "1 1 160px" }}>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 6 }}>Город</label>
              <input
                className="form-input"
                placeholder="Москва, Удалённо…"
                value={locationVal}
                onChange={e => setLocationVal(e.target.value)}
              />
            </div>
            <div style={{ flex: "1 1 160px" }}>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 6 }}>Уровень</label>
              <div style={{ position: "relative" }}>
                <select
                  className="form-input"
                  style={{ appearance: "none", paddingRight: 32 }}
                  value={seniority}
                  onChange={e => setSeniority(e.target.value)}
                >
                  {SENIORITY_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
                <span style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", pointerEvents: "none", color: "#94A3B8", fontSize: 11 }}>▼</span>
              </div>
            </div>
            <button
              type="submit"
              style={{
                flexShrink: 0,
                padding: "10px 24px",
                background: "#3B5BDB",
                color: "#fff",
                border: "none",
                borderRadius: 12,
                cursor: "pointer",
                fontWeight: 700,
                fontSize: 14,
                boxShadow: "0 2px 8px rgba(59,91,219,0.25)",
                transition: "all 0.15s",
                height: 42,
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "#2F4AC2"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "#3B5BDB"; }}
            >
              Найти
            </button>
          </div>
        </form>
      </div>

      {error && <ErrorBanner message={error} />}
      {loading && <Spinner />}

      {!loading && data && (
        <>
          {data.items.length === 0 && (
            <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "48px", textAlign: "center" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🔍</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#0F172A", marginBottom: 8 }}>Вакансий не найдено</div>
              <div style={{ fontSize: 14, color: "#64748B" }}>Попробуйте изменить запрос или убрать фильтры</div>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16, marginBottom: 28 }}>
            {data.items.map(v => (
              <div key={v.id} className="hoverable-card" style={{
                background: "#fff",
                border: "1.5px solid #E2E8F0",
                borderRadius: 20,
                padding: "20px",
                display: "flex",
                flexDirection: "column",
                gap: 10,
                boxShadow: "0 1px 3px rgba(15,23,42,0.05)",
              }}>
                <Link to={`/vacancies/${v.id}`} className="card-title-link" style={{ fontWeight: 700, color: "#0F172A", textDecoration: "none", fontSize: 15, lineHeight: 1.3 }}>
                  {v.title}
                </Link>
                <div style={{ fontSize: 14, color: "#3B5BDB", fontWeight: 500 }}>{v.company}</div>
                {v.location && (
                  <div style={{ display: "flex", alignItems: "center", gap: 5, color: "#64748B", fontSize: 13 }}>
                    <span>📍</span> {v.location}
                  </div>
                )}

                {/* Tags row */}
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {v.seniority && (
                    <span style={{ background: "#F1F5F9", color: "#475569", fontSize: 11, fontWeight: 500, borderRadius: 999, padding: "3px 10px" }}>
                      {v.seniority}
                    </span>
                  )}
                  {v.employment_type && (
                    <span style={{ background: "#F1F5F9", color: "#475569", fontSize: 11, fontWeight: 500, borderRadius: 999, padding: "3px 10px" }}>
                      {v.employment_type}
                    </span>
                  )}
                </div>

                {salary(v) && (
                  <div style={{ fontSize: 14, color: "#0F172A", fontWeight: 700 }}>
                    {salary(v)}
                  </div>
                )}

                {v.skills && v.skills.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                    {v.skills.slice(0, 4).map(s => (
                      <span key={s} style={{ background: "#EEF2FF", color: "#3B5BDB", fontSize: 11, fontWeight: 500, borderRadius: 999, padding: "3px 10px" }}>
                        {s}
                      </span>
                    ))}
                    {v.skills.length > 4 && (
                      <span style={{ background: "#F1F5F9", color: "#64748B", fontSize: 11, borderRadius: 999, padding: "3px 10px" }}>
                        +{v.skills.length - 4}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", justifyContent: "center" }}>
              <button
                style={{ padding: "9px 18px", border: "1.5px solid #E2E8F0", borderRadius: 10, background: "#fff", cursor: page <= 1 ? "not-allowed" : "pointer", fontWeight: 500, fontSize: 14, color: page <= 1 ? "#CBD5E1" : "#334155", transition: "all 0.15s" }}
                disabled={page <= 1}
                onClick={() => load(page - 1, query, locationVal, seniority)}
                onMouseEnter={e => { if (page > 1) e.currentTarget.style.borderColor = "#3B5BDB"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "#E2E8F0"; }}
              >
                ← Назад
              </button>
              <div style={{ display: "flex", gap: 4 }}>
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                  const p = i + 1;
                  return (
                    <button key={p} onClick={() => load(p, query, locationVal, seniority)} style={{
                      width: 36, height: 36, border: "1.5px solid", borderRadius: 8, cursor: "pointer", fontSize: 13, fontWeight: 600,
                      borderColor: p === page ? "#3B5BDB" : "#E2E8F0",
                      background: p === page ? "#EEF2FF" : "#fff",
                      color: p === page ? "#3B5BDB" : "#334155",
                      transition: "all 0.15s",
                    }}>
                      {p}
                    </button>
                  );
                })}
              </div>
              <button
                style={{ padding: "9px 18px", border: "1.5px solid #E2E8F0", borderRadius: 10, background: "#fff", cursor: page >= totalPages ? "not-allowed" : "pointer", fontWeight: 500, fontSize: 14, color: page >= totalPages ? "#CBD5E1" : "#334155", transition: "all 0.15s" }}
                disabled={page >= totalPages}
                onClick={() => load(page + 1, query, locationVal, seniority)}
                onMouseEnter={e => { if (page < totalPages) e.currentTarget.style.borderColor = "#3B5BDB"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "#E2E8F0"; }}
              >
                Вперёд →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

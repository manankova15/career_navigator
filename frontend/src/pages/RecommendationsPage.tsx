import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getRecommendations,
  refreshRecommendations,
  getSkillGap,
  Recommendation,
  SkillGap,
} from "../api/recommendations";
import { getVacancy, Vacancy } from "../api/vacancies";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [vacancyMap, setVacancyMap] = useState<Map<string, Vacancy>>(new Map());
  const [skillGap, setSkillGap] = useState<SkillGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadVacancyDetails(recList: Recommendation[]) {
    const details = await Promise.all(
      recList.map(r => getVacancy(r.vacancy_id).catch(() => null)),
    );
    const map = new Map<string, Vacancy>();
    details.forEach((v, i) => { if (v) map.set(recList[i].vacancy_id, v); });
    setVacancyMap(map);
  }

  function load() {
    setLoading(true);
    setError("");
    Promise.all([
      getRecommendations(),
      getSkillGap().then(r => r.gaps).catch(() => []),
    ])
      .then(([recList, sg]) => {
        setRecs(recList);
        setSkillGap(sg);
        return loadVacancyDetails(recList);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await refreshRecommendations();
      load();
    } catch (e: any) {
      setError(e.message);
      setRefreshing(false);
    }
  }

  const maxImportance = Math.max(...skillGap.map(s => s.importance_score), 1);

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 32, flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "#0F172A", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
            Рекомендации
          </h1>
          <p style={{ color: "#64748B", margin: 0, fontSize: 15 }}>
            AI подобрал вакансии на основе вашего профиля и навыков
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          style={{
            padding: "10px 20px", background: refreshing ? "#F1F5F9" : "#3B5BDB",
            color: refreshing ? "#94A3B8" : "#fff",
            border: "none", borderRadius: 12, cursor: refreshing ? "not-allowed" : "pointer",
            fontWeight: 600, fontSize: 14, transition: "all 0.15s",
            boxShadow: refreshing ? "none" : "0 2px 8px rgba(59,91,219,0.25)",
          }}
        >
          {refreshing ? "Обновляем…" : "↻ Обновить"}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {loading && <Spinner />}

      {!loading && recs.length === 0 && (
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "48px", textAlign: "center", boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <div style={{ fontSize: 44, marginBottom: 16 }}>✦</div>
          <div style={{ fontSize: 17, fontWeight: 700, color: "#0F172A", marginBottom: 8 }}>Рекомендаций пока нет</div>
          <p style={{ color: "#64748B", fontSize: 14, lineHeight: 1.6, maxWidth: 360, margin: "0 auto 24px" }}>
            Заполните профиль (навыки и желаемую должность), затем нажмите «Обновить» — AI сформирует персональные рекомендации.
          </p>
          <Link to="/profile" style={{ display: "inline-flex", padding: "10px 22px", background: "#3B5BDB", color: "#fff", borderRadius: 10, textDecoration: "none", fontWeight: 600, fontSize: 14 }}>
            Заполнить профиль →
          </Link>
        </div>
      )}

      {!loading && recs.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16, marginBottom: 40 }}>
          {recs.map(rec => {
            const vacancy = vacancyMap.get(rec.vacancy_id);
            const title = vacancy?.title ?? rec.vacancy?.title ?? "Вакансия";
            const company = vacancy?.company ?? rec.vacancy?.company;
            const location = vacancy?.location ?? rec.vacancy?.location;
            const score = Math.round(rec.score * 100);
            const scoreColor = score >= 80 ? "#059669" : score >= 60 ? "#D97706" : "#64748B";
            const scoreBg = score >= 80 ? "#ECFDF5" : score >= 60 ? "#FFFBEB" : "#F1F5F9";

            return (
              <div key={rec.id} className="hoverable-card" style={{
                background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20,
                padding: "20px", display: "flex", flexDirection: "column", gap: 10,
                boxShadow: "0 1px 3px rgba(15,23,42,0.05)",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                  <Link
                    to={`/vacancies/${rec.vacancy_id}`}
                    className="card-title-link"
                    style={{ fontWeight: 700, color: "#0F172A", textDecoration: "none", fontSize: 15, lineHeight: 1.3, flex: 1 }}
                  >
                    {title}
                  </Link>
                  <span style={{ background: scoreBg, color: scoreColor, fontSize: 12, fontWeight: 700, borderRadius: 999, padding: "4px 10px", whiteSpace: "nowrap", flexShrink: 0 }}>
                    {score}% match
                  </span>
                </div>
                {company && <div style={{ color: "#3B5BDB", fontSize: 13, fontWeight: 500 }}>{company}</div>}
                {location && (
                  <div style={{ display: "flex", alignItems: "center", gap: 5, color: "#64748B", fontSize: 13 }}>
                    <span>📍</span> {location}
                  </div>
                )}
                {rec.reason && (
                  <div style={{ fontSize: 12, color: "#475569", background: "#F8FAFC", borderRadius: 10, padding: "8px 12px", lineHeight: 1.5, border: "1px solid #E2E8F0" }}>
                    {rec.reason}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Skill gap analysis */}
      {skillGap.length > 0 && (
        <>
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ fontSize: 22, fontWeight: 800, color: "#0F172A", margin: "0 0 6px", letterSpacing: "-0.3px" }}>
              Анализ пробелов в навыках
            </h2>
            <p style={{ color: "#64748B", margin: 0, fontSize: 14 }}>
              Навыки, которые наиболее востребованы в ваших целевых вакансиях
            </p>
          </div>
          <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "24px", boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
            <div style={{ display: "grid", gap: 18 }}>
              {skillGap.slice(0, 10).map(sg => (
                <div key={sg.skill_name}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, alignItems: "baseline" }}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: "#0F172A" }}>{sg.skill_name}</span>
                    <span style={{ fontSize: 12, color: "#94A3B8" }}>
                      {sg.frequency} вакансий
                    </span>
                  </div>
                  <div style={{ background: "#F1F5F9", borderRadius: 999, height: 6, overflow: "hidden" }}>
                    <div style={{
                      width: `${(sg.importance_score / maxImportance) * 100}%`,
                      background: "linear-gradient(90deg, #3B5BDB, #5C7CFA)",
                      borderRadius: 999, height: "100%",
                      transition: "width 0.4s ease",
                    }} />
                  </div>
                  {sg.recommended_resources.length > 0 && (
                    <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 4 }}>
                      📚 {sg.recommended_resources.slice(0, 2).join(" · ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

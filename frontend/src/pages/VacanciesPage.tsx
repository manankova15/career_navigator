import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { getVacancies, VacanciesPage as VPage } from "../api/vacancies";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";
import VacanciesIntroHero from "../components/vacancies/VacanciesIntroHero";
import VacanciesSearchPanel, { VacancySearchDraft } from "../components/vacancies/VacanciesSearchPanel";
import VacanciesToolbar from "../components/vacancies/VacanciesToolbar";
import FeaturedVacancyCard from "../components/vacancies/FeaturedVacancyCard";
import VacancyCard from "../components/vacancies/VacancyCard";
import VacanciesEmptyState from "../components/vacancies/VacanciesEmptyState";
import { PAGE_SIZE_OPTIONS } from "../components/vacancies/vacanciesConstants";
import { useLikedVacancies } from "../hooks/useLikedVacancies";

function splitCsv(s: string | null): string[] {
  if (!s) return [];
  return s.split(",").map(x => x.trim()).filter(Boolean);
}

export type VacanciesUrlState = {
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
  skills: string;
  english_level: string;
  education_level: string;
  published_within: string;
  page: number;
  pageSize: number;
};

function parseSearchParams(searchParams: URLSearchParams): VacanciesUrlState {
  let query = searchParams.get("query") ?? "";
  if (!query) {
    const title = searchParams.get("title") ?? "";
    const keywords = searchParams.get("keywords") ?? "";
    query = [title, keywords].filter(Boolean).join(" ").trim();
  }
  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10) || 1);
  const pageSizeRaw = Number(searchParams.get("page_size"));
  const pageSize = PAGE_SIZE_OPTIONS.includes(pageSizeRaw) ? pageSizeRaw : 12;
  return {
    query,
    profession_area: splitCsv(searchParams.get("profession_area")),
    specialization: searchParams.get("specialization") ?? "",
    city: searchParams.get("city") ?? searchParams.get("location") ?? "",
    country: searchParams.get("country") ?? "",
    work_format: splitCsv(searchParams.get("work_format")),
    employment_type: splitCsv(searchParams.get("employment_type")),
    schedule_type: splitCsv(searchParams.get("schedule_type")),
    experience_level: searchParams.get("experience_level") ?? "",
    salary_from: searchParams.get("salary_from") ?? "",
    salary_currency: searchParams.get("salary_currency") ?? "",
    has_salary: searchParams.get("has_salary") === "true",
    skills: searchParams.get("skills") ?? "",
    english_level: searchParams.get("english_level") ?? "",
    education_level: searchParams.get("education_level") ?? "",
    published_within: searchParams.get("published_within") ?? "",
    page,
    pageSize,
  };
}

function parsedToDraft(p: VacanciesUrlState): VacancySearchDraft {
  return {
    query: p.query,
    profession_area: [...p.profession_area],
    specialization: p.specialization,
    city: p.city,
    country: p.country,
    work_format: [...p.work_format],
    employment_type: [...p.employment_type],
    schedule_type: [...p.schedule_type],
    experience_level: p.experience_level,
    salary_from: p.salary_from,
    salary_currency: p.salary_currency,
    has_salary: p.has_salary,
    skills: p.skills,
    english_level: p.english_level,
    education_level: p.education_level,
    published_within: p.published_within,
    pageSize: p.pageSize,
  };
}

function buildSearchParams(parsed: VacanciesUrlState): URLSearchParams {
  const p = new URLSearchParams();
  if (parsed.query) p.set("query", parsed.query);
  if (parsed.profession_area.length) p.set("profession_area", parsed.profession_area.join(","));
  if (parsed.specialization) p.set("specialization", parsed.specialization);
  if (parsed.city) p.set("city", parsed.city);
  if (parsed.country) p.set("country", parsed.country);
  if (parsed.work_format.length) p.set("work_format", parsed.work_format.join(","));
  if (parsed.employment_type.length) p.set("employment_type", parsed.employment_type.join(","));
  if (parsed.schedule_type.length) p.set("schedule_type", parsed.schedule_type.join(","));
  if (parsed.experience_level) p.set("experience_level", parsed.experience_level);
  if (parsed.salary_from) p.set("salary_from", parsed.salary_from);
  if (parsed.salary_currency) p.set("salary_currency", parsed.salary_currency);
  if (parsed.has_salary) p.set("has_salary", "true");
  if (parsed.skills) p.set("skills", parsed.skills);
  if (parsed.english_level) p.set("english_level", parsed.english_level);
  if (parsed.education_level) p.set("education_level", parsed.education_level);
  if (parsed.published_within) p.set("published_within", parsed.published_within);
  if (parsed.page > 1) p.set("page", String(parsed.page));
  if (parsed.pageSize !== 12) p.set("page_size", String(parsed.pageSize));
  return p;
}

function buildReturnTo(parsed: VacanciesUrlState): string {
  const s = buildSearchParams(parsed).toString();
  return s ? `?${s}` : "";
}

function draftToParsed(d: VacancySearchDraft, page: number): VacanciesUrlState {
  return {
    query: d.query.trim(),
    profession_area: d.profession_area,
    specialization: d.specialization.trim(),
    city: d.city.trim(),
    country: d.country.trim(),
    work_format: d.work_format,
    employment_type: d.employment_type,
    schedule_type: d.schedule_type,
    experience_level: d.experience_level.trim(),
    salary_from: d.salary_from.trim(),
    salary_currency: d.salary_currency.trim(),
    has_salary: d.has_salary,
    skills: d.skills.trim(),
    english_level: d.english_level.trim(),
    education_level: d.education_level.trim(),
    published_within: d.published_within.trim(),
    page,
    pageSize: d.pageSize,
  };
}

function filtersActiveParsed(p: VacanciesUrlState): boolean {
  if (p.pageSize !== 12) return true;
  return !!(
    p.profession_area.length
    || p.specialization
    || p.city
    || p.country
    || p.work_format.length
    || p.employment_type.length
    || p.schedule_type.length
    || p.experience_level
    || p.salary_from
    || p.salary_currency
    || p.has_salary
    || p.skills
    || p.english_level
    || p.education_level
    || p.published_within
  );
}

export default function VacanciesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState<VPage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [sortValue, setSortValue] = useState("relevance");
  const [showLikedOnly, setShowLikedOnly] = useState(false);
  const { likedVacancies, isLiked, toggleLike } = useLikedVacancies();

  const parsed = useMemo(() => parseSearchParams(searchParams), [searchParams.toString()]);
  const [draft, setDraft] = useState<VacancySearchDraft>(() => parsedToDraft(parsed));

  useEffect(() => {
    setDraft(parsedToDraft(parsed));
  }, [parsed]);

  const load = useCallback((p: VacanciesUrlState) => {
    setLoading(true);
    setError("");
    const salaryN = p.salary_from ? parseInt(p.salary_from, 10) : NaN;
    getVacancies({
      page: p.page,
      page_size: p.pageSize,
      query: p.query || undefined,
      profession_area: p.profession_area.length ? p.profession_area : undefined,
      specialization: p.specialization || undefined,
      city: p.city || undefined,
      country: p.country || undefined,
      work_format: p.work_format.length ? p.work_format : undefined,
      employment_type: p.employment_type.length ? p.employment_type : undefined,
      schedule_type: p.schedule_type.length ? p.schedule_type : undefined,
      experience_level: p.experience_level || undefined,
      salary_from: Number.isFinite(salaryN) && salaryN > 0 ? salaryN : undefined,
      salary_currency: p.salary_currency || undefined,
      has_salary: p.has_salary ? true : undefined,
      skills: p.skills ? p.skills.split(",").map(s => s.trim()).filter(Boolean) : undefined,
      english_level: p.english_level || undefined,
      education_level: p.education_level || undefined,
      published_within: p.published_within || undefined,
    })
      .then(d => setData(d))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const depKey = useMemo(() => buildSearchParams(parsed).toString(), [parsed]);

  useEffect(() => {
    if (!showLikedOnly) load(parsed);
  }, [showLikedOnly, load, depKey]);

  function applyMainSearch(e: React.FormEvent) {
    e.preventDefault();
    const next = draftToParsed(draft, 1);
    setSearchParams(buildSearchParams(next));
  }

  function applyFilters() {
    const next = draftToParsed(draft, 1);
    setSearchParams(buildSearchParams(next));
    setFiltersOpen(false);
  }

  function handleQuickFilter(value: string) {
    const next = { ...parsed, query: value, page: 1 };
    setSearchParams(buildSearchParams(next));
  }

  function handleResetFilters() {
    setSearchParams("");
  }

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;
  const page = parsed.page;
  const filtersActive = filtersActiveParsed(parsed);

  const featuredVacancy = data && data.items.length > 0 ? data.items[0] : null;
  const restVacancies = data && data.items.length > 1 ? data.items.slice(1) : [];

  function getCardVariant(index: number): "standard" | "tinted" | "accent-border" {
    if ((index + 1) % 5 === 0) return "accent-border";
    if ((index + 1) % 3 === 0) return "tinted";
    return "standard";
  }

  return (
    <div className="vacancies-page" style={{ background: "#F5F7FD", minHeight: "100%", paddingBottom: 40 }}>
      <VacanciesIntroHero totalCount={data?.total ?? null} />

      <VacanciesSearchPanel
        draft={draft}
        setDraft={setDraft}
        onSearch={applyMainSearch}
        filtersOpen={filtersOpen}
        setFiltersOpen={setFiltersOpen}
        filtersActive={filtersActive}
        onApplyFilters={applyFilters}
      />

      <div style={{ marginTop: 16, marginBottom: 8 }}>
        <button
          type="button"
          onClick={() => setShowLikedOnly(prev => !prev)}
          style={{
            padding: "10px 18px",
            background: showLikedOnly ? "#EEF2FF" : "#FFFFFF",
            border: `1px solid ${showLikedOnly ? "#C7D2FE" : "#E6EAF2"}`,
            color: showLikedOnly ? "#4338CA" : "#64748B",
            borderRadius: 999,
            fontSize: 14,
            fontWeight: 600,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <svg width={18} height={18} viewBox="0 0 24 24" fill={showLikedOnly ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" aria-hidden>
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
          Понравившиеся вакансии
          {likedVacancies.length > 0 && (
            <span style={{ background: showLikedOnly ? "#C7D2FE" : "#E6EAF2", color: showLikedOnly ? "#4338CA" : "#64748B", borderRadius: 999, padding: "2px 8px", fontSize: 12, fontWeight: 700 }}>
              {likedVacancies.length}
            </span>
          )}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}
      {!showLikedOnly && loading && <Spinner />}

      {showLikedOnly && (
        <>
          <div style={{ marginTop: 22 }} />
          <VacanciesToolbar
            total={likedVacancies.length}
            quickFilterValue={parsed.query}
            onQuickFilter={handleQuickFilter}
            sortValue={sortValue}
            onSortChange={setSortValue}
          />
          {likedVacancies.length === 0 ? (
            <VacanciesEmptyState
              onResetFilters={() => setShowLikedOnly(false)}
              onShowAll={() => setShowLikedOnly(false)}
            />
          ) : (
            <>
              {likedVacancies[0] && (
                <div style={{ marginBottom: 24 }}>
                  <FeaturedVacancyCard
                    vacancy={likedVacancies[0]}
                    returnTo={buildReturnTo(parsed)}
                    isLiked={true}
                    onToggleLike={toggleLike}
                  />
                </div>
              )}
              <div className="vacancies-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
                {likedVacancies.slice(1).map((v, i) => (
                  <VacancyCard
                    key={v.id}
                    vacancy={v}
                    returnTo={buildReturnTo(parsed)}
                    variant={getCardVariant(i)}
                    isLiked={true}
                    onToggleLike={toggleLike}
                  />
                ))}
              </div>
            </>
          )}
        </>
      )}

      {!showLikedOnly && !loading && data && (
        <>
          <div style={{ marginTop: 22 }} />
          <VacanciesToolbar
            total={data.total}
            quickFilterValue={parsed.query}
            onQuickFilter={handleQuickFilter}
            sortValue={sortValue}
            onSortChange={setSortValue}
          />

          {data.items.length === 0 && (
            <VacanciesEmptyState onResetFilters={handleResetFilters} onShowAll={handleResetFilters} />
          )}

          {data.items.length > 0 && (
            <>
              {featuredVacancy && (
                <div style={{ marginBottom: 24 }}>
                  <FeaturedVacancyCard
                    vacancy={featuredVacancy}
                    returnTo={buildReturnTo(parsed)}
                    isLiked={isLiked(featuredVacancy.id)}
                    onToggleLike={toggleLike}
                  />
                </div>
              )}
              <div
                className="vacancies-grid"
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: 20,
                }}
              >
                {restVacancies.map((v, i) => (
                  <VacancyCard
                    key={v.id}
                    vacancy={v}
                    returnTo={buildReturnTo(parsed)}
                    variant={getCardVariant(i)}
                    isLiked={isLiked(v.id)}
                    onToggleLike={toggleLike}
                  />
                ))}
              </div>

              {totalPages > 1 && (
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    justifyContent: "center",
                    marginTop: 36,
                    flexWrap: "wrap",
                  }}
                >
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setSearchParams(buildSearchParams({ ...parsed, page: page - 1 }))}
                    style={{
                      padding: "12px 20px",
                      border: "1px solid #E6EAF2",
                      borderRadius: 16,
                      background: "#FFFFFF",
                      cursor: page <= 1 ? "not-allowed" : "pointer",
                      fontWeight: 600,
                      fontSize: 14,
                      color: page <= 1 ? "#94A3B8" : "#0F172A",
                    }}
                  >
                    ← Назад
                  </button>
                  <div style={{ display: "flex", gap: 6 }}>
                    {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                      const pnum = i + 1;
                      const isActive = pnum === page;
                      return (
                        <button
                          key={pnum}
                          type="button"
                          onClick={() => setSearchParams(buildSearchParams({ ...parsed, page: pnum }))}
                          style={{
                            width: 40,
                            height: 40,
                            border: "1px solid",
                            borderRadius: 14,
                            cursor: "pointer",
                            fontSize: 14,
                            fontWeight: 600,
                            borderColor: isActive ? "#5B5CEB" : "#E6EAF2",
                            background: isActive ? "#EEF2FF" : "#FFFFFF",
                            color: isActive ? "#5B5CEB" : "#0F172A",
                          }}
                        >
                          {pnum}
                        </button>
                      );
                    })}
                  </div>
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setSearchParams(buildSearchParams({ ...parsed, page: page + 1 }))}
                    style={{
                      padding: "12px 20px",
                      border: "1px solid #E6EAF2",
                      borderRadius: 16,
                      background: "#FFFFFF",
                      cursor: page >= totalPages ? "not-allowed" : "pointer",
                      fontWeight: 600,
                      fontSize: 14,
                      color: page >= totalPages ? "#94A3B8" : "#0F172A",
                    }}
                  >
                    Вперёд →
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

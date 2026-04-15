import React, { useEffect, useMemo, useState } from "react";
import {
  getRecommendations,
  refreshRecommendations,
  getSkillGap,
  Recommendation,
  SkillGap,
} from "../api/recommendations";
import { getVacancy, Vacancy } from "../api/vacancies";
import { useLikedVacancies } from "../hooks/useLikedVacancies";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";
import RecommendationsIntroHero from "../components/recommendations/RecommendationsIntroHero";
import RecommendationsToolbar, { RecSortMode } from "../components/recommendations/RecommendationsToolbar";
import TopMatchesStrip from "../components/recommendations/TopMatchesStrip";
import RecommendationCard from "../components/recommendations/RecommendationCard";
import SkillsGapSection from "../components/recommendations/SkillsGapSection";
import RecommendationsEmptyState from "../components/recommendations/RecommendationsEmptyState";
import {
  filterRecommendations,
  sortByMatchDesc,
  orderAsInFeed,
  matchPercent,
  QuickRecFilter,
} from "../components/recommendations/recommendationUtils";

const RETURN_TO = "/recommendations";

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [vacancyMap, setVacancyMap] = useState<Map<string, Vacancy>>(new Map());
  const [skillGap, setSkillGap] = useState<SkillGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [quickFilter, setQuickFilter] = useState<QuickRecFilter>("all");
  const [sortMode, setSortMode] = useState<RecSortMode>("match");
  const { isLiked, toggleLike } = useLikedVacancies();

  async function loadVacancyDetails(recList: Recommendation[]) {
    const vacancyIds = recList.map(r => String(r.vacancy_id));
    const details = await Promise.all(vacancyIds.map(id => getVacancy(id).catch(() => null)));
    const map = new Map<string, Vacancy>();
    details.forEach((v, i) => {
      if (v) map.set(vacancyIds[i], v);
    });
    setVacancyMap(map);
  }

  async function fetchRecommendationsData(alreadyTriedRefresh = false): Promise<void> {
    let recList: Recommendation[];
    try {
      recList = await getRecommendations();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      const needsRefresh =
        /no recommendations yet|call post.*refresh|refresh first/i.test(msg);
      if (needsRefresh && !alreadyTriedRefresh) {
        await refreshRecommendations();
        return fetchRecommendationsData(true);
      }
      throw e;
    }
    let sg: SkillGap[] = [];
    try {
      sg = (await getSkillGap()).gaps;
    } catch {
      sg = [];
    }
    setRecs(recList);
    setSkillGap(sg);
    await loadVacancyDetails(recList);
  }

  function load() {
    setLoading(true);
    setError("");
    fetchRecommendationsData()
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleRefresh() {
    setRefreshing(true);
    setError("");
    try {
      await refreshRecommendations();
      setLoading(true);
      await fetchRecommendationsData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ошибка обновления");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  const filtered = useMemo(
    () => filterRecommendations(recs, vacancyMap, quickFilter),
    [recs, vacancyMap, quickFilter],
  );

  const ordered = useMemo(() => {
    if (sortMode === "match") return sortByMatchDesc(filtered);
    return orderAsInFeed(recs, filtered);
  }, [recs, filtered, sortMode]);

  const sortedByScore = useMemo(() => sortByMatchDesc(filtered), [filtered]);

  const showFeaturedStrip = sortedByScore.length > 3;
  const topFeatured = showFeaturedStrip ? sortedByScore.slice(0, 3) : [];
  const topIds = useMemo(() => new Set(topFeatured.map(r => r.id)), [topFeatured]);

  const featuredItems = useMemo(() => {
    return topFeatured
      .map(rec => {
        const v = vacancyMap.get(String(rec.vacancy_id));
        if (!v) return null;
        return { rec, vacancy: v };
      })
      .filter(Boolean) as { rec: Recommendation; vacancy: Vacancy }[];
  }, [topFeatured, vacancyMap]);

  const stripRendered = showFeaturedStrip && featuredItems.length > 0;

  const gridRecs = useMemo(() => {
    if (!stripRendered) return ordered;
    return ordered.filter(r => !topIds.has(r.id));
  }, [ordered, stripRendered, topIds]);

  const bestMatchPercent = useMemo(() => {
    if (filtered.length === 0) return null;
    return Math.max(...filtered.map(r => matchPercent(r.score)));
  }, [filtered]);

  function vacancyForRec(rec: Recommendation): Vacancy {
    const id = String(rec.vacancy_id);
    return (
      vacancyMap.get(id) ?? {
        id,
        title: "Вакансия",
        company: "Загрузка…",
        status: "active",
      }
    );
  }

  return (
    <div className="recommendations-page" style={{ background: "#F5F7FD", minHeight: "100%", paddingBottom: 48 }}>
      <div style={{ marginBottom: 28 }}>
        <RecommendationsIntroHero
          recommendationCount={filtered.length}
          bestMatchPercent={bestMatchPercent}
          loading={loading}
        />
      </div>

      {error && <ErrorBanner message={error} />}
      {loading && <Spinner />}

      {!loading && recs.length === 0 && (
        <div style={{ marginTop: 24 }}>
          <RecommendationsEmptyState />
        </div>
      )}

      {!loading && recs.length > 0 && (
        <>
          <RecommendationsToolbar
            activeFilter={quickFilter}
            onFilterChange={setQuickFilter}
            sortMode={sortMode}
            onSortModeChange={setSortMode}
            onRefresh={handleRefresh}
            refreshing={refreshing}
            loading={loading}
          />

          {filtered.length === 0 && (
            <div
              style={{
                marginTop: 32,
                textAlign: "center",
                padding: "32px 24px",
                background: "#FFFFFF",
                border: "1px solid #E6EAF2",
                borderRadius: 24,
                boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05)",
              }}
            >
              <p style={{ fontSize: 16, color: "#64748B", margin: "0 0 16px" }}>
                Нет вакансий по выбранному фильтру. Попробуйте другой тег или сбросьте фильтр.
              </p>
              <button
                type="button"
                onClick={() => setQuickFilter("all")}
                style={{
                  padding: "10px 20px",
                  background: "#EEF2FF",
                  border: "1px solid #C7D2FE",
                  borderRadius: 16,
                  color: "#4338CA",
                  fontWeight: 600,
                  fontSize: 14,
                  cursor: "pointer",
                }}
              >
                Показать все
              </button>
            </div>
          )}

          {filtered.length > 0 && (
            <>
              {showFeaturedStrip && featuredItems.length > 0 && (
                <TopMatchesStrip
                  items={featuredItems}
                  returnTo={RETURN_TO}
                  isLiked={isLiked}
                  onToggleLike={toggleLike}
                />
              )}

              <section style={{ marginTop: showFeaturedStrip && featuredItems.length > 0 ? 24 : 32 }}>
                {showFeaturedStrip && featuredItems.length > 0 && (
                  <div style={{ marginBottom: 18 }}>
                    <h2
                      style={{
                        fontSize: 30,
                        fontWeight: 700,
                        lineHeight: "36px",
                        color: "#0F172A",
                        margin: 0,
                        letterSpacing: "-0.3px",
                      }}
                    >
                      Все рекомендации
                    </h2>
                  </div>
                )}
                <div className="recommendations-grid">
                  {gridRecs.map((rec, index) => (
                    <RecommendationCard
                      key={rec.id}
                      rec={rec}
                      vacancy={vacancyForRec(rec)}
                      returnTo={RETURN_TO}
                      gridIndex={index}
                      isLiked={isLiked(String(rec.vacancy_id))}
                      onToggleLike={toggleLike}
                    />
                  ))}
                </div>
              </section>
            </>
          )}
        </>
      )}

      <SkillsGapSection gaps={skillGap.slice(0, 10)} />
    </div>
  );
}

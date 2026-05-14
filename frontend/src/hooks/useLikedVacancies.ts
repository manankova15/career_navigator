import { useState, useCallback, useEffect } from "react";
import { Vacancy, getVacancy } from "../api/vacancies";
import { getToken } from "../api/client";
import { likeVacancyOnServer, listMyLikes, unlikeVacancyOnServer } from "../api/recommendations";
import {
  getLikedVacancies,
  setLikedVacancies,
  toggleLike as toggleLikeStorage,
} from "../utils/likedVacancies";

function likedDtoToVacancy(row: { vacancy_id: string; vacancy_title: string | null; vacancy_skills: string[] }): Vacancy {
  return {
    id: row.vacancy_id,
    title: row.vacancy_title?.trim() || "Вакансия",
    company: "—",
    status: "active",
    skills: row.vacancy_skills ?? [],
  };
}

export function useLikedVacancies() {
  const [likedVacancies, setLikedVacanciesState] = useState<Vacancy[]>(() => getLikedVacancies());

  const syncFromStorage = useCallback(() => {
    setLikedVacanciesState(getLikedVacancies());
  }, []);

  useEffect(() => {
    const onStorage = () => syncFromStorage();
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [syncFromStorage]);

  useEffect(() => {
    if (!getToken()) return;
    listMyLikes()
      .then(async rows => {
        // Build base list from DTO, then enrich with full vacancy data (company, salary, etc.)
        const localCache = getLikedVacancies();
        const cacheById = new Map(localCache.map(v => [v.id, v]));

        const enriched = await Promise.all(
          rows.map(async row => {
            const fallback = likedDtoToVacancy(row);
            const cached = cacheById.get(row.vacancy_id);
            if (cached && cached.company && cached.company !== "—") {
              return { ...fallback, ...cached };
            }
            try {
              const full = await getVacancy(row.vacancy_id);
              return full;
            } catch {
              return cached ?? fallback;
            }
          }),
        );

        setLikedVacancies(enriched);
        setLikedVacanciesState(enriched);
      })
      .catch(() => {
        /* offline or no likes table yet — keep localStorage */
      });
  }, []);

  const isLiked = useCallback((id: string) => likedVacancies.some(v => v.id === id), [likedVacancies]);

  const toggleLike = useCallback(async (vacancy: Vacancy) => {
    const wasLiked = likedVacancies.some(v => v.id === vacancy.id);
    toggleLikeStorage(vacancy);
    setLikedVacanciesState(getLikedVacancies());

    if (!getToken()) {
      return;
    }

    try {
      if (wasLiked) {
        await unlikeVacancyOnServer(vacancy.id);
      } else {
        await likeVacancyOnServer(vacancy.id, {
          vacancy_title: vacancy.title,
          vacancy_skills: vacancy.skills ?? [],
          vacancy_category: vacancy.profession_area ?? null,
          vacancy_specialization: vacancy.specialization ?? null,
        });
      }
    } catch {
      toggleLikeStorage(vacancy);
      setLikedVacanciesState(getLikedVacancies());
    }
  }, [likedVacancies]);

  return { likedVacancies, isLiked, toggleLike };
}

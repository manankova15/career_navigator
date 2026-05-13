import { api } from "./client";

export interface Recommendation {
  id: string;
  vacancy_id: string;
  score: number;
  ml_score?: number | null;
  reason: string;
  vacancy?: { title: string; company: string; location: string };
}

export interface RecommendFeedPage {
  items: Recommendation[];
  total: number;
}

// До 100 записей за запрос; пагинация и сетка на клиенте
export async function getRecommendations(): Promise<Recommendation[]> {
  const data = await api.get<RecommendFeedPage>("/recommendations/me?page_size=100");
  return data.items ?? [];
}

export async function refreshRecommendations(): Promise<void> {
  await api.post("/recommendations/refresh", {});
}

// SkillGapOut (recommendation-service)
export interface SkillGap {
  skill_name: string;
  importance_score: number;
  frequency: number;
  rank: number;
  recommended_resources: string[];
}

export interface SkillGapReport {
  gaps: SkillGap[];
  total_target_vacancies: number;
}

export async function getSkillGap(): Promise<SkillGapReport> {
  return api.get<SkillGapReport>("/recommendations/skill-gap");
}

export interface LikedVacancyDto {
  id: string;
  vacancy_id: string;
  vacancy_title: string | null;
  vacancy_skills: string[];
  liked_at: string;
}

export async function listMyLikes(): Promise<LikedVacancyDto[]> {
  return api.get<LikedVacancyDto[]>("/recommendations/likes");
}

export async function likeVacancyOnServer(
  vacancyId: string,
  body: {
    vacancy_title?: string | null;
    vacancy_skills?: string[];
    vacancy_category?: string | null;
    vacancy_specialization?: string | null;
  } = {},
): Promise<LikedVacancyDto> {
  return api.post<LikedVacancyDto>(`/recommendations/likes/${vacancyId}`, body);
}

export async function unlikeVacancyOnServer(vacancyId: string): Promise<void> {
  await api.del<void>(`/recommendations/likes/${vacancyId}`);
}

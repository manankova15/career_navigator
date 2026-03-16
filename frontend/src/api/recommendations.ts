import { api } from "./client";

export interface Recommendation {
  id: string;
  vacancy_id: string;
  score: number;
  reason: string;
  vacancy?: { title: string; company: string; location: string };
}

export interface RecommendFeedPage {
  items: Recommendation[];
  total: number;
}

export async function getRecommendations(): Promise<Recommendation[]> {
  const data = await api.get<RecommendFeedPage>("/recommendations/me?page_size=20");
  return data.items ?? [];
}

export async function refreshRecommendations(): Promise<void> {
  await api.post("/recommendations/refresh", {});
}

// Matches SkillGapOut from recommendation-service
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

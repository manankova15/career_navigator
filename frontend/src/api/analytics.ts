import { api } from "./client";

export interface UserProgress {
  user_id: string; total_attempts: number; avg_score: number;
  best_score: number; assessments_taken: number;
  vacancy_views: number; recommendation_clicks: number;
  recent_stats: { assessment_id: string; topic?: string; attempts_count: number; best_percentage: number; avg_percentage: number }[];
}

export async function getMyProgress(): Promise<UserProgress> {
  return api.get<UserProgress>("/analytics/me/progress");
}

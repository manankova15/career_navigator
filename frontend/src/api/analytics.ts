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

/** Отправить событие от текущего пользователя (просмотр вакансии, клик по рекомендации и т.д.). */
export function recordEvent(
  eventType: string,
  resourceType?: string | null,
  resourceId?: string | null,
  properties?: Record<string, unknown>,
): Promise<void> {
  return api
    .post("/analytics/events/me", {
      event_type: eventType,
      resource_type: resourceType ?? null,
      resource_id: resourceId ?? null,
      properties: properties ?? {},
    })
    .then(() => {})
    .catch(() => {}); // не блокируем UI при ошибке аналитики
}

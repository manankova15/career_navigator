import { api } from "./client";

export type IngestionRun = {
  id: string;
  source_id: string | null;
  source_name: string | null;
  source_type: string | null;
  task_id: string | null;
  status: string;
  new_vacancies: number;
  max_vacancies: number | null;
  reason: string | null;
  error: string | null;
  started_at: string;
  finished_at: string | null;
};

export type IngestionRunsPage = {
  items: IngestionRun[];
  total: number;
  page: number;
  page_size: number;
};

export type IngestionSchedule = {
  fetch_interval_hours: number;
  normalize_interval_minutes: number;
};

export function listIngestionRuns(
  page = 1,
  pageSize = 30,
  filters: { source_id?: string; status?: string } = {},
) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (filters.source_id) params.set("source_id", filters.source_id);
  if (filters.status) params.set("status", filters.status);
  return api.get<IngestionRunsPage>(`/admin/ingestion/runs?${params.toString()}`);
}

export function deleteIngestionRun(id: string) {
  return api.delete<void>(`/admin/ingestion/runs/${id}`);
}

export function getIngestionSchedule() {
  return api.get<IngestionSchedule>(`/admin/ingestion/schedule`);
}

export function updateIngestionSchedule(payload: Partial<IngestionSchedule>) {
  return api.patch<IngestionSchedule>(`/admin/ingestion/schedule`, payload);
}

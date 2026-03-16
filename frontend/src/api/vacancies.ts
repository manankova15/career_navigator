import { api, getToken } from "./client";

export interface Vacancy {
  id: string;
  title: string;
  company: string;
  location?: string | null;
  salary_from?: number | null;
  salary_to?: number | null;
  currency?: string | null;
  seniority?: string | null;
  employment_type?: string | null;
  skills?: string[];
  description?: string | null;
  canonical_url?: string | null;
  status: string;
  published_at?: string | null;
}

export interface VacanciesPage {
  items: Vacancy[];
  total: number;
  page: number;
  page_size: number;
  pages?: number;
}

export async function getVacancies(
  page = 1,
  q = "",
  location = "",
  seniority = "",
): Promise<VacanciesPage> {
  const params = new URLSearchParams({ page: String(page), page_size: "12" });
  if (q) params.set("q", q);
  if (location) params.set("location", location);
  if (seniority) params.set("seniority", seniority);
  return api.get<VacanciesPage>(`/vacancies?${params.toString()}`);
}

export async function getVacancy(id: string): Promise<Vacancy> {
  return api.get<Vacancy>(`/vacancies/${id}`);
}

function getUserIdFromToken(): string | null {
  const token = getToken();
  if (!token) return null;
  try {
    return JSON.parse(atob(token.split(".")[1])).sub ?? null;
  } catch {
    return null;
  }
}

export async function recordVacancyInterest(
  vacancyId: string,
  interested: boolean,
): Promise<void> {
  const userId = getUserIdFromToken();
  if (!userId) return;
  await api
    .post("/analytics/events", {
      user_id: userId,
      event_type: "vacancy_interest",
      resource_type: "vacancy",
      resource_id: vacancyId,
      properties: { interested },
    })
    .catch(() => {}); // non-critical, swallow errors
}

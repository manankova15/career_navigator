import { api, getToken } from "./client";

export interface Vacancy {
  id: string;
  title: string;
  company: string;
  location?: string | null;
  salary_from?: number | null;
  salary_to?: number | null;
  /** Валюта зарплаты (ТЗ); для старых данных допускается `currency` */
  salary_currency?: string | null;
  currency?: string | null;
  seniority?: string | null;
  experience_level?: string | null;
  employment_type?: string[] | null;
  work_format?: string[];
  schedule_type?: string | null;
  salary_gross_type?: string | null;
  salary_period?: string | null;
  profession_area?: string | null;
  specialization?: string | null;
  location_country?: string | null;
  location_city?: string | null;
  education_level?: string | null;
  english_level?: string | null;
  company_industry?: string | null;
  source_name?: string | null;
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

export interface VacancySearchParams {
  page?: number;
  page_size?: number;
  query?: string;
  profession_area?: string[];
  specialization?: string;
  city?: string;
  country?: string;
  work_format?: string[];
  employment_type?: string[];
  schedule_type?: string[];
  experience_level?: string;
  salary_from?: number;
  salary_currency?: string;
  has_salary?: boolean;
  skills?: string[];
  english_level?: string;
  education_level?: string;
  published_within?: string;
  seniority?: string;
}

function appendCsv(search: URLSearchParams, key: string, values: string[] | undefined) {
  if (!values?.length) return;
  search.set(key, values.join(","));
}

export async function getVacancies(params: VacancySearchParams = {}): Promise<VacanciesPage> {
  const {
    page = 1,
    page_size = 12,
    query = "",
    profession_area = [],
    specialization = "",
    city = "",
    country = "",
    work_format = [],
    employment_type = [],
    schedule_type = [],
    experience_level = "",
    salary_from,
    salary_currency = "",
    has_salary,
    skills = [],
    english_level = "",
    education_level = "",
    published_within = "",
    seniority = "",
  } = params;
  const search = new URLSearchParams({ page: String(page), page_size: String(page_size) });
  if (query.trim()) search.set("query", query.trim());
  appendCsv(search, "profession_area", profession_area);
  if (specialization.trim()) search.set("specialization", specialization.trim());
  if (city.trim()) search.set("city", city.trim());
  if (country.trim()) search.set("country", country.trim());
  appendCsv(search, "work_format", work_format);
  appendCsv(search, "employment_type", employment_type);
  appendCsv(search, "schedule_type", schedule_type);
  if (experience_level) search.set("experience_level", experience_level);
  if (salary_from != null && salary_from > 0) search.set("salary_from", String(salary_from));
  if (salary_currency) search.set("salary_currency", salary_currency);
  if (has_salary === true) search.set("has_salary", "true");
  appendCsv(search, "skills", skills);
  if (english_level) search.set("english_level", english_level);
  if (education_level) search.set("education_level", education_level);
  if (published_within) search.set("published_within", published_within);
  if (seniority) search.set("seniority", seniority);
  return api.get<VacanciesPage>(`/vacancies?${search.toString()}`);
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

export function vacancySalaryCurrency(v: Vacancy): string {
  return v.salary_currency || v.currency || "RUB";
}

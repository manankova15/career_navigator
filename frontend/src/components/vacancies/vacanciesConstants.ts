/** Значения API и подписи UI по ТЗ (поиск вакансий). */

export const PROFESSION_AREAS: { value: string; label: string }[] = [
  { value: "it", label: "IT" },
  { value: "analytics", label: "Аналитика" },
  { value: "finance", label: "Финансы" },
  { value: "accounting", label: "Бухгалтерия" },
  { value: "marketing", label: "Маркетинг" },
  { value: "sales", label: "Продажи" },
  { value: "product", label: "Продукт" },
  { value: "project_management", label: "Проектный менеджмент" },
  { value: "design", label: "Дизайн" },
  { value: "hr", label: "HR" },
  { value: "legal", label: "Юриспруденция" },
  { value: "customer_support", label: "Поддержка клиентов" },
  { value: "operations", label: "Операции" },
  { value: "logistics", label: "Логистика" },
  { value: "administration", label: "Администрирование" },
  { value: "education", label: "Образование" },
  { value: "engineering", label: "Инженерия" },
  { value: "medicine", label: "Медицина" },
  { value: "other", label: "Другое" },
];

export const SPECIALIZATION_OPTIONS: { value: string; label: string }[] = [
  { value: "backend_developer", label: "Backend" },
  { value: "frontend_developer", label: "Frontend" },
  { value: "fullstack_developer", label: "Fullstack" },
  { value: "qa_engineer", label: "QA" },
  { value: "devops_engineer", label: "DevOps / SRE" },
  { value: "data_analyst", label: "Data analyst" },
  { value: "business_analyst", label: "Business analyst" },
  { value: "system_analyst", label: "System analyst" },
  { value: "financial_analyst", label: "Financial analyst" },
  { value: "accountant", label: "Бухгалтер" },
  { value: "internet_marketer", label: "Internet marketing" },
  { value: "performance_marketer", label: "Performance" },
  { value: "sales_manager", label: "Sales manager" },
  { value: "account_manager", label: "Account manager" },
  { value: "product_manager", label: "Product manager" },
  { value: "project_manager", label: "Project manager" },
  { value: "ui_ux_designer", label: "UI/UX" },
  { value: "graphic_designer", label: "Graphic design" },
  { value: "recruiter", label: "Рекрутинг" },
  { value: "lawyer", label: "Юрист" },
  { value: "support_specialist", label: "Поддержка" },
];

export const WORK_FORMATS: { value: string; label: string }[] = [
  { value: "office", label: "В офисе" },
  { value: "remote", label: "Удалённо" },
  { value: "hybrid", label: "Гибрид" },
  { value: "field", label: "Разъездная" },
];

export const EMPLOYMENT_TYPES: { value: string; label: string }[] = [
  { value: "full_time", label: "Полная занятость" },
  { value: "part_time", label: "Частичная занятость" },
  { value: "contract", label: "Контракт" },
  { value: "project", label: "Проектная работа" },
  { value: "internship", label: "Стажировка" },
  { value: "temporary", label: "Временная работа" },
  { value: "volunteering", label: "Волонтёрство" },
];

export const SCHEDULE_TYPES: { value: string; label: string }[] = [
  { value: "full_day", label: "Полный день" },
  { value: "flexible", label: "Гибкий график" },
  { value: "shift", label: "Сменный" },
  { value: "weekend", label: "По выходным" },
  { value: "watch", label: "Вахта" },
  { value: "custom", label: "Другое" },
];

export const EXPERIENCE_LEVELS: { value: string; label: string }[] = [
  { value: "", label: "Любой опыт" },
  { value: "no_experience", label: "Без опыта" },
  { value: "1_3_years", label: "От 1 до 3 лет" },
  { value: "3_6_years", label: "От 3 до 6 лет" },
  { value: "6_plus_years", label: "Более 6 лет" },
];

export const SALARY_CURRENCIES: { value: string; label: string }[] = [
  { value: "", label: "Любая" },
  { value: "RUB", label: "RUB" },
  { value: "USD", label: "USD" },
  { value: "EUR", label: "EUR" },
  { value: "KZT", label: "KZT" },
  { value: "OTHER", label: "Другая" },
];

export const ENGLISH_LEVELS: { value: string; label: string }[] = [
  { value: "", label: "Любой" },
  { value: "not_required", label: "Не требуется" },
  { value: "a1", label: "A1" },
  { value: "a2", label: "A2" },
  { value: "b1", label: "B1" },
  { value: "b2", label: "B2" },
  { value: "c1", label: "C1" },
  { value: "c2", label: "C2" },
];

export const EDUCATION_LEVELS: { value: string; label: string }[] = [
  { value: "", label: "Любое" },
  { value: "not_required", label: "Не требуется" },
  { value: "secondary", label: "Среднее" },
  { value: "specialized_secondary", label: "Среднее специальное" },
  { value: "bachelor", label: "Бакалавр" },
  { value: "master", label: "Магистр" },
  { value: "higher", label: "Высшее" },
  { value: "unknown", label: "Не указано" },
];

export const PUBLISHED_WITHIN: { value: string; label: string }[] = [
  { value: "", label: "За всё время" },
  { value: "1d", label: "За сутки" },
  { value: "3d", label: "За 3 дня" },
  { value: "7d", label: "За неделю" },
  { value: "30d", label: "За месяц" },
];

export const PAGE_SIZE_OPTIONS = [12, 24, 48];

export const EXPERIENCE_LEVEL_LABEL: Record<string, string> = {
  no_experience: "Без опыта",
  "1_3_years": "1–3 года",
  "3_6_years": "3–6 лет",
  "6_plus_years": "6+ лет",
};

export const PROFESSION_AREA_LABEL: Record<string, string> = Object.fromEntries(
  PROFESSION_AREAS.map(({ value, label }) => [value, label]),
);

export const WORK_FORMAT_LABEL: Record<string, string> = Object.fromEntries(
  WORK_FORMATS.map(({ value, label }) => [value, label]),
);

export const EMPLOYMENT_LABEL: Record<string, string> = Object.fromEntries(
  EMPLOYMENT_TYPES.map(({ value, label }) => [value, label]),
);

export const SCHEDULE_LABEL: Record<string, string> = Object.fromEntries(
  SCHEDULE_TYPES.map(({ value, label }) => [value, label]),
);

export const SALARY_PERIOD_LABEL: Record<string, string> = {
  month: "в месяц",
  hour: "в час",
  shift: "за смену",
  project: "за проект",
  year: "в год",
  unknown: "",
};

export const SALARY_GROSS_LABEL: Record<string, string> = {
  gross: "до налогов",
  net: "на руки",
  unknown: "",
};

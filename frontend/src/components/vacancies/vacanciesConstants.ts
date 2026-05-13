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
  // IT / разработка
  { value: "backend_developer", label: "Backend разработчик" },
  { value: "frontend_developer", label: "Frontend разработчик" },
  { value: "fullstack_developer", label: "Fullstack разработчик" },
  { value: "mobile_developer", label: "Mobile разработчик" },
  { value: "ios_developer", label: "iOS разработчик" },
  { value: "android_developer", label: "Android разработчик" },
  { value: "game_developer", label: "Game разработчик" },
  { value: "embedded_developer", label: "Embedded разработчик" },
  { value: "qa_engineer", label: "QA / тестировщик" },
  { value: "qa_automation_engineer", label: "QA Automation" },
  { value: "devops_engineer", label: "DevOps / SRE" },
  { value: "system_administrator", label: "Системный администратор" },
  { value: "security_engineer", label: "Информационная безопасность" },
  { value: "database_administrator", label: "DBA / администратор БД" },
  { value: "data_engineer", label: "Data Engineer" },
  { value: "data_scientist", label: "Data Scientist" },
  { value: "ml_engineer", label: "ML / AI Engineer" },
  // Аналитика
  { value: "data_analyst", label: "Data analyst" },
  { value: "business_analyst", label: "Business analyst" },
  { value: "system_analyst", label: "System analyst" },
  { value: "product_analyst", label: "Product analyst" },
  { value: "financial_analyst", label: "Financial analyst" },
  // Финансы / бухгалтерия
  { value: "accountant", label: "Бухгалтер" },
  { value: "auditor", label: "Аудитор" },
  { value: "economist", label: "Экономист" },
  // Маркетинг / продажи
  { value: "internet_marketer", label: "Internet-маркетолог" },
  { value: "performance_marketer", label: "Performance-маркетолог" },
  { value: "content_marketer", label: "Контент-маркетолог" },
  { value: "smm_specialist", label: "SMM-специалист" },
  { value: "seo_specialist", label: "SEO-специалист" },
  { value: "brand_manager", label: "Brand manager" },
  { value: "copywriter", label: "Копирайтер" },
  { value: "sales_manager", label: "Sales manager" },
  { value: "account_manager", label: "Account manager" },
  // Продукт / проекты
  { value: "product_manager", label: "Product manager" },
  { value: "project_manager", label: "Project manager" },
  { value: "scrum_master", label: "Scrum master / Agile coach" },
  // Дизайн
  { value: "ui_ux_designer", label: "UI/UX дизайнер" },
  { value: "graphic_designer", label: "Графический дизайнер" },
  { value: "product_designer", label: "Product designer" },
  { value: "motion_designer", label: "Motion дизайнер" },
  // HR / юриспруденция / поддержка
  { value: "recruiter", label: "Рекрутёр" },
  { value: "hr_manager", label: "HR-менеджер" },
  { value: "lawyer", label: "Юрист" },
  { value: "support_specialist", label: "Специалист поддержки" },
  // Операции / логистика
  { value: "operations_manager", label: "Operations manager" },
  { value: "logistics_specialist", label: "Логист" },
  { value: "office_manager", label: "Офис-менеджер" },
  // Инженерия / образование / медицина
  { value: "engineer", label: "Инженер" },
  { value: "teacher", label: "Преподаватель" },
  { value: "doctor", label: "Врач" },
  { value: "other", label: "Другое" },
];

/**
 * Список городов / локаций для профиля пользователя (dropdown).
 * Покрывает крупнейшие города РФ и СНГ + удалённый формат.
 */
export const CITIES: { value: string; label: string }[] = [
  { value: "remote", label: "Удалённо" },
  { value: "moscow", label: "Москва" },
  { value: "spb", label: "Санкт-Петербург" },
  { value: "novosibirsk", label: "Новосибирск" },
  { value: "ekaterinburg", label: "Екатеринбург" },
  { value: "kazan", label: "Казань" },
  { value: "nizhny_novgorod", label: "Нижний Новгород" },
  { value: "chelyabinsk", label: "Челябинск" },
  { value: "samara", label: "Самара" },
  { value: "omsk", label: "Омск" },
  { value: "rostov_on_don", label: "Ростов-на-Дону" },
  { value: "ufa", label: "Уфа" },
  { value: "krasnoyarsk", label: "Красноярск" },
  { value: "voronezh", label: "Воронеж" },
  { value: "perm", label: "Пермь" },
  { value: "volgograd", label: "Волгоград" },
  { value: "krasnodar", label: "Краснодар" },
  { value: "saratov", label: "Саратов" },
  { value: "tyumen", label: "Тюмень" },
  { value: "tolyatti", label: "Тольятти" },
  { value: "izhevsk", label: "Ижевск" },
  { value: "barnaul", label: "Барнаул" },
  { value: "ulyanovsk", label: "Ульяновск" },
  { value: "irkutsk", label: "Иркутск" },
  { value: "khabarovsk", label: "Хабаровск" },
  { value: "yaroslavl", label: "Ярославль" },
  { value: "vladivostok", label: "Владивосток" },
  { value: "makhachkala", label: "Махачкала" },
  { value: "tomsk", label: "Томск" },
  { value: "orenburg", label: "Оренбург" },
  { value: "kemerovo", label: "Кемерово" },
  { value: "novokuznetsk", label: "Новокузнецк" },
  { value: "ryazan", label: "Рязань" },
  { value: "naberezhnye_chelny", label: "Набережные Челны" },
  { value: "astrakhan", label: "Астрахань" },
  { value: "penza", label: "Пенза" },
  { value: "lipetsk", label: "Липецк" },
  { value: "kirov", label: "Киров" },
  { value: "cheboksary", label: "Чебоксары" },
  { value: "kaliningrad", label: "Калининград" },
  { value: "tula", label: "Тула" },
  { value: "kursk", label: "Курск" },
  { value: "stavropol", label: "Ставрополь" },
  { value: "ulan_ude", label: "Улан-Удэ" },
  { value: "tver", label: "Тверь" },
  { value: "magnitogorsk", label: "Магнитогорск" },
  { value: "sochi", label: "Сочи" },
  { value: "ivanovo", label: "Иваново" },
  { value: "bryansk", label: "Брянск" },
  { value: "belgorod", label: "Белгород" },
  { value: "vladimir", label: "Владимир" },
  { value: "arkhangelsk", label: "Архангельск" },
  { value: "kaluga", label: "Калуга" },
  { value: "smolensk", label: "Смоленск" },
  { value: "yakutsk", label: "Якутск" },
  // СНГ
  { value: "minsk", label: "Минск" },
  { value: "almaty", label: "Алматы" },
  { value: "astana", label: "Астана" },
  { value: "tashkent", label: "Ташкент" },
  { value: "baku", label: "Баку" },
  { value: "tbilisi", label: "Тбилиси" },
  { value: "yerevan", label: "Ереван" },
  { value: "bishkek", label: "Бишкек" },
  { value: "other", label: "Другое" },
];

export const WORK_FORMATS: { value: string; label: string }[] = [
  { value: "office", label: "В офисе" },
  { value: "remote", label: "Удалённо" },
  { value: "hybrid", label: "Гибрид" },
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

/**
 * Размеры страницы подобраны под layout «1 большая карточка + grid из 3 колонок»:
 * первая карточка идёт «featured», остальные раскладываются по 3 в ряд, поэтому
 * (pageSize - 1) должно быть кратно 3, иначе в конце остаётся пустое место.
 */
export const PAGE_SIZE_OPTIONS = [13, 25, 49];
export const DEFAULT_PAGE_SIZE = 13;

export const EXPERIENCE_LEVEL_LABEL: Record<string, string> = {
  no_experience: "Без опыта",
  "1_3_years": "1–3 года",
  "3_6_years": "3–6 лет",
  "6_plus_years": "6+ лет",
};

export const PROFESSION_AREA_LABEL: Record<string, string> = Object.fromEntries(
  PROFESSION_AREAS.map(({ value, label }) => [value, label]),
);

export const SPECIALIZATION_LABEL: Record<string, string> = Object.fromEntries(
  SPECIALIZATION_OPTIONS.map(({ value, label }) => [value, label]),
);

export const CITY_LABEL: Record<string, string> = Object.fromEntries(
  CITIES.map(({ value, label }) => [value, label]),
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

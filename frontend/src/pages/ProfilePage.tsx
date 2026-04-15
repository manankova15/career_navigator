import React, { useEffect, useRef, useState } from "react";
import {
  getProfile,
  updateProfile,
  Profile,
  getProfileSkills,
  addProfileSkill,
  removeProfileSkill,
  ProfileSkill,
  getPreferences,
  updatePreferences,
  type ProfilePreferences,
} from "../api/profile";
import {
  applyResumeDraft,
  getResumeFileStatus,
  uploadResumePdf,
  type ResumeStatusBundle,
} from "../api/resume";
import { MeResponse } from "../api/auth";
import Spinner from "../components/Spinner";
import ErrorBanner from "../components/ErrorBanner";

const SUGGESTED_SKILLS = [
  "Python", "JavaScript", "TypeScript", "React", "Vue.js", "Angular",
  "Node.js", "FastAPI", "Django", "Flask", "Go", "Rust", "Java", "Kotlin",
  "C++", "C#", ".NET", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
  "Docker", "Kubernetes", "Git", "Linux", "AWS", "GCP", "Azure",
  "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "scikit-learn",
  "Data Analysis", "Pandas", "NumPy", "Spark", "Kafka",
  "REST API", "GraphQL", "gRPC", "Microservices", "CI/CD", "DevOps",
  "HTML", "CSS", "SCSS", "Figma", "UX/UI Design",
  "Agile", "Scrum", "Jira", "Product Management",
];

interface Props { user?: MeResponse | null; }

export default function ProfilePage({ user }: Props) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [form, setForm] = useState<Partial<Profile>>({});
  const [skills, setSkills] = useState<ProfileSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [skillInput, setSkillInput] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [addingSkill, setAddingSkill] = useState(false);
  const skillInputRef = useRef<HTMLInputElement>(null);

  const emptyPrefs = (): ProfilePreferences => ({
    preferred_locations: [],
    work_formats: [],
    target_roles: [],
    salary_from: null,
    salary_to: null,
    seniority: null,
  });
  const [prefs, setPrefs] = useState<ProfilePreferences>(emptyPrefs);
  const [prefsLoading, setPrefsLoading] = useState(true);

  const [resumeBusy, setResumeBusy] = useState(false);
  const [resumeErr, setResumeErr] = useState("");
  const [resumeHint, setResumeHint] = useState("");
  const [resumeFileId, setResumeFileId] = useState<string | null>(null);
  const [resumeBundle, setResumeBundle] = useState<ResumeStatusBundle | null>(null);
  const [importingDraft, setImportingDraft] = useState(false);
  const [resumeApply, setResumeApply] = useState({
    profile: true,
    prefs: true,
    skills: true,
    experience: true,
    education: true,
  });

  useEffect(() => {
    Promise.all([getProfile(), getProfileSkills()])
      .then(([p, sk]) => {
        setProfile(p);
        const initialForm: Partial<Profile> = { ...p };
        if (!initialForm.full_name && user?.full_name) {
          initialForm.full_name = user.full_name;
        }
        // back-fill first/last name from full_name if not yet stored separately
        if (!initialForm.first_name && !initialForm.last_name) {
          const source = initialForm.full_name ?? user?.full_name ?? "";
          const parts = source.trim().split(/\s+/);
          if (parts.length >= 2) {
            initialForm.first_name = parts[0];
            initialForm.last_name = parts[1];
            initialForm.patronymic = parts.slice(2).join(" ") || undefined;
          } else if (parts.length === 1 && parts[0]) {
            initialForm.first_name = parts[0];
          }
        }
        setForm(initialForm);
        setSkills(sk);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    getPreferences()
      .then(p => {
        if (p) {
          setPrefs({
            ...emptyPrefs(),
            ...p,
            preferred_locations: p.preferred_locations ?? [],
            work_formats: p.work_formats ?? [],
            target_roles: p.target_roles ?? [],
          });
        } else setPrefs(emptyPrefs());
      })
      .catch(() => setPrefs(emptyPrefs()))
      .finally(() => setPrefsLoading(false));
  }, []);

  useEffect(() => {
    if (!resumeFileId) return;
    let cancelled = false;
    let id: ReturnType<typeof setInterval> | undefined;
    const tick = () => {
      getResumeFileStatus(resumeFileId)
        .then(b => {
          if (cancelled) return;
          setResumeBundle(b);
          const st = b.parse_job?.status ?? "";
          if (["parsed", "invalid", "failed"].includes(st)) {
            if (id) clearInterval(id);
            if (st === "failed") {
              setResumeErr(b.parse_job?.error_message ?? "Не удалось распознать файл");
            } else if (st === "invalid") {
              setResumeHint(
                "Файл сохранён, но мы не уверены, что это резюме hh.ru. Заполните профиль вручную или загрузите другой PDF.",
              );
            } else {
              setResumeHint(
                b.parse_result && !b.parse_result.is_hh_resume && b.parse_result.hh_confidence_score < 0.75
                  ? "Распознавание выполнено. Проверьте данные перед применением."
                  : "Распознавание завершено. Ниже выберите блоки и нажмите «Применить к профилю».",
              );
            }
          }
        })
        .catch(() => {});
    };
    tick();
    id = setInterval(tick, 1500);
    return () => {
      cancelled = true;
      if (id) clearInterval(id);
    };
  }, [resumeFileId]);

  async function handleResumeUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setResumeErr("Нужен файл в формате PDF");
      return;
    }
    setResumeBusy(true);
    setResumeErr("");
    setResumeHint("");
    setResumeBundle(null);
    try {
      const up = await uploadResumePdf(f);
      setResumeFileId(up.resume_file.id);
      setResumeBundle({
        resume_file: up.resume_file,
        parse_job: up.parse_job,
        parse_result: null,
        draft: null,
      });
      setResumeHint("Файл загружен, идёт распознавание…");
    } catch (err: unknown) {
      setResumeErr(err instanceof Error ? err.message : "Ошибка загрузки");
    } finally {
      setResumeBusy(false);
    }
  }

  function scheduleToWorkFormats(schedules: string[]): string[] {
    const out = new Set<string>();
    const s = schedules.join(" ").toLowerCase();
    if (s.includes("удален")) out.add("remote");
    if (s.includes("офис") || s.includes("полный день")) out.add("office");
    if (s.includes("гибрид") || s.includes("гибкий")) out.add("hybrid");
    if (out.size === 0 && schedules.length) out.add("office");
    return [...out];
  }

  function skillLevelToStars(level: string | undefined): number {
    const m: Record<string, number> = { basic: 2, intermediate: 3, advanced: 4, unknown: 2 };
    return m[level ?? ""] ?? 3;
  }

  async function handleApplyResumeDraft() {
    const draft = resumeBundle?.draft;
    const parsed = draft?.draft_json?.parsed as Record<string, unknown> | undefined;
    if (!draft || !parsed) {
      setResumeErr("Нет черновика для применения (уверенность могла быть слишком низкой).");
      return;
    }
    setImportingDraft(true);
    setResumeErr("");
    try {
      const prof = (parsed.profile as Record<string, string | undefined>) || {};
      const city = prof.city || "";
      const job = (parsed.job as Record<string, unknown>) || {};
      const specs = (job.specializations as string[]) || [];
      const desired = (job.desiredPosition as string) || "";
      const salaryFrom = (job.salaryFrom as number) ?? (job.salaryAmount as number) ?? null;
      const schedules = (job.workSchedules as string[]) || [];

      const body: Record<string, unknown> = {};

      if (resumeApply.profile) {
        const metro = prof.metro || "";
        body.profile = {
          first_name: prof.firstName || null,
          last_name: prof.lastName || null,
          patronymic: prof.middleName || null,
          location: [city, metro].filter(Boolean).join(", ") || null,
          target_role: desired || null,
          headline: (job.resumeTitleRaw as string) || desired || null,
          summary: [parsed.aboutMe, parsed.additionalInfo].filter(Boolean).join("\n\n") || null,
          bio: (parsed.aboutMe as string) || null,
        };
      }

      if (resumeApply.prefs) {
        const roles = [...specs];
        if (desired && !roles.includes(desired)) roles.unshift(desired);
        body.preferences = {
          target_roles: roles,
          preferred_locations: city ? [city] : [],
          work_formats: scheduleToWorkFormats(schedules),
          salary_from: salaryFrom,
          salary_to: (job.salaryTo as number) ?? null,
          seniority: null,
        };
      }

      if (resumeApply.skills) {
        const sl = (parsed.skillLevels as { skill: string; level: string }[]) || [];
        const names = (parsed.skills as string[]) || [];
        const levelByName = Object.fromEntries(sl.map(x => [x.skill.toLowerCase(), x.level]));
        body.skills = names.map(name => ({
          skill_name: name,
          self_assessed_level: skillLevelToStars(levelByName[name.toLowerCase()]),
        }));
        body.skills_mode = "append";
      }

      if (resumeApply.experience) {
        const ex = (parsed.experience as Record<string, unknown>[]) || [];
        body.work_experience = ex.map(row => ({
          company: String(row.companyName || ""),
          title: String(row.position || ""),
          start_date: row.startDate || null,
          end_date: row.isCurrent ? null : row.endDate || null,
          is_current: !!row.isCurrent,
          description: row.description ? String(row.description) : null,
        }));
        body.work_experience_mode = "append";
      }

      if (resumeApply.education) {
        const ed = (parsed.education as Record<string, unknown>[]) || [];
        body.education = ed.map(row => ({
          institution: String(row.institution || ""),
          degree: row.level ? String(row.level) : null,
          field: row.speciality ? String(row.speciality) : null,
          start_year: null,
          end_year: row.endYear != null ? Number(row.endYear) : null,
        }));
        body.education_mode = "append";
      }

      await applyResumeDraft(draft.id, body);
      setResumeHint("Импорт применён. Обновляем данные…");
      const [p, sk, pref] = await Promise.all([getProfile(), getProfileSkills(), getPreferences()]);
      setProfile(p);
      setForm({ ...p });
      setSkills(sk);
      if (pref) {
        setPrefs({
          preferred_locations: pref.preferred_locations ?? [],
          work_formats: pref.work_formats ?? [],
          target_roles: pref.target_roles ?? [],
          salary_from: pref.salary_from ?? null,
          salary_to: pref.salary_to ?? null,
          seniority: pref.seniority ?? null,
        });
      }
      setResumeHint("Готово. При необходимости отредактируйте поля и нажмите «Сохранить профиль» внизу страницы.");
    } catch (err: unknown) {
      setResumeErr(err instanceof Error ? err.message : "Ошибка применения");
    } finally {
      setImportingDraft(false);
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess(false);
    try {
      const parts = [form.first_name, form.last_name, form.patronymic].map(s => s?.trim() ?? "").filter(Boolean);
      const payload: Partial<Profile> = {
        ...form,
        full_name: parts.length ? parts.join(" ") : form.full_name,
      };
      const updated = await updateProfile(payload);
      setProfile(updated);
      setForm(updated);
      if (!prefsLoading) {
        const prefUpdated = await updatePreferences(prefs);
        setPrefs({
          ...emptyPrefs(),
          ...prefUpdated,
          preferred_locations: prefUpdated.preferred_locations ?? [],
          work_formats: prefUpdated.work_formats ?? [],
          target_roles: prefUpdated.target_roles ?? [],
        });
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить");
    } finally {
      setSaving(false);
    }
  }

  function handleSkillInput(val: string) {
    setSkillInput(val);
    if (val.trim().length > 0) {
      const filtered = SUGGESTED_SKILLS.filter(
        s => s.toLowerCase().includes(val.toLowerCase()) &&
          !skills.some(sk => sk.skill_name.toLowerCase() === s.toLowerCase()),
      );
      setSuggestions(filtered.slice(0, 7));
    } else {
      setSuggestions([]);
    }
  }

  async function handleAddSkill(name?: string) {
    const skillName = (name ?? skillInput).trim();
    if (!skillName) return;
    if (skills.some(s => s.skill_name.toLowerCase() === skillName.toLowerCase())) {
      setSuggestions([]); setSkillInput(""); return;
    }
    setAddingSkill(true);
    try {
      const newSkill = await addProfileSkill(skillName, 1);
      setSkills(prev => [...prev, newSkill]);
      setSkillInput(""); setSuggestions([]);
    } catch (e: any) { setError(e.message); }
    finally { setAddingSkill(false); }
  }

  async function handleRemoveSkill(id: string) {
    try {
      await removeProfileSkill(id);
      setSkills(prev => prev.filter(s => s.id !== id));
    } catch (e: any) { setError(e.message); }
  }

  function parseLines(s: string): string[] {
    return s
      .split(/\r?\n/)
      .map(x => x.trim())
      .filter(Boolean);
  }

  if (loading) return <Spinner />;

  const initials = (() => {
    const fn = (form.first_name ?? "").trim();
    const ln = (form.last_name ?? "").trim();
    if (fn && ln) return (fn[0] + ln[0]).toUpperCase();
    if (fn) return fn.slice(0, 2).toUpperCase();
    const fallback = user?.full_name ?? user?.email?.split("@")[0] ?? "П";
    const parts = fallback.trim().split(/\s+/);
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : parts[0].slice(0, 2).toUpperCase();
  })();

  return (
    <div style={{ maxWidth: 720 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 32 }}>
        <div style={{ width: 64, height: 64, borderRadius: "50%", background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, fontWeight: 800, color: "#3B5BDB", border: "3px solid #C7D2FE", flexShrink: 0 }}>
          {initials}
        </div>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: "#0F172A", margin: "0 0 4px", letterSpacing: "-0.4px" }}>
            Мой профиль
          </h1>
          <p style={{ color: "#64748B", margin: 0, fontSize: 14 }}>
            {user?.email}
          </p>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <SectionCard title="Импорт резюме с hh.ru (PDF)" icon="📄">
        <p style={{ color: "#64748B", fontSize: 14, marginTop: 0, marginBottom: 12 }}>
          Загрузите PDF-версию резюме с hh.ru. Поля изменятся после нажатия «Сохранить профиль»
          (включая блок «Предпочтения по вакансиям»).
        </p>
        {resumeErr && <ErrorBanner message={resumeErr} />}
        {resumeHint && !resumeErr && (
          <div style={{ background: "#EFF6FF", color: "#1D4ED8", border: "1.5px solid #BFDBFE", borderRadius: 12, padding: "10px 14px", marginBottom: 12, fontSize: 13 }}>
            {resumeHint}
          </div>
        )}
        <label style={{ display: "inline-flex", alignItems: "center", gap: 10, cursor: resumeBusy ? "wait" : "pointer" }}>
          <span style={{ padding: "10px 18px", background: resumeBusy ? "#CBD5E1" : "#0F766E", color: "#fff", borderRadius: 12, fontWeight: 600, fontSize: 14 }}>
            {resumeBusy ? "Загрузка…" : "Выбрать PDF"}
          </span>
          <input type="file" accept="application/pdf,.pdf" style={{ display: "none" }} disabled={resumeBusy} onChange={handleResumeUpload} />
        </label>
        <span style={{ color: "#94A3B8", fontSize: 12, marginLeft: 10 }}>до 5 МБ</span>

        {resumeBundle?.parse_job && (
          <p style={{ marginTop: 14, marginBottom: 8, fontSize: 13, color: "#475569" }}>
            Статус: <strong>{resumeBundle.parse_job.status}</strong>
            {resumeBundle.parse_result != null && (
              <>
                {" "}
                · уверенность hh.ru: {(resumeBundle.parse_result.hh_confidence_score * 100).toFixed(0)}%
              </>
            )}
          </p>
        )}
        {resumeBundle?.parse_result?.warnings?.length ? (
          <ul style={{ fontSize: 12, color: "#92400E", margin: "0 0 12px 18px" }}>
            {resumeBundle.parse_result.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        ) : null}

        {resumeBundle?.draft && resumeBundle.parse_job?.status === "parsed" && (
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #E2E8F0" }}>
            <p style={{ fontWeight: 600, margin: "0 0 10px", fontSize: 14 }}>Что перенести в профиль</p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 14, fontSize: 14 }}>
              {(["profile", "prefs", "skills", "experience", "education"] as const).map(key => (
                <label key={key} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={resumeApply[key]}
                    onChange={e => setResumeApply(a => ({ ...a, [key]: e.target.checked }))}
                  />
                  {key === "profile" && "Основные поля и цели"}
                  {key === "prefs" && "Предпочтения по вакансиям (роли, локации, зарплата, формат)"}
                  {key === "skills" && "Навыки (добавятся к уже указанным)"}
                  {key === "experience" && "Опыт работы (добавится к текущим записям)"}
                  {key === "education" && "Образование (добавится к текущим записям)"}
                </label>
              ))}
            </div>
            <button
              type="button"
              disabled={importingDraft}
              onClick={handleApplyResumeDraft}
              style={{
                padding: "11px 22px",
                background: importingDraft ? "#CBD5E1" : "#3B5BDB",
                color: "#fff",
                border: "none",
                borderRadius: 12,
                fontWeight: 600,
                cursor: importingDraft ? "not-allowed" : "pointer",
                fontSize: 14,
              }}
            >
              {importingDraft ? "Применяем…" : "Применить к профилю"}
            </button>
            <p style={{ fontSize: 12, color: "#94A3B8", marginTop: 10, marginBottom: 0 }}>
              Это запишет выбранные данные на сервере. Затем при необходимости отредактируйте поля и нажмите «Сохранить профиль».
            </p>
          </div>
        )}
      </SectionCard>

      {success && (
        <div style={{ background: "#ECFDF5", color: "#059669", border: "1.5px solid #A7F3D0", borderRadius: 12, padding: "12px 18px", marginBottom: 20, fontSize: 14, fontWeight: 500, display: "flex", alignItems: "center", gap: 8 }}>
          ✓ Профиль и предпочтения по вакансиям сохранены
        </div>
      )}

      <form onSubmit={handleSave}>
        {/* Basic info */}
        <SectionCard title="Основная информация" icon="👤">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Field label={<>Имя <span style={{ color: "#EF4444" }}>*</span></>}>
              <input
                className="form-input"
                value={form.first_name ?? ""}
                onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))}
                required
                placeholder="Иван"
              />
            </Field>
            <Field label={<>Фамилия <span style={{ color: "#EF4444" }}>*</span></>}>
              <input
                className="form-input"
                value={form.last_name ?? ""}
                onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))}
                required
                placeholder="Иванов"
              />
            </Field>
          </div>
          <Field label={<>Отчество <span style={{ color: "#94A3B8", fontSize: 12, fontWeight: 400 }}>необязательно</span></>}>
            <input
              className="form-input"
              value={form.patronymic ?? ""}
              onChange={e => setForm(f => ({ ...f, patronymic: e.target.value }))}
              placeholder="Иванович"
            />
          </Field>
          <Field label="Город / регион">
            <input className="form-input" value={form.location ?? ""} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} placeholder="Москва" />
          </Field>
          <Field label="О себе">
            <textarea
              className="form-input"
              style={{ resize: "vertical", minHeight: 80 }}
              rows={3}
              value={form.bio ?? ""}
              onChange={e => setForm(f => ({ ...f, bio: e.target.value }))}
              placeholder="Кратко о вашем опыте и целях"
            />
          </Field>
        </SectionCard>

        {/* Career goals */}
        <SectionCard title="Карьерные цели" icon="🎯">
          <Field label="Желаемая должность">
            <input className="form-input" value={form.target_role ?? ""}
              onChange={e => setForm(f => ({ ...f, target_role: e.target.value }))}
              placeholder="например: Аналитик данных, Product Analyst" />
          </Field>
          <Field label="Заголовок профиля (для подбора вакансий)">
            <input
              className="form-input"
              value={form.headline ?? ""}
              onChange={e => setForm(f => ({ ...f, headline: e.target.value }))}
              placeholder="например: Data Analyst · SQL · Python"
            />
          </Field>
          <Field label="Краткое резюме (первые ~200 символов учитываются в рекомендациях)">
            <textarea
              className="form-input"
              style={{ resize: "vertical", minHeight: 72 }}
              rows={3}
              value={form.summary ?? ""}
              onChange={e => setForm(f => ({ ...f, summary: e.target.value }))}
              placeholder="Опишите, какие задачи и роли вам интересны"
            />
          </Field>
          <Field label="Желаемая отрасль">
            <input className="form-input" value={form.target_industry ?? ""}
              onChange={e => setForm(f => ({ ...f, target_industry: e.target.value }))}
              placeholder="например: FinTech, GameDev, E-commerce" />
          </Field>
        </SectionCard>

        <SectionCard title="Предпочтения по вакансиям" icon="📋">
          {prefsLoading ? (
            <p style={{ color: "#64748B", margin: 0 }}>Загрузка…</p>
          ) : (
            <div>
              <p style={{ fontSize: 13, color: "#64748B", margin: "0 0 14px" }}>
                Сохраняются вместе с остальным профилем кнопкой «Сохранить профиль» внизу страницы.
              </p>
              <Field label="Целевые роли (по одной на строку)">
                <textarea
                  className="form-input"
                  style={{ resize: "vertical", minHeight: 72 }}
                  value={prefs.target_roles.join("\n")}
                  onChange={e =>
                    setPrefs(p => ({ ...p, target_roles: parseLines(e.target.value) }))
                  }
                  placeholder={"Аналитик данных\nProduct Analyst"}
                />
              </Field>
              <Field label="Предпочитаемые локации (по одной на строке)">
                <textarea
                  className="form-input"
                  style={{ resize: "vertical", minHeight: 56 }}
                  value={prefs.preferred_locations.join("\n")}
                  onChange={e =>
                    setPrefs(p => ({ ...p, preferred_locations: parseLines(e.target.value) }))
                  }
                  placeholder="Москва\nRemote"
                />
              </Field>
              <Field label="Формат работы">
                <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                  {(["remote", "office", "hybrid"] as const).map(fmt => (
                    <label key={fmt} style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 14 }}>
                      <input
                        type="checkbox"
                        checked={prefs.work_formats.includes(fmt)}
                        onChange={e => {
                          setPrefs(p => ({
                            ...p,
                            work_formats: e.target.checked
                              ? [...p.work_formats, fmt]
                              : p.work_formats.filter(x => x !== fmt),
                          }));
                        }}
                      />
                      {fmt === "remote" ? "Удалённо" : fmt === "office" ? "Офис" : "Гибрид"}
                    </label>
                  ))}
                </div>
              </Field>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <Field label="Зарплата от (₽)">
                  <input
                    type="number"
                    className="form-input"
                    min={0}
                    value={prefs.salary_from ?? ""}
                    onChange={e =>
                      setPrefs(p => ({
                        ...p,
                        salary_from: e.target.value === "" ? null : Number(e.target.value),
                      }))
                    }
                    placeholder="120000"
                  />
                </Field>
                <Field label="Зарплата до (₽)">
                  <input
                    type="number"
                    className="form-input"
                    min={0}
                    value={prefs.salary_to ?? ""}
                    onChange={e =>
                      setPrefs(p => ({
                        ...p,
                        salary_to: e.target.value === "" ? null : Number(e.target.value),
                      }))
                    }
                    placeholder="250000"
                  />
                </Field>
              </div>
              <Field label="Уровень">
                <select
                  className="form-input"
                  value={prefs.seniority ?? ""}
                  onChange={e =>
                    setPrefs(p => ({ ...p, seniority: e.target.value || null }))
                  }
                >
                  <option value="">Не указано</option>
                  <option value="intern">Intern</option>
                  <option value="junior">Junior</option>
                  <option value="middle">Middle</option>
                  <option value="senior">Senior</option>
                  <option value="lead">Lead</option>
                </select>
              </Field>
            </div>
          )}
        </SectionCard>

        {/* Skills */}
        <SectionCard title="Навыки" icon="⚡">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16, minHeight: 32 }}>
            {skills.map(s => (
              <span key={s.id} style={{
                background: "#EEF2FF", color: "#3B5BDB", fontSize: 13, fontWeight: 500,
                borderRadius: 999, padding: "6px 14px",
                display: "inline-flex", alignItems: "center", gap: 8,
                border: "1.5px solid #C7D2FE",
              }}>
                {s.skill_name}
                <button
                  type="button"
                  onClick={() => handleRemoveSkill(s.id)}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "#94A3B8", lineHeight: 1, padding: 0, fontSize: 16, display: "flex", alignItems: "center", transition: "color 0.1s" }}
                  onMouseEnter={e => { e.currentTarget.style.color = "#DC2626"; }}
                  onMouseLeave={e => { e.currentTarget.style.color = "#94A3B8"; }}
                >
                  ×
                </button>
              </span>
            ))}
            {skills.length === 0 && (
              <span style={{ color: "#94A3B8", fontSize: 14 }}>Навыки не добавлены. Начните ввод ниже.</span>
            )}
          </div>

          <div style={{ position: "relative" }}>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                ref={skillInputRef}
                className="form-input"
                style={{ flex: 1 }}
                value={skillInput}
                onChange={e => handleSkillInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === "Enter") { e.preventDefault(); handleAddSkill(); }
                  if (e.key === "Escape") { setSuggestions([]); }
                }}
                placeholder="Введите навык или выберите из списка…"
              />
              <button
                type="button"
                onClick={() => handleAddSkill()}
                disabled={addingSkill}
                style={{ padding: "10px 18px", background: "#3B5BDB", color: "#fff", border: "none", borderRadius: 12, cursor: "pointer", fontWeight: 600, whiteSpace: "nowrap", fontSize: 14, transition: "all 0.15s" }}
                onMouseEnter={e => { e.currentTarget.style.background = "#2F4AC2"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#3B5BDB"; }}
              >
                {addingSkill ? "…" : "+ Добавить"}
              </button>
            </div>

            {suggestions.length > 0 && (
              <div style={{
                position: "absolute", top: "calc(100% + 6px)", left: 0,
                background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 14,
                boxShadow: "0 8px 32px rgba(15,23,42,0.1)", zIndex: 100,
                width: "calc(100% - 100px)", maxHeight: 240, overflowY: "auto",
                padding: "6px",
              }}>
                {suggestions.map(s => (
                  <div
                    key={s}
                    onMouseDown={e => { e.preventDefault(); handleAddSkill(s); }}
                    style={{ padding: "9px 12px", cursor: "pointer", fontSize: 14, borderRadius: 8, transition: "background 0.1s", color: "#334155" }}
                    onMouseEnter={e => { e.currentTarget.style.background = "#EEF2FF"; e.currentTarget.style.color = "#3B5BDB"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#334155"; }}
                  >
                    {s}
                  </div>
                ))}
              </div>
            )}
          </div>
          <p style={{ fontSize: 12, color: "#94A3B8", marginTop: 10, marginBottom: 0 }}>
            Начните вводить — появятся подсказки. Можно добавить свой вариант.
          </p>
        </SectionCard>

        {/* Save button */}
        <button
          type="submit"
          disabled={saving || prefsLoading}
          style={{
            padding: "13px 32px", background: saving || prefsLoading ? "#CBD5E1" : "#3B5BDB",
            color: "#fff", border: "none", borderRadius: 14,
            cursor: saving || prefsLoading ? "not-allowed" : "pointer",
            fontWeight: 700, fontSize: 15,
            boxShadow: saving || prefsLoading ? "none" : "0 4px 16px rgba(59,91,219,0.3)",
            transition: "all 0.15s",
          }}
        >
          {saving ? "Сохраняем…" : prefsLoading ? "Загрузка предпочтений…" : "Сохранить профиль"}
        </button>
      </form>
    </div>
  );
}

function SectionCard({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "24px", marginBottom: 20, boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
      <h3 style={{ margin: "0 0 20px", fontSize: 15, fontWeight: 700, color: "#0F172A", display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

function Field({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label className="form-label">{label}</label>
      {children}
    </div>
  );
}

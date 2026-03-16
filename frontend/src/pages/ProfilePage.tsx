import React, { useEffect, useRef, useState } from "react";
import {
  getProfile, updateProfile, Profile,
  getProfileSkills, addProfileSkill, removeProfileSkill, ProfileSkill,
} from "../api/profile";
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

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError(""); setSuccess(false);
    try {
      const parts = [form.first_name, form.last_name, form.patronymic].map(s => s?.trim() ?? "").filter(Boolean);
      const payload: Partial<Profile> = {
        ...form,
        full_name: parts.length ? parts.join(" ") : form.full_name,
      };
      const updated = await updateProfile(payload);
      setProfile(updated); setForm(updated); setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
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

      {success && (
        <div style={{ background: "#ECFDF5", color: "#059669", border: "1.5px solid #A7F3D0", borderRadius: 12, padding: "12px 18px", marginBottom: 20, fontSize: 14, fontWeight: 500, display: "flex", alignItems: "center", gap: 8 }}>
          ✓ Профиль успешно сохранён!
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
              placeholder="например: Senior Python Developer" />
          </Field>
          <Field label="Желаемая отрасль">
            <input className="form-input" value={form.target_industry ?? ""}
              onChange={e => setForm(f => ({ ...f, target_industry: e.target.value }))}
              placeholder="например: FinTech, GameDev, E-commerce" />
          </Field>
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
          disabled={saving}
          style={{
            padding: "13px 32px", background: saving ? "#CBD5E1" : "#3B5BDB",
            color: "#fff", border: "none", borderRadius: 14,
            cursor: saving ? "not-allowed" : "pointer",
            fontWeight: 700, fontSize: 15,
            boxShadow: saving ? "none" : "0 4px 16px rgba(59,91,219,0.3)",
            transition: "all 0.15s",
          }}
        >
          {saving ? "Сохраняем…" : "Сохранить профиль"}
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

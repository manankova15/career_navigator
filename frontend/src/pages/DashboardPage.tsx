import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MeResponse } from "../api/auth";
import { getMyProgress, UserProgress } from "../api/analytics";
import { getProfile, Profile } from "../api/profile";
import Spinner from "../components/Spinner";

interface Props { user: MeResponse; }

const QUICK_ACTIONS = [
  { to: "/vacancies", icon: "💼", label: "Найти вакансии", desc: "Поиск по 50 000+ позициям", color: "#EEF2FF", accent: "#3B5BDB" },
  { to: "/recommendations", icon: "✦", label: "Рекомендации", desc: "AI-подбор для вас", color: "#ECFDF5", accent: "#059669" },
  { to: "/assessments", icon: "📋", label: "Задания", desc: "Подготовьтесь к интервью", color: "#FFFBEB", accent: "#D97706" },
  { to: "/profile", icon: "👤", label: "Профиль", desc: "Обновите данные и навыки", color: "#FDF4FF", accent: "#7C3AED" },
];

export default function DashboardPage({ user }: Props) {
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [progressLoading, setProgressLoading] = useState(true);

  useEffect(() => {
    getMyProgress()
      .then(setProgress)
      .catch(() => {})
      .finally(() => setProgressLoading(false));
    getProfile()
      .then(setProfile)
      .catch(() => {});
  }, []);

  // Для приветствия используем имя (first_name), не фамилию
  const firstName = profile?.first_name?.trim()
    ?? user.full_name?.trim().split(/\s+/)[0]
    ?? user.email?.split("@")[0]
    ?? "пользователь";

  const stats = [
    {
      label: "Пройдено тестов",
      value: progress?.assessments_taken ?? "—",
      icon: "📋",
      color: "#EEF2FF",
      accent: "#3B5BDB",
    },
    {
      label: "Лучший результат",
      value: progress ? `${progress.best_score.toFixed(0)}%` : "—",
      icon: "🏆",
      color: "#ECFDF5",
      accent: "#059669",
    },
    {
      label: "Средний результат",
      value: progress ? `${progress.avg_score.toFixed(0)}%` : "—",
      icon: "📊",
      color: "#FFFBEB",
      accent: "#D97706",
    },
    {
      label: "Просмотрено вакансий",
      value: progress?.vacancy_views ?? "—",
      icon: "👁",
      color: "#FDF4FF",
      accent: "#7C3AED",
    },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "#0F172A", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
          Привет, {firstName}!
        </h1>
        <p style={{ color: "#64748B", margin: 0, fontSize: 15 }}>
          Вот что происходит с вашей карьерой сегодня
        </p>
      </div>

      {/* Stats grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
        {stats.map(s => (
          <div key={s.label} style={{
            background: "#fff",
            border: "1.5px solid #E2E8F0",
            borderRadius: 20,
            padding: "20px 22px",
            boxShadow: "0 1px 3px rgba(15,23,42,0.05)",
          }}>
            <div style={{ width: 40, height: 40, background: s.color, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, marginBottom: 14 }}>
              {s.icon}
            </div>
            <div style={{ fontSize: 28, fontWeight: 800, color: "#0F172A", letterSpacing: "-0.5px", lineHeight: 1 }}>
              {progressLoading ? <span style={{ fontSize: 16, color: "#94A3B8" }}>—</span> : s.value}
            </div>
            <div style={{ fontSize: 13, color: "#64748B", marginTop: 5 }}>{s.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        {/* Quick actions */}
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "24px", boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <h3 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 700, color: "#0F172A" }}>Быстрые действия</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {QUICK_ACTIONS.map(a => (
              <Link key={a.to} to={a.to} style={{ textDecoration: "none" }}>
                <div style={{
                  padding: "16px",
                  background: a.color,
                  borderRadius: 14,
                  border: "1.5px solid transparent",
                  transition: "all 0.15s",
                  cursor: "pointer",
                }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = a.accent; e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "transparent"; e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}>
                  <div style={{ fontSize: 22, marginBottom: 8 }}>{a.icon}</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#0F172A", marginBottom: 3 }}>{a.label}</div>
                  <div style={{ fontSize: 11, color: "#64748B", lineHeight: 1.4 }}>{a.desc}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent assessments */}
        <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "24px", boxShadow: "0 1px 3px rgba(15,23,42,0.05)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: "#0F172A" }}>Последние задания</h3>
            <Link to="/assessments" style={{ fontSize: 13, color: "#3B5BDB", textDecoration: "none", fontWeight: 500 }}>
              Все →
            </Link>
          </div>

          {progressLoading && <Spinner />}

          {!progressLoading && progress && progress.recent_stats.length === 0 && (
            <div style={{ textAlign: "center", padding: "32px 0" }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>📋</div>
              <div style={{ fontSize: 14, color: "#64748B", marginBottom: 12 }}>Заданий пока нет</div>
              <Link to="/assessments" style={{ display: "inline-flex", padding: "8px 18px", background: "#3B5BDB", color: "#fff", borderRadius: 8, textDecoration: "none", fontSize: 13, fontWeight: 600 }}>
                Начать →
              </Link>
            </div>
          )}

          {progress?.recent_stats.slice(0, 5).map((s, i) => (
            <div key={s.assessment_id} style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "12px 0",
              borderBottom: i < Math.min((progress.recent_stats.length - 1), 4) ? "1px solid #F1F5F9" : "none",
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#0F172A" }}>{s.topic ?? "Задание"}</div>
                <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>
                  Попыток: {s.attempts_count} · Средний: {s.avg_percentage.toFixed(0)}%
                </div>
              </div>
              <div style={{
                padding: "4px 10px",
                borderRadius: 999,
                background: s.best_percentage >= 70 ? "#ECFDF5" : "#FFFBEB",
                color: s.best_percentage >= 70 ? "#059669" : "#D97706",
                fontSize: 13,
                fontWeight: 700,
              }}>
                {s.best_percentage.toFixed(0)}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

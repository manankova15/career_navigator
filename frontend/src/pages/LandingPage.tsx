import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

interface Props { onNavigateToSearch?: (params: Record<string, string>) => void; }

const TOP_ROLES = [
  { icon: "⚙️", label: "Backend Developer", count: "1 240+" },
  { icon: "🎨", label: "Frontend Developer", count: "980+" },
  { icon: "📊", label: "Data Scientist", count: "540+" },
  { icon: "📱", label: "Mobile Developer", count: "410+" },
  { icon: "☁️", label: "DevOps / Cloud", count: "360+" },
  { icon: "🤖", label: "ML Engineer", count: "290+" },
  { icon: "🎯", label: "Product Manager", count: "720+" },
  { icon: "🛡️", label: "QA Engineer", count: "480+" },
];

const TESTIMONIALS = [
  {
    name: "Алексей Морозов",
    role: "Senior Backend Developer",
    company: "Yandex",
    text: "Career Navigator нашёл мне позицию за 3 недели. AI-подбор предложил вакансии, о которых я сам бы не подумал.",
    avatar: "АМ",
  },
  {
    name: "Мария Соколова",
    role: "Data Analyst",
    company: "Сбер",
    text: "Анализ пробелов в навыках помог мне понять, чему учиться. Через месяц я уже проходила собеседования в топовые компании.",
    avatar: "МС",
  },
  {
    name: "Дмитрий Лебедев",
    role: "Product Manager",
    company: "VK",
    text: "Лучший сервис для поиска работы в IT. Персонализированные рекомендации и тесты-задания — это реально работает.",
    avatar: "ДЛ",
  },
];

export default function LandingPage() {
  const navigate = useNavigate();
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [employmentType, setEmploymentType] = useState("");
  const [experience, setExperience] = useState("");
  const [remote, setRemote] = useState("");

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (role) params.set("q", role);
    if (location) params.set("loc", location);
    navigate(`/login`);
  }

  return (
    <div style={{ background: "#F8FAFC", minHeight: "100vh", fontFamily: "var(--font, system-ui, sans-serif)" }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="landing-nav">
        <div style={{ maxWidth: 1200, margin: "0 auto", width: "100%", padding: "0 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, overflow: "hidden", flexShrink: 0 }}>
                <img src="/pictures/hr-avatar-career-assistant.webp" alt="Career Navigator" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
              </div>
              <span style={{ fontSize: 16, fontWeight: 700, color: "var(--text-heading, #0F172A)", letterSpacing: "-0.3px" }}>Career Navigator</span>
            </div>
            <nav style={{ display: "flex", gap: 4 }}>
              {["Вакансии", "Компании", "Ресурсы"].map(item => (
                <a key={item} href="#" style={{ padding: "6px 14px", color: "#64748B", textDecoration: "none", fontSize: 14, fontWeight: 500, borderRadius: 8, transition: "all 0.15s" }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#F1F5F9"; e.currentTarget.style.color = "#0F172A"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#64748B"; }}>
                  {item}
                </a>
              ))}
            </nav>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ fontSize: 13, color: "#64748B", padding: "4px 10px", borderRadius: 6, border: "1px solid #E2E8F0", cursor: "pointer" }}>🌍 RU</span>
            </div>
            <Link to="/login" style={{ padding: "9px 18px", color: "#334155", textDecoration: "none", fontSize: 14, fontWeight: 500, border: "1.5px solid #E2E8F0", borderRadius: 10, background: "#fff", transition: "all 0.15s" }}>
              Войти
            </Link>
            <Link to="/register" style={{ padding: "9px 20px", background: "var(--primary, #3B5BDB)", color: "#fff", textDecoration: "none", fontSize: 14, fontWeight: 600, borderRadius: 10, boxShadow: "0 2px 8px rgba(59,91,219,0.25)", transition: "all 0.15s" }}>
              Начать бесплатно
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────────────── */}
      <section style={{ paddingTop: 100, paddingBottom: 80, maxWidth: 1200, margin: "0 auto", padding: "100px 32px 80px" }}>
        <div className="hero-grid" style={{ display: "flex", gap: 64, alignItems: "center" }}>

          {/* Left column */}
          <div style={{ flex: "0 0 520px", maxWidth: 520 }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "#EEF2FF", border: "1px solid #C7D2FE", borderRadius: 999, padding: "6px 14px", marginBottom: 24 }}>
              <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#3B5BDB", display: "inline-block" }}></span>
              <span style={{ fontSize: 13, fontWeight: 500, color: "#3B5BDB" }}>AI-подбор вакансий нового поколения</span>
            </div>

            <h1 style={{ fontSize: 52, fontWeight: 800, color: "#0F172A", lineHeight: 1.1, letterSpacing: "-1.5px", margin: "0 0 20px" }}>
              Найдите работу,<br />
              <span style={{ color: "#3B5BDB" }}>которая вас<br />вдохновит</span>
            </h1>
            <p style={{ fontSize: 18, color: "#475569", lineHeight: 1.65, margin: "0 0 36px", maxWidth: 440 }}>
              Умный поиск, AI-рекомендации и персонализированные задания — всё, чтобы вы нашли идеальную позицию быстрее.
            </p>

            {/* Search form */}
            <form onSubmit={handleSearch} style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "20px 20px 16px", boxShadow: "0 8px 40px rgba(15,23,42,0.08)" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 5 }}>Роль / Должность</label>
                  <input
                    className="hero-search-input"
                    value={role}
                    onChange={e => setRole(e.target.value)}
                    placeholder="например, Python Developer"
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 5 }}>Локация</label>
                  <input
                    className="hero-search-input"
                    value={location}
                    onChange={e => setLocation(e.target.value)}
                    placeholder="Москва, Санкт-Петербург…"
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 5 }}>Тип занятости</label>
                  <div style={{ position: "relative" }}>
                    <select className="hero-search-select" value={employmentType} onChange={e => setEmploymentType(e.target.value)}>
                      <option value="">Любой тип</option>
                      <option value="full-time">Полная занятость</option>
                      <option value="part-time">Частичная</option>
                      <option value="contract">Контракт</option>
                      <option value="freelance">Фриланс</option>
                    </select>
                    <span style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", pointerEvents: "none", color: "#94A3B8", fontSize: 12 }}>▼</span>
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 5 }}>Опыт</label>
                  <div style={{ position: "relative" }}>
                    <select className="hero-search-select" value={experience} onChange={e => setExperience(e.target.value)}>
                      <option value="">Любой опыт</option>
                      <option value="junior">Junior (0–2 года)</option>
                      <option value="middle">Middle (2–5 лет)</option>
                      <option value="senior">Senior (5+ лет)</option>
                      <option value="lead">Lead / Principal</option>
                    </select>
                    <span style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", pointerEvents: "none", color: "#94A3B8", fontSize: 12 }}>▼</span>
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 14 }}>
                {["Remote", "Hybrid", "On-site"].map(opt => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setRemote(remote === opt ? "" : opt)}
                    style={{
                      padding: "6px 14px",
                      borderRadius: 999,
                      border: "1.5px solid",
                      borderColor: remote === opt ? "#3B5BDB" : "#E2E8F0",
                      background: remote === opt ? "#EEF2FF" : "#fff",
                      color: remote === opt ? "#3B5BDB" : "#64748B",
                      fontSize: 13,
                      fontWeight: 500,
                      cursor: "pointer",
                      transition: "all 0.15s",
                    }}
                  >
                    {opt}
                  </button>
                ))}
              </div>

              <button
                type="submit"
                style={{
                  width: "100%",
                  padding: "14px",
                  background: "#3B5BDB",
                  color: "#fff",
                  border: "none",
                  borderRadius: 14,
                  fontSize: 15,
                  fontWeight: 700,
                  cursor: "pointer",
                  letterSpacing: "0.2px",
                  boxShadow: "0 4px 16px rgba(59,91,219,0.3)",
                  transition: "all 0.15s",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "#2F4AC2"; e.currentTarget.style.boxShadow = "0 6px 24px rgba(59,91,219,0.4)"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#3B5BDB"; e.currentTarget.style.boxShadow = "0 4px 16px rgba(59,91,219,0.3)"; }}
              >
                Найти вакансии →
              </button>
            </form>

            {/* Stats strip */}
            <div style={{ display: "flex", gap: 24, marginTop: 20 }}>
              {[
                { val: "50 000+", lbl: "вакансий" },
                { val: "1 200+", lbl: "компаний" },
                { val: "98%", lbl: "точность AI" },
              ].map(s => (
                <div key={s.lbl}>
                  <div style={{ fontSize: 17, fontWeight: 700, color: "#0F172A" }}>{s.val}</div>
                  <div style={{ fontSize: 12, color: "#94A3B8" }}>{s.lbl}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right column — hero image */}
          <div className="hero-image-col" style={{ flex: 1, position: "relative", minHeight: 520 }}>
            <div style={{
              borderRadius: 28,
              overflow: "hidden",
              boxShadow: "0 32px 80px rgba(15,23,42,0.16)",
              width: "100%",
              height: 520,
              position: "relative",
            }}>
              <img
                src="/pictures/professionals-in-modern-office.webp"
                alt="Professionals in modern office"
                style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
              />
              <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, rgba(59,91,219,0.08) 0%, transparent 60%)" }} />
            </div>

            {/* Floating card 1 */}
            <div style={{
              position: "absolute", bottom: 72, left: -28,
              background: "#fff", borderRadius: 16,
              boxShadow: "0 8px 32px rgba(15,23,42,0.12)",
              border: "1px solid #E2E8F0",
              padding: "14px 18px",
              minWidth: 180,
            }}>
              <div style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4, fontWeight: 500 }}>AI Match Score</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "#0F172A" }}>96%</div>
              <div style={{ fontSize: 12, color: "#3B5BDB", fontWeight: 500, marginTop: 2 }}>Senior Python Dev</div>
            </div>

            {/* Floating card 2 */}
            <div style={{
              position: "absolute", top: 32, right: -20,
              background: "#fff", borderRadius: 16,
              boxShadow: "0 8px 32px rgba(15,23,42,0.12)",
              border: "1px solid #E2E8F0",
              padding: "14px 18px",
              minWidth: 160,
            }}>
              <div style={{ fontSize: 11, color: "#94A3B8", marginBottom: 4, fontWeight: 500 }}>Новых вакансий</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "#0F172A" }}>+127</div>
              <div style={{ fontSize: 12, color: "#059669", fontWeight: 500, marginTop: 2 }}>за сегодня</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Top Roles ──────────────────────────────────────────────────────── */}
      <section style={{ background: "#fff", borderTop: "1px solid #E2E8F0", borderBottom: "1px solid #E2E8F0", padding: "64px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#3B5BDB", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 12 }}>Популярные направления</div>
            <h2 className="section-title">Топ ролей на рынке</h2>
            <p className="section-subtitle" style={{ marginTop: 8, maxWidth: 500, margin: "8px auto 0" }}>
              Найдите позицию по своей специализации среди тысяч актуальных вакансий
            </p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
            {TOP_ROLES.map(r => (
              <Link
                key={r.label}
                to="/login"
                style={{
                  display: "flex", alignItems: "center", gap: 14,
                  padding: "18px 20px",
                  background: "#F8FAFC",
                  border: "1.5px solid #E2E8F0",
                  borderRadius: 16,
                  textDecoration: "none",
                  transition: "all 0.15s",
                  cursor: "pointer",
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "#3B5BDB"; e.currentTarget.style.background = "#EEF2FF"; e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(59,91,219,0.12)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "#E2E8F0"; e.currentTarget.style.background = "#F8FAFC"; e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
              >
                <span style={{ fontSize: 22 }}>{r.icon}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#0F172A" }}>{r.label}</div>
                  <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>{r.count} вакансий</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── AI Matching ────────────────────────────────────────────────────── */}
      <section style={{ padding: "80px 32px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 80, alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#3B5BDB", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 16 }}>Технология</div>
            <h2 className="section-title" style={{ marginBottom: 16 }}>AI, который знает<br />ваши сильные стороны</h2>
            <p className="section-subtitle" style={{ marginBottom: 32 }}>
              Алгоритм анализирует ваш профиль, навыки и опыт, чтобы предложить вакансии с максимальным совпадением — без шума и нерелевантных предложений.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              {[
                { icon: "🎯", title: "Точный подбор", text: "Совпадение по навыкам, грейду и индустрии" },
                { icon: "📈", title: "Анализ пробелов", text: "Узнайте, какие навыки прокачать для карьерного роста" },
                { icon: "📋", title: "Задания и тесты", text: "Подготовьтесь к собеседованию с персональными заданиями" },
              ].map(f => (
                <div key={f.title} style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
                  <div style={{ width: 44, height: 44, background: "#EEF2FF", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>
                    {f.icon}
                  </div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: "#0F172A", marginBottom: 3 }}>{f.title}</div>
                    <div style={{ fontSize: 14, color: "#64748B", lineHeight: 1.5 }}>{f.text}</div>
                  </div>
                </div>
              ))}
            </div>
            <Link to="/register" style={{ display: "inline-flex", marginTop: 32, padding: "12px 24px", background: "#3B5BDB", color: "#fff", borderRadius: 12, textDecoration: "none", fontWeight: 600, fontSize: 14, boxShadow: "0 4px 16px rgba(59,91,219,0.3)" }}>
              Попробовать бесплатно →
            </Link>
          </div>

          <div style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 24, padding: "32px", boxShadow: "0 8px 40px rgba(15,23,42,0.07)" }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#94A3B8", marginBottom: 20 }}>Ваши рекомендации</div>
            {[
              { title: "Senior Python Developer", company: "Яндекс", score: 96, salary: "350 000 ₽" },
              { title: "Backend Engineer", company: "Тинькофф", score: 89, salary: "280 000 ₽" },
              { title: "Team Lead Python", company: "Озон", score: 84, salary: "420 000 ₽" },
            ].map((job, i) => (
              <div key={job.title} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "14px 16px",
                background: i === 0 ? "#EEF2FF" : "#F8FAFC",
                borderRadius: 12,
                border: "1.5px solid",
                borderColor: i === 0 ? "#C7D2FE" : "#E2E8F0",
                marginBottom: 10,
              }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#0F172A" }}>{job.title}</div>
                  <div style={{ fontSize: 12, color: "#64748B", marginTop: 3 }}>{job.company} · {job.salary}</div>
                </div>
                <div style={{
                  background: i === 0 ? "#3B5BDB" : "#E2E8F0",
                  color: i === 0 ? "#fff" : "#64748B",
                  borderRadius: 999,
                  padding: "4px 10px",
                  fontSize: 12,
                  fontWeight: 700,
                  whiteSpace: "nowrap",
                }}>
                  {job.score}%
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trusted by employers ───────────────────────────────────────────── */}
      <section style={{ background: "#fff", borderTop: "1px solid #E2E8F0", borderBottom: "1px solid #E2E8F0", padding: "56px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", textAlign: "center" }}>
          <div style={{ fontSize: 13, color: "#94A3B8", marginBottom: 32, fontWeight: 500 }}>Нам доверяют ведущие работодатели</div>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", flexWrap: "wrap", gap: 40 }}>
            {["Яндекс", "Сбер", "Тинькофф", "VK", "Озон", "Авито", "HeadHunter", "Kaspersky"].map(c => (
              <div key={c} style={{ fontSize: 18, fontWeight: 700, color: "#CBD5E1", letterSpacing: "-0.3px", userSelect: "none" }}>{c}</div>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 32, marginTop: 56, maxWidth: 800, margin: "56px auto 0" }}>
            {[
              { val: "50 000+", lbl: "Активных вакансий", icon: "💼" },
              { val: "1 200+", lbl: "Компаний-партнёров", icon: "🏢" },
              { val: "120 000+", lbl: "Успешных трудоустройств", icon: "🎉" },
            ].map(s => (
              <div key={s.lbl} style={{ padding: "28px 20px", background: "#F8FAFC", borderRadius: 16, border: "1px solid #E2E8F0" }}>
                <div style={{ fontSize: 28 }}>{s.icon}</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: "#0F172A", letterSpacing: "-1px", margin: "8px 0 4px" }}>{s.val}</div>
                <div style={{ fontSize: 14, color: "#64748B" }}>{s.lbl}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ───────────────────────────────────────────────────── */}
      <section style={{ padding: "80px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#3B5BDB", textTransform: "uppercase", letterSpacing: "1px", marginBottom: 12 }}>Отзывы</div>
            <h2 className="section-title">Истории успеха</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
            {TESTIMONIALS.map(t => (
              <div key={t.name} style={{ background: "#fff", border: "1.5px solid #E2E8F0", borderRadius: 20, padding: "28px", boxShadow: "0 4px 16px rgba(15,23,42,0.04)" }}>
                <div style={{ fontSize: 24, marginBottom: 16, lineHeight: 1 }}>⭐⭐⭐⭐⭐</div>
                <p style={{ fontSize: 15, color: "#334155", lineHeight: 1.7, margin: "0 0 24px", fontStyle: "italic" }}>
                  «{t.text}»
                </p>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ width: 40, height: 40, borderRadius: "50%", background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "#3B5BDB" }}>
                    {t.avatar}
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "#0F172A" }}>{t.name}</div>
                    <div style={{ fontSize: 12, color: "#94A3B8" }}>{t.role} · {t.company}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Mobile app CTA ─────────────────────────────────────────────────── */}
      <section style={{ padding: "0 32px 80px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ background: "linear-gradient(135deg, #3B5BDB 0%, #5C7CFA 100%)", borderRadius: 28, padding: "56px 64px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 40, flexWrap: "wrap" }}>
            <div style={{ color: "#fff" }}>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "1px", opacity: 0.7, marginBottom: 12 }}>Мобильное приложение</div>
              <h2 style={{ fontSize: 36, fontWeight: 800, margin: "0 0 12px", letterSpacing: "-0.8px", lineHeight: 1.2 }}>
                Поиск работы<br />в вашем кармане
              </h2>
              <p style={{ fontSize: 16, opacity: 0.85, lineHeight: 1.6, margin: 0, maxWidth: 380 }}>
                Получайте уведомления о новых вакансиях, проходите тесты и управляйте откликами прямо со смартфона.
              </p>
              <div style={{ display: "flex", gap: 12, marginTop: 28 }}>
                {["App Store", "Google Play"].map(s => (
                  <div key={s} style={{ padding: "12px 20px", background: "rgba(255,255,255,0.15)", backdropFilter: "blur(10px)", border: "1.5px solid rgba(255,255,255,0.3)", borderRadius: 12, cursor: "pointer", fontSize: 14, fontWeight: 600, color: "#fff", transition: "all 0.15s" }}>
                    {s === "App Store" ? "🍎 " : "🤖 "}{s}
                  </div>
                ))}
              </div>
            </div>
            <div style={{ background: "rgba(255,255,255,0.1)", borderRadius: 20, padding: "24px 32px", border: "1.5px solid rgba(255,255,255,0.2)", minWidth: 200, textAlign: "center" }}>
              <div style={{ fontSize: 48, marginBottom: 8 }}>📱</div>
              <div style={{ color: "#fff", fontSize: 14, fontWeight: 500, opacity: 0.9 }}>Сканируйте QR-код</div>
              <div style={{ color: "#fff", fontSize: 12, opacity: 0.6, marginTop: 4 }}>для скачивания</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <footer style={{ background: "#0F172A", color: "#94A3B8", padding: "56px 32px 32px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 48, marginBottom: 48 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, overflow: "hidden", flexShrink: 0 }}>
                  <img src="/pictures/hr-avatar-career-assistant.webp" alt="Career Navigator" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                </div>
                <span style={{ fontSize: 16, fontWeight: 700, color: "#F1F5F9" }}>Career Navigator</span>
              </div>
              <p style={{ fontSize: 14, lineHeight: 1.65, maxWidth: 280, margin: 0 }}>
                AI-платформа для поиска работы и развития карьеры в IT и технологических компаниях.
              </p>
            </div>
            {[
              { title: "Соискателям", links: ["Найти вакансии", "Рекомендации", "Тесты и задания", "Профиль"] },
              { title: "Работодателям", links: ["Разместить вакансию", "AI-подбор", "Аналитика", "Тарифы"] },
              { title: "Компания", links: ["О нас", "Блог", "Карьера", "Контакты"] },
            ].map(col => (
              <div key={col.title}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#F1F5F9", marginBottom: 16, textTransform: "uppercase", letterSpacing: "0.5px" }}>{col.title}</div>
                {col.links.map(l => (
                  <div key={l} style={{ marginBottom: 10 }}>
                    <a href="#" style={{ fontSize: 14, color: "#64748B", textDecoration: "none", transition: "color 0.15s" }}
                      onMouseEnter={e => e.currentTarget.style.color = "#94A3B8"}
                      onMouseLeave={e => e.currentTarget.style.color = "#64748B"}>
                      {l}
                    </a>
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div style={{ borderTop: "1px solid #1E293B", paddingTop: 24, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
            <div style={{ fontSize: 13 }}>© 2025 Career Navigator. Все права защищены.</div>
            <div style={{ display: "flex", gap: 20 }}>
              {["Политика конфиденциальности", "Условия использования"].map(l => (
                <a key={l} href="#" style={{ fontSize: 13, color: "#64748B", textDecoration: "none" }}>{l}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register, getMe, MeResponse } from "../api/auth";
import { updateProfile } from "../api/profile";
import ErrorBanner from "../components/ErrorBanner";

interface Props { onLogin: (user: MeResponse) => void; }

export default function RegisterPage({ onLogin }: Props) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [patronymic, setPatronymic] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const parts = [firstName.trim(), lastName.trim(), patronymic.trim()].filter(Boolean);
      const fullName = parts.join(" ");
      await register(email, password, fullName);
      await updateProfile({
        full_name: fullName,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        patronymic: patronymic.trim() || null,
      }).catch(() => {});
      const user = await getMe();
      onLogin(user);
      navigate("/");
    } catch (err: any) {
      setError(err.message ?? "Ошибка регистрации");
    } finally { setLoading(false); }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "#F8FAFC", fontFamily: "var(--font, system-ui, sans-serif)" }}>

      {/* Left panel — decorative */}
      <div style={{ flex: 1, background: "linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #334155 100%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "64px", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: -100, left: -100, width: 360, height: 360, background: "rgba(59,91,219,0.15)", borderRadius: "50%" }} />
        <div style={{ position: "absolute", bottom: -80, right: -80, width: 280, height: 280, background: "rgba(59,91,219,0.1)", borderRadius: "50%" }} />

        <div style={{ position: "relative", zIndex: 1, textAlign: "center", color: "#fff" }}>
          <div style={{ fontSize: 56, marginBottom: 24 }}>✨</div>
          <h2 style={{ fontSize: 28, fontWeight: 800, margin: "0 0 16px", letterSpacing: "-0.5px", lineHeight: 1.2 }}>
            Начните карьерный<br />путь прямо сейчас
          </h2>
          <p style={{ fontSize: 15, opacity: 0.7, maxWidth: 300, lineHeight: 1.65, margin: "0 auto 40px" }}>
            Присоединяйтесь к тысячам специалистов, которые уже нашли работу мечты через Career Navigator
          </p>
          <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: 16, padding: "20px 24px", border: "1px solid rgba(255,255,255,0.1)", textAlign: "left" }}>
            <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", marginBottom: 12, fontWeight: 500 }}>Регистрация занимает</div>
            <div style={{ fontSize: 32, fontWeight: 800, color: "#fff" }}>30 секунд</div>
            <div style={{ fontSize: 14, color: "rgba(255,255,255,0.6)", marginTop: 4 }}>и это абсолютно бесплатно</div>
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 40px", position: "relative" }}>
        <div style={{ position: "absolute", top: 28, right: 40, display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, overflow: "hidden", flexShrink: 0 }}>
            <img src="/pictures/hr-avatar-career-assistant.webp" alt="Career Navigator" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
          </div>
          <Link to="/" style={{ fontSize: 15, fontWeight: 700, color: "#0F172A", textDecoration: "none", letterSpacing: "-0.3px" }}>Career Navigator</Link>
        </div>

        <div style={{ width: "100%", maxWidth: 400 }}>
          <h1 style={{ fontSize: 30, fontWeight: 800, color: "#0F172A", margin: "0 0 8px", letterSpacing: "-0.6px" }}>
            Создать аккаунт
          </h1>
          <p style={{ color: "#64748B", marginBottom: 32, marginTop: 0, fontSize: 15 }}>
            Бесплатно. Без кредитной карты.
          </p>

          {error && <ErrorBanner message={error} />}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label className="form-label">
                Имя <span style={{ color: "#EF4444" }}>*</span>
              </label>
              <input
                className="form-input"
                value={firstName}
                onChange={e => setFirstName(e.target.value)}
                required
                autoFocus
                placeholder="Иван"
              />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label className="form-label">
                Фамилия <span style={{ color: "#EF4444" }}>*</span>
              </label>
              <input
                className="form-input"
                value={lastName}
                onChange={e => setLastName(e.target.value)}
                required
                placeholder="Иванов"
              />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label className="form-label">
                Отчество{" "}
                <span style={{ color: "#94A3B8", fontSize: 12, fontWeight: 400 }}>необязательно</span>
              </label>
              <input
                className="form-input"
                value={patronymic}
                onChange={e => setPatronymic(e.target.value)}
                placeholder="Иванович"
              />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="your@email.com"
              />
            </div>
            <div style={{ marginBottom: 28 }}>
              <label className="form-label">Пароль</label>
              <input
                className="form-input"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="Минимум 8 символов"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%", padding: "13px", background: "#3B5BDB", color: "#fff",
                border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1,
                boxShadow: "0 4px 16px rgba(59,91,219,0.3)",
                transition: "all 0.15s",
              }}
            >
              {loading ? "Создаём аккаунт…" : "Создать аккаунт →"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 24, color: "#64748B", fontSize: 14 }}>
            Уже есть аккаунт?{" "}
            <Link to="/login" style={{ color: "#3B5BDB", fontWeight: 600, textDecoration: "none" }}>
              Войти
            </Link>
          </p>

          <p style={{ textAlign: "center", marginTop: 16, color: "#94A3B8", fontSize: 12, lineHeight: 1.5 }}>
            Регистрируясь, вы соглашаетесь с{" "}
            <a href="#" style={{ color: "#64748B" }}>условиями использования</a>
            {" "}и{" "}
            <a href="#" style={{ color: "#64748B" }}>политикой конфиденциальности</a>
          </p>
        </div>
      </div>
    </div>
  );
}

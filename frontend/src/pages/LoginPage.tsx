import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api/auth";
import { MeResponse } from "../api/auth";
import ErrorBanner from "../components/ErrorBanner";

interface Props { onLogin: (user: MeResponse) => void; }

export default function LoginPage({ onLogin }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const user = await login(email, password);
      onLogin(user);
      navigate("/");
    } catch (err: any) {
      setError(err.message ?? "Ошибка входа");
    } finally { setLoading(false); }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "#F8FAFC", fontFamily: "var(--font, system-ui, sans-serif)" }}>

      {/* Left panel */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 40px" }}>
        {/* Logo */}
        <div style={{ position: "absolute", top: 28, left: 40, display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, overflow: "hidden", flexShrink: 0 }}>
            <img src="/pictures/hr-avatar-career-assistant.webp" alt="Career Navigator" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
          </div>
          <Link to="/" style={{ fontSize: 15, fontWeight: 700, color: "#0F172A", textDecoration: "none", letterSpacing: "-0.3px" }}>Career Navigator</Link>
        </div>

        <div style={{ width: "100%", maxWidth: 400 }}>
          <h1 style={{ fontSize: 30, fontWeight: 800, color: "#0F172A", margin: "0 0 8px", letterSpacing: "-0.6px" }}>
            Добро пожаловать
          </h1>
          <p style={{ color: "#64748B", marginBottom: 32, marginTop: 0, fontSize: 15, lineHeight: 1.5 }}>
            Войдите, чтобы продолжить поиск вашей идеальной работы
          </p>

          {error && <ErrorBanner message={error} />}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoFocus
                placeholder="your@email.com"
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 5 }}>
                <label className="form-label" style={{ marginBottom: 0 }}>Пароль</label>
                <Link to="/forgot-password" style={{ fontSize: 13, color: "#3B5BDB", textDecoration: "none" }}>Забыли пароль?</Link>
              </div>
              <input
                className="form-input"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                placeholder="••••••••"
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
                letterSpacing: "0.1px",
              }}
            >
              {loading ? "Входим…" : "Войти"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 24, color: "#64748B", fontSize: 14 }}>
            Нет аккаунта?{" "}
            <Link to="/register" style={{ color: "#3B5BDB", fontWeight: 600, textDecoration: "none" }}>
              Зарегистрироваться
            </Link>
          </p>
        </div>
      </div>

      {/* Right panel — decorative */}
      <div style={{ flex: 1, background: "linear-gradient(135deg, #3B5BDB 0%, #5C7CFA 50%, #748FFC 100%)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "64px", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: -80, right: -80, width: 320, height: 320, background: "rgba(255,255,255,0.06)", borderRadius: "50%" }} />
        <div style={{ position: "absolute", bottom: -60, left: -60, width: 240, height: 240, background: "rgba(255,255,255,0.06)", borderRadius: "50%" }} />

        <div style={{ position: "relative", zIndex: 1, textAlign: "center", color: "#fff" }}>
          <div style={{ fontSize: 56, marginBottom: 24 }}>🚀</div>
          <h2 style={{ fontSize: 28, fontWeight: 800, margin: "0 0 16px", letterSpacing: "-0.5px", lineHeight: 1.2 }}>
            Найдите работу<br />мечты сегодня
          </h2>
          <p style={{ fontSize: 16, opacity: 0.85, maxWidth: 320, lineHeight: 1.65, margin: "0 auto 40px" }}>
            AI-подбор вакансий, персонализированные рекомендации и умные тесты — всё в одном месте
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 280, margin: "0 auto" }}>
            {[
              { icon: "✦", text: "50 000+ актуальных вакансий" },
              { icon: "✦", text: "AI-подбор по вашим навыкам" },
              { icon: "✦", text: "Анализ пробелов в знаниях" },
            ].map(f => (
              <div key={f.text} style={{ display: "flex", alignItems: "center", gap: 12, background: "rgba(255,255,255,0.12)", borderRadius: 12, padding: "12px 16px" }}>
                <span style={{ fontSize: 14, opacity: 0.8 }}>{f.icon}</span>
                <span style={{ fontSize: 14, fontWeight: 500 }}>{f.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

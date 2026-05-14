import React, { useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api/auth";
import ErrorBanner from "../components/ErrorBanner";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      setMessage(
        res?.message ||
          "Если такой email зарегистрирован в системе, мы отправили на него письмо с временным паролем.",
      );
    } catch (err: any) {
      setError(err.message ?? "Не удалось отправить запрос. Попробуйте ещё раз.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        background: "#F8FAFC",
        fontFamily: "var(--font, system-ui, sans-serif)",
      }}
    >
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "48px 40px",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 28,
            left: 40,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <div style={{ width: 32, height: 32, borderRadius: 8, overflow: "hidden", flexShrink: 0 }}>
            <img
              src="/pictures/hr-avatar-career-assistant.webp"
              alt="Career Navigator"
              style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
            />
          </div>
          <Link
            to="/"
            style={{
              fontSize: 15,
              fontWeight: 700,
              color: "#0F172A",
              textDecoration: "none",
              letterSpacing: "-0.3px",
            }}
          >
            Career Navigator
          </Link>
        </div>

        <div style={{ width: "100%", maxWidth: 420 }}>
          <h1
            style={{
              fontSize: 28,
              fontWeight: 800,
              color: "#0F172A",
              margin: "0 0 8px",
              letterSpacing: "-0.6px",
            }}
          >
            Восстановление пароля
          </h1>
          <p
            style={{
              color: "#64748B",
              marginBottom: 28,
              marginTop: 0,
              fontSize: 15,
              lineHeight: 1.5,
            }}
          >
            Укажите ваш email — мы отправим на него временный пароль, с которым вы сможете войти в систему.
          </p>

          {error && <ErrorBanner message={error} />}
          {message && (
            <div
              role="status"
              style={{
                background: "#ECFDF5",
                border: "1px solid #A7F3D0",
                color: "#065F46",
                borderRadius: 12,
                padding: "12px 14px",
                fontSize: 14,
                lineHeight: 1.5,
                marginBottom: 16,
              }}
            >
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 20 }}>
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

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "13px",
                background: "#3B5BDB",
                color: "#fff",
                border: "none",
                borderRadius: 12,
                fontSize: 15,
                fontWeight: 700,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1,
                boxShadow: "0 4px 16px rgba(59,91,219,0.3)",
                transition: "all 0.15s",
                letterSpacing: "0.1px",
              }}
            >
              {loading ? "Отправляем…" : "Отправить временный пароль"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 24, color: "#64748B", fontSize: 14 }}>
            Вспомнили пароль?{" "}
            <Link
              to="/login"
              style={{ color: "#3B5BDB", fontWeight: 600, textDecoration: "none" }}
            >
              Войти
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

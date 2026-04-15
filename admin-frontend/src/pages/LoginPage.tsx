import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0f172a",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 400,
          padding: 32,
          borderRadius: 12,
          background: "#1e293b",
          color: "#f1f5f9",
        }}
      >
        <h1 style={{ margin: "0 0 8px", fontSize: 22 }}>Админ-панель</h1>
        <p style={{ margin: "0 0 24px", fontSize: 14, color: "#94a3b8" }}>
          Career Navigator — отдельный вход для администраторов (порт 3001).
        </p>
        <form onSubmit={handleSubmit}>
          <label style={{ display: "block", marginBottom: 12, fontSize: 13 }}>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                display: "block",
                width: "100%",
                marginTop: 6,
                padding: "10px 12px",
                borderRadius: 8,
                border: "1px solid #334155",
                background: "#0f172a",
                color: "#f8fafc",
              }}
            />
          </label>
          <label style={{ display: "block", marginBottom: 16, fontSize: 13 }}>
            Пароль
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                display: "block",
                width: "100%",
                marginTop: 6,
                padding: "10px 12px",
                borderRadius: 8,
                border: "1px solid #334155",
                background: "#0f172a",
                color: "#f8fafc",
              }}
            />
          </label>
          {error ? (
            <p style={{ color: "#f87171", fontSize: 14, marginBottom: 12 }}>{error}</p>
          ) : null}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px 16px",
              borderRadius: 8,
              border: "none",
              background: "#3b82f6",
              color: "#fff",
              fontWeight: 600,
              cursor: loading ? "wait" : "pointer",
            }}
          >
            {loading ? "Вход…" : "Войти"}
          </button>
        </form>
        <p style={{ marginTop: 20, fontSize: 12, color: "#64748b" }}>
          Пользовательский сайт:{" "}
          <a href="http://localhost:3000/" style={{ color: "#93c5fd" }}>
            localhost:3000
          </a>
        </p>
      </div>
    </div>
  );
}

import { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";

const navLinkStyle = (isActive: boolean): React.CSSProperties => ({
  padding: "6px 12px",
  borderRadius: 6,
  color: isActive ? "#0f172a" : "#cbd5e1",
  background: isActive ? "#f8fafc" : "transparent",
  textDecoration: "none",
  fontSize: 14,
  fontWeight: 500,
});

export default function AdminLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "system-ui, sans-serif" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          background: "#0f172a",
          color: "#f8fafc",
          gap: 16,
        }}
      >
        <strong style={{ marginRight: 16 }}>Career Navigator — админ</strong>
        <nav style={{ display: "flex", gap: 8, flex: 1 }}>
          <NavLink to="/" end style={({ isActive }) => navLinkStyle(isActive)}>
            Главная
          </NavLink>
          <NavLink to="/tests" style={({ isActive }) => navLinkStyle(isActive)}>
            Тесты
          </NavLink>
          <NavLink to="/ingestion-runs" style={({ isActive }) => navLinkStyle(isActive)}>
            История дозагрузок
          </NavLink>
        </nav>
        <button
          type="button"
          onClick={() => {
            logout();
            navigate("/login");
          }}
          style={{
            background: "#334155",
            color: "#f8fafc",
            border: "none",
            padding: "8px 14px",
            borderRadius: 8,
            cursor: "pointer",
          }}
        >
          Выйти
        </button>
      </header>
      <main style={{ maxWidth: 1100, margin: "24px auto", padding: "0 16px" }}>{children}</main>
    </div>
  );
}

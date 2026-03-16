import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { MeResponse } from "../api/auth";

interface Props { user: MeResponse | null; onLogout: () => void; children: React.ReactNode; }

const NAV_ITEMS = [
  { to: "/", label: "Главная", icon: "⊞" },
  { to: "/vacancies", label: "Вакансии", icon: "💼" },
  { to: "/recommendations", label: "Рекомендации", icon: "✦" },
  { to: "/assessments", label: "Задания", icon: "📋" },
];

export default function Layout({ user, onLogout, children }: Props) {
  const navigate = useNavigate();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  function handleLogout() { onLogout(); navigate("/login"); }

  const displayName = user?.full_name ?? user?.email?.split("@")[0] ?? "Профиль";
  const initials = (() => {
    const parts = displayName.trim().split(/\s+/);
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : parts[0].slice(0, 2).toUpperCase();
  })();

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: "var(--bg, #F8FAFC)", fontFamily: "var(--font, system-ui, sans-serif)" }}>

      {/* ── Top Navigation ───────────────────────────────────────────────── */}
      <header className="top-nav">
        <div style={{ maxWidth: 1200, margin: "0 auto", width: "100%", padding: "0 32px", display: "flex", alignItems: "center", gap: 0 }}>

          {/* Logo */}
          <NavLink to="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", marginRight: 32, flexShrink: 0 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, overflow: "hidden", flexShrink: 0 }}>
              <img src="/pictures/hr-avatar-career-assistant.webp" alt="Career Navigator" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
            </div>
            <span style={{ fontSize: 15, fontWeight: 700, color: "#0F172A", letterSpacing: "-0.3px" }}>Career Navigator</span>
          </NavLink>

          {/* Nav links */}
          <nav style={{ display: "flex", gap: 2, flex: 1 }}>
            {NAV_ITEMS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
              >
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Right side */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
            <NavLink
              to="/profile"
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              Профиль
            </NavLink>

            {/* User avatar / menu */}
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setUserMenuOpen(v => !v)}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "6px 10px 6px 6px",
                  background: userMenuOpen ? "#F1F5F9" : "transparent",
                  border: "1.5px solid",
                  borderColor: userMenuOpen ? "#CBD5E1" : "#E2E8F0",
                  borderRadius: 10,
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
                onMouseEnter={e => { if (!userMenuOpen) { e.currentTarget.style.background = "#F8FAFC"; } }}
                onMouseLeave={e => { if (!userMenuOpen) { e.currentTarget.style.background = "transparent"; } }}
              >
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "#3B5BDB", flexShrink: 0 }}>
                  {initials}
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: "#334155", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {displayName}
                </span>
                <span style={{ fontSize: 10, color: "#94A3B8", transition: "transform 0.15s", transform: userMenuOpen ? "rotate(180deg)" : "none", display: "inline-block" }}>▼</span>
              </button>

              {userMenuOpen && (
                <>
                  <div style={{ position: "fixed", inset: 0, zIndex: 49 }} onClick={() => setUserMenuOpen(false)} />
                  <div style={{
                    position: "absolute", top: "calc(100% + 8px)", right: 0,
                    background: "#fff", border: "1.5px solid #E2E8F0",
                    borderRadius: 14, boxShadow: "0 12px 40px rgba(15,23,42,0.12)",
                    minWidth: 200, zIndex: 50, overflow: "hidden",
                    padding: "6px",
                  }}>
                    <div style={{ padding: "10px 12px", borderBottom: "1px solid #F1F5F9", marginBottom: 4 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "#0F172A" }}>{user?.full_name}</div>
                      <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 1 }}>{user?.email}</div>
                    </div>
                    <NavLink to="/profile" onClick={() => setUserMenuOpen(false)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", color: "#334155", textDecoration: "none", borderRadius: 8, fontSize: 14, transition: "background 0.1s" }}
                      onMouseEnter={e => e.currentTarget.style.background = "#F8FAFC"}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      👤 Мой профиль
                    </NavLink>
                    <button onClick={handleLogout} style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "9px 12px", background: "transparent", border: "none", color: "#EF4444", cursor: "pointer", borderRadius: 8, fontSize: 14, textAlign: "left", transition: "background 0.1s" }}
                      onMouseEnter={e => e.currentTarget.style.background = "#FEF2F2"}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      ↩ Выйти
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main style={{ flex: 1, overflowY: "auto" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 32px" }}>
          {children}
        </div>
      </main>
    </div>
  );
}

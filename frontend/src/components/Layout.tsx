import React, { useState, useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { MeResponse } from "../api/auth";
import { getProfile } from "../api/profile";

interface Props { user: MeResponse | null; onLogout: () => void; children: React.ReactNode; }

const NAV_ITEMS = [
  { to: "/", label: "Главная" },
  { to: "/vacancies", label: "Вакансии" },
  { to: "/recommendations", label: "Рекомендации" },
  { to: "/assessments", label: "Задания" },
];

function IconUser({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function IconChevronDown({ size = 12 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

export default function Layout({ user, onLogout, children }: Props) {
  const navigate = useNavigate();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [profileFullName, setProfileFullName] = useState<string | null>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!user) {
      setProfileFullName(null);
      return;
    }
    getProfile()
      .then(p => setProfileFullName(p.full_name ?? null))
      .catch(() => setProfileFullName(null));
  }, [user?.user_id]);

  useEffect(() => {
    const onProfileUpdated = (event: Event) => {
      const fullName = (event as CustomEvent<{ full_name?: string | null }>).detail?.full_name;
      setProfileFullName(fullName ?? null);
    };
    window.addEventListener("profile-updated", onProfileUpdated);
    return () => window.removeEventListener("profile-updated", onProfileUpdated);
  }, []);

  function handleLogout() { onLogout(); navigate("/login"); }

  const displayName = profileFullName ?? user?.full_name ?? user?.email?.split("@")[0] ?? "Профиль";
  const initials = (() => {
    const parts = displayName.trim().split(/\s+/);
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : parts[0].slice(0, 2).toUpperCase();
  })();

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: "var(--bg-page, var(--bg, #F8FAFC))", fontFamily: "var(--font)" }}>

      <header className={`top-nav ${scrolled ? "scrolled" : ""}`}>
        <div style={{ maxWidth: 1360, margin: "0 auto", width: "100%", padding: "0 24px", display: "flex", alignItems: "center", gap: 0 }}>
          <NavLink to="/" style={{ display: "flex", alignItems: "center", gap: 12, textDecoration: "none", marginRight: 32, flexShrink: 0 }}>
            <div style={{ width: 48, height: 48, borderRadius: 10, overflow: "hidden", flexShrink: 0 }}>
              <img src="/pictures/cn-icon-on-white-bg.png" alt="Career Navigator" style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }} />
            </div>
            <span style={{ fontSize: 15, fontWeight: 700, color: "#0F172A", letterSpacing: "-0.3px" }}>Career Navigator</span>
          </NavLink>

          <nav style={{ display: "flex", gap: 10, flex: 1 }}>
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

          <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
            <NavLink
              to="/profile"
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              Профиль
            </NavLink>

            <div style={{ position: "relative" }}>
              <button
                type="button"
                onClick={() => setUserMenuOpen(v => !v)}
                aria-expanded={userMenuOpen}
                aria-haspopup="true"
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "6px 10px 6px 6px",
                  background: userMenuOpen ? "#F8FAFF" : "transparent",
                  border: "1.5px solid",
                  borderColor: userMenuOpen ? "#CBD5E1" : "#E2E8F0",
                  borderRadius: 10,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={e => { if (!userMenuOpen) e.currentTarget.style.background = "#F8FAFF"; }}
                onMouseLeave={e => { if (!userMenuOpen) e.currentTarget.style.background = "transparent"; }}
              >
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "#4338CA", flexShrink: 0 }}>
                  {initials}
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: "#334155", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {displayName}
                </span>
                <span style={{ transition: "transform 0.2s ease", transform: userMenuOpen ? "rotate(180deg)" : "none", display: "inline-flex", color: "#94A3B8" }}>
                  <IconChevronDown size={12} />
                </span>
              </button>

              {userMenuOpen && (
                <>
                  <div style={{ position: "fixed", inset: 0, zIndex: 49 }} onClick={() => setUserMenuOpen(false)} aria-hidden />
                  <div style={{
                    position: "absolute", top: "calc(100% + 8px)", right: 0,
                    background: "#fff", border: "1.5px solid #E2E8F0",
                    borderRadius: 14, boxShadow: "0 12px 40px rgba(15,23,42,0.12)",
                    minWidth: 200, zIndex: 50, overflow: "hidden",
                    padding: "6px",
                  }} role="menu">
                    <div style={{ padding: "10px 12px", borderBottom: "1px solid #F1F5F9", marginBottom: 4 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "#0F172A" }}>{displayName}</div>
                      <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 1 }}>{user?.email}</div>
                    </div>
                    <NavLink to="/profile" onClick={() => setUserMenuOpen(false)} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", color: "#334155", textDecoration: "none", borderRadius: 8, fontSize: 14, transition: "background 0.2s ease" }}
                      onMouseEnter={e => e.currentTarget.style.background = "#F8FAFF"}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <IconUser size={18} /> Мой профиль
                    </NavLink>
                    <button type="button" onClick={handleLogout} style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "9px 12px", background: "transparent", border: "none", color: "#EF4444", cursor: "pointer", borderRadius: 8, fontSize: 14, textAlign: "left", transition: "background 0.2s ease" }}
                      onMouseEnter={e => e.currentTarget.style.background = "#FEF2F2"}
                      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      Выйти
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main style={{ flex: 1, overflowY: "auto" }}>
        <div className="layout-content" style={{ maxWidth: 1360, margin: "0 auto", padding: "32px 32px 40px" }}>
          {children}
        </div>
      </main>
    </div>
  );
}

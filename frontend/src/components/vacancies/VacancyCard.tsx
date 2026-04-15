import React from "react";
import { Link } from "react-router-dom";
import { Vacancy, vacancySalaryCurrency } from "../../api/vacancies";
import { EXPERIENCE_LEVEL_LABEL } from "./vacanciesConstants";

export interface VacancyCardProps {
  vacancy: Vacancy;
  returnTo: string;
  variant?: "standard" | "tinted" | "accent-border";
  isLiked?: boolean;
  onToggleLike?: (vacancy: Vacancy) => void;
}

function IconHeart({ filled }: { filled: boolean }) {
  return (
    <svg width={20} height={20} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}

export function salaryString(v: Vacancy): string | null {
  if (!v.salary_from && !v.salary_to) return null;
  const parts = [v.salary_from, v.salary_to].filter(Boolean).map(n => n!.toLocaleString("ru-RU"));
  const c = vacancySalaryCurrency(v);
  const sym = c === "RUB" ? "₽" : c;
  return `${parts.join(" – ")} ${sym}`.trim();
}

const SENIORITY_STYLES: Record<string, { bg: string; color: string }> = {
  intern: { bg: "#F0FDFA", color: "#0D9488" },
  junior: { bg: "#ECFEFF", color: "#0E7490" },
  middle: { bg: "#EEF2FF", color: "#4338CA" },
  senior: { bg: "#FFF7E8", color: "#B45309" },
  lead: { bg: "#F5F3FF", color: "#6D28D9" },
};

function companyInitials(company: string): string {
  const words = company.trim().split(/[\s\-–—]+/).filter(Boolean);
  const firstLetter = (s: string) => {
    const match = s.match(/\p{L}/u);
    return match ? match[0].toUpperCase() : "";
  };
  if (words.length >= 2) {
    const a = firstLetter(words[0]);
    const b = firstLetter(words[1]);
    if (a && b) return a + b;
  }
  const letters = company.replace(/\P{L}/gu, "");
  return letters.slice(0, 2).toUpperCase() || company.slice(0, 2).toUpperCase();
}

function IconMapPin() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

function IconArrowRight() {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

export default function VacancyCard({ vacancy, returnTo, variant = "standard", isLiked = false, onToggleLike }: VacancyCardProps) {
  const salary = salaryString(vacancy);
  const seniorityLevels = vacancy.seniority
    ? vacancy.seniority.split(/\s*,\s*/).map(s => s.trim().toLowerCase()).filter(Boolean)
    : [];
  const experienceLabel = vacancy.experience_level
    ? EXPERIENCE_LEVEL_LABEL[vacancy.experience_level] ?? vacancy.experience_level
    : null;
  const getSeniorityStyle = (level: string) => SENIORITY_STYLES[level] ?? { bg: "#F8FAFF", color: "#475569" };
  const skills = vacancy.skills ?? [];
  const displaySkills = skills.slice(0, 4);
  const extraCount = skills.length > 4 ? skills.length - 4 : 0;

  const cardStyle: React.CSSProperties = {
    background: variant === "tinted" ? "#FFFFFF" : "#FFFFFF",
    border: "1px solid #E6EAF2",
    borderRadius: 24,
    padding: 22,
    minHeight: 260,
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05)",
    transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
    position: "relative",
    overflow: "hidden",
    textDecoration: "none",
    color: "inherit",
  };
  if (variant === "tinted") {
    cardStyle.background = "linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 100%)";
  }
  if (variant === "accent-border") {
    cardStyle.borderLeft = "4px solid #EEF2FF";
  }

  return (
    <Link
      to={`/vacancies/${vacancy.id}`}
      state={{ returnTo }}
      style={cardStyle}
      className="vacancy-card-link"
      onMouseEnter={e => {
        e.currentTarget.style.transform = "translateY(-4px)";
        e.currentTarget.style.boxShadow = "0 18px 32px rgba(91, 92, 235, 0.12)";
        e.currentTarget.style.borderColor = "#D9E2F2";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "0 10px 26px rgba(15, 23, 42, 0.05)";
        e.currentTarget.style.borderColor = variant === "accent-border" ? "#E6EAF2" : "#E6EAF2";
        if (variant === "accent-border") e.currentTarget.style.borderLeft = "4px solid #EEF2FF";
      }}
    >
      {onToggleLike && (
        <button
          type="button"
          onClick={e => {
            e.preventDefault();
            e.stopPropagation();
            onToggleLike(vacancy);
          }}
          aria-label={isLiked ? "Убрать из понравившихся" : "Добавить в понравившиеся"}
          style={{
            position: "absolute",
            top: 16,
            right: 16,
            zIndex: 2,
            width: 40,
            height: 40,
            borderRadius: 12,
            border: "none",
            background: "rgba(255,255,255,0.9)",
            color: isLiked ? "#E11D48" : "#94A3B8",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 8px rgba(15,23,42,0.08)",
            transition: "color 0.2s ease, background 0.2s ease",
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = "#E11D48";
            e.currentTarget.style.background = "#FFF1F2";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = isLiked ? "#E11D48" : "#94A3B8";
            e.currentTarget.style.background = "rgba(255,255,255,0.9)";
          }}
        >
          <IconHeart filled={isLiked} />
        </button>
      )}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: "50%",
              background: "#EEF2FF",
              color: "#4338CA",
              fontSize: 14,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            {companyInitials(vacancy.company)}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: "#4F46E5" }}>{vacancy.company}</div>
            {(seniorityLevels.length > 0 || experienceLabel) && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                {seniorityLevels.map(level => {
                  const style = getSeniorityStyle(level);
                  return (
                    <span
                      key={level}
                      style={{
                        display: "inline-block",
                        background: style.bg,
                        color: style.color,
                        fontSize: 12,
                        fontWeight: 600,
                        borderRadius: 999,
                        padding: "4px 10px",
                      }}
                    >
                      {level}
                    </span>
                  );
                })}
                {experienceLabel && (
                  <span
                    style={{
                      display: "inline-block",
                      background: "#F0FDF4",
                      color: "#166534",
                      fontSize: 12,
                      fontWeight: 600,
                      borderRadius: 999,
                      padding: "4px 10px",
                    }}
                  >
                    {experienceLabel}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
        <h3
          style={{
            fontSize: 18,
            fontWeight: 700,
            color: "#0F172A",
            margin: "0 0 10px",
            lineHeight: 1.35,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {vacancy.title}
        </h3>
        {vacancy.location && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#64748B", fontSize: 14, marginBottom: 8 }}>
            <IconMapPin />
            {vacancy.location}
          </div>
        )}
        {salary && (
          <div
            style={{
              display: "inline-block",
              background: "#EEF2FF",
              color: "#4338CA",
              borderRadius: 999,
              padding: "8px 12px",
              fontSize: 14,
              fontWeight: 700,
              marginBottom: 12,
            }}
          >
            {salary}
          </div>
        )}
      </div>
      <div>
        {displaySkills.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 14 }}>
            {displaySkills.map(s => (
              <span
                key={s}
                style={{
                  background: "#F8FAFF",
                  border: "1px solid #E6EAF2",
                  color: "#475569",
                  borderRadius: 999,
                  padding: "8px 10px",
                  fontSize: 13,
                }}
              >
                {s}
              </span>
            ))}
            {extraCount > 0 && (
              <span
                style={{
                  background: "#F8FAFF",
                  border: "1px solid #E6EAF2",
                  color: "#64748B",
                  borderRadius: 999,
                  padding: "8px 10px",
                  fontSize: 13,
                }}
              >
                +{extraCount}
              </span>
            )}
          </div>
        )}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#5B5CEB" }}>Подробнее</span>
          <IconArrowRight />
        </div>
      </div>
    </Link>
  );
}

export { SENIORITY_STYLES, companyInitials };

import { useNavigate } from "react-router-dom";
import { Vacancy } from "../../api/vacancies";
import { salaryString } from "./VacancyCard";

export interface FeaturedVacancyCardProps {
  vacancy: Vacancy;
  returnTo: string;
  isLiked?: boolean;
  onToggleLike?: (vacancy: Vacancy) => void;
}

function IconHeart({ filled }: { filled: boolean }) {
  return (
    <svg width={22} height={22} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}

function IconArrowRight() {
  return (
    <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

export default function FeaturedVacancyCard({ vacancy, returnTo, isLiked = false, onToggleLike }: FeaturedVacancyCardProps) {
  const navigate = useNavigate();
  const salary = salaryString(vacancy);
  const skills = vacancy.skills ?? [];
  const displaySkills = skills.slice(0, 5);

  return (
    <div
      className="featured-vacancy-card"
      style={{
        background: "linear-gradient(135deg, #FFFFFF 0%, #F8FAFF 100%)",
        border: "1px solid #E6EAF2",
        borderRadius: 28,
        padding: 28,
        boxShadow: "0 18px 36px rgba(15, 23, 42, 0.05)",
        display: "grid",
        gridTemplateColumns: "1.3fr 0.7fr",
        gap: 24,
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -30,
          right: -30,
          width: 180,
          height: 180,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(91,92,235,0.12) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div style={{ position: "relative", zIndex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
          <span
            style={{
              background: "#EEF2FF",
              color: "#4338CA",
              border: "1px solid #C7D2FE",
              borderRadius: 999,
              padding: "6px 12px",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            {vacancy.company}
          </span>
          <span
            style={{
              background: "#ECFDF5",
              color: "#047857",
              border: "1px solid #A7F3D0",
              borderRadius: 999,
              padding: "6px 12px",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            Подходит вам
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 14 }}>
          <h2
            style={{
              fontSize: 26,
              fontWeight: 700,
              lineHeight: 1.3,
              color: "#0F172A",
              margin: 0,
              letterSpacing: "-0.02em",
              flex: 1,
              minWidth: 0,
            }}
          >
            {vacancy.title}
          </h2>
          {onToggleLike && (
            <button
              type="button"
              onClick={() => onToggleLike(vacancy)}
              aria-label={isLiked ? "Убрать из понравившихся" : "Добавить в понравившиеся"}
              style={{
                flexShrink: 0,
                width: 44,
                height: 44,
                borderRadius: 14,
                border: "1px solid #E6EAF2",
                background: isLiked ? "#FFF1F2" : "#FFFFFF",
                color: isLiked ? "#E11D48" : "#94A3B8",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "color 0.2s ease, background 0.2s ease",
              }}
              onMouseEnter={e => {
                e.currentTarget.style.color = "#E11D48";
                e.currentTarget.style.background = "#FFF1F2";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.color = isLiked ? "#E11D48" : "#94A3B8";
                e.currentTarget.style.background = isLiked ? "#FFF1F2" : "#FFFFFF";
              }}
            >
              <IconHeart filled={isLiked} />
            </button>
          )}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 14, fontSize: 15, color: "#64748B" }}>
          <span>{vacancy.company}</span>
          {vacancy.location && <span>· {vacancy.location}</span>}
          {vacancy.employment_type?.length ? (
            <span>
              · {Array.isArray(vacancy.employment_type) ? vacancy.employment_type.join(", ") : vacancy.employment_type}
            </span>
          ) : null}
          {vacancy.seniority && <span>· {vacancy.seniority}</span>}
        </div>
        {salary && (
          <div
            style={{
              display: "inline-block",
              background: "#EEF2FF",
              color: "#4338CA",
              borderRadius: 999,
              padding: "10px 16px",
              fontSize: 16,
              fontWeight: 700,
              marginBottom: 16,
            }}
          >
            {salary}
          </div>
        )}
        {displaySkills.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
            {displaySkills.map(s => (
              <span
                key={s}
                style={{
                  background: "#F8FAFF",
                  border: "1px solid #E6EAF2",
                  color: "#475569",
                  borderRadius: 999,
                  padding: "8px 12px",
                  fontSize: 13,
                }}
              >
                {s}
              </span>
            ))}
          </div>
        )}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <button
            type="button"
            onClick={() => navigate(`/vacancies/${vacancy.id}`, { state: { returnTo } })}
            style={{
              background: "#5B5CEB",
              color: "#fff",
              border: "none",
              borderRadius: 16,
              padding: "14px 18px",
              fontSize: 15,
              fontWeight: 600,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              transition: "background 0.2s ease",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "#4F46E5")}
            onMouseLeave={e => (e.currentTarget.style.background = "#5B5CEB")}
          >
            Подробнее
            <IconArrowRight />
          </button>
          <button
            type="button"
            style={{
              background: "#FFFFFF",
              border: "1px solid #D8E0EE",
              color: "#0F172A",
              borderRadius: 16,
              padding: "14px 18px",
              fontSize: 15,
              fontWeight: 600,
              cursor: "pointer",
              transition: "background 0.2s ease, border-color 0.2s ease",
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = "#F8FAFF";
              e.currentTarget.style.borderColor = "#C7D2FE";
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = "#FFFFFF";
              e.currentTarget.style.borderColor = "#D8E0EE";
            }}
          >
            Сохранить
          </button>
        </div>
      </div>
      <div
        style={{
          position: "relative",
          zIndex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 700, color: "#0F172A", marginBottom: 4 }}>
          Почему стоит посмотреть
        </div>
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 10 }}>
          <li
            style={{
              background: "#F8FAFF",
              border: "1px solid #E6EAF2",
              borderRadius: 14,
              padding: "12px 14px",
              fontSize: 14,
              color: "#475569",
            }}
          >
            Подходит под ваш стек
          </li>
          <li
            style={{
              background: "#F8FAFF",
              border: "1px solid #E6EAF2",
              borderRadius: 14,
              padding: "12px 14px",
              fontSize: 14,
              color: "#475569",
            }}
          >
            {salary ? "Высокая зарплата" : "Актуальные требования"}
          </li>
          <li
            style={{
              background: "#F8FAFF",
              border: "1px solid #E6EAF2",
              borderRadius: 14,
              padding: "12px 14px",
              fontSize: 14,
              color: "#475569",
            }}
          >
            Популярный стек
          </li>
        </ul>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: "auto" }}>
          <span
            style={{
              background: "#EEF2FF",
              color: "#4338CA",
              borderRadius: 999,
              padding: "6px 12px",
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            {displaySkills.length} ключевых навыка
          </span>
          {vacancy.seniority && vacancy.seniority.split(/\s*,\s*/).filter(Boolean).map(level => (
            <span
              key={level}
              style={{
                background: "#F8FAFF",
                color: "#475569",
                borderRadius: 999,
                padding: "6px 12px",
                fontSize: 13,
                fontWeight: 500,
              }}
            >
              {level.trim()}
            </span>
          ))}
          {vacancy.location && (
            <span
              style={{
                background: "#F8FAFF",
                color: "#475569",
                borderRadius: 999,
                padding: "6px 12px",
                fontSize: 13,
                fontWeight: 500,
              }}
            >
              {vacancy.location}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

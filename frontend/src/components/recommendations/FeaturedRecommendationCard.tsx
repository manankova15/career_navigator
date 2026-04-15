import React from "react";
import { Link } from "react-router-dom";
import { Recommendation } from "../../api/recommendations";
import { Vacancy } from "../../api/vacancies";
import { matchPercent, matchChipTier } from "./recommendationUtils";
import { IconHeart, IconMapPin, IconArrowRight } from "./RecIcons";

interface Props {
  rec: Recommendation;
  vacancy: Vacancy;
  returnTo: string;
  isLiked: boolean;
  onToggleLike: (v: Vacancy) => void;
}

function topAccentGradient(percent: number): string {
  const t = matchChipTier(percent);
  if (t === "high") return "linear-gradient(90deg, #5B5CEB, #8B5CF6)";
  if (t === "mid") return "linear-gradient(90deg, #06B6D4, #67E8F9)";
  return "linear-gradient(90deg, #F59E0B, #FCD34D)";
}

function matchChipStyles(percent: number): React.CSSProperties {
  const t = matchChipTier(percent);
  if (t === "high") {
    return { background: "#EEF2FF", color: "#4338CA", border: "1px solid #C7D2FE" };
  }
  if (t === "mid") {
    return { background: "#ECFEFF", color: "#0E7490", border: "1px solid #A5F3FC" };
  }
  return { background: "#FFF7E8", color: "#B45309", border: "1px solid #FDE68A" };
}

export default function FeaturedRecommendationCard({ rec, vacancy, returnTo, isLiked, onToggleLike }: Props) {
  const pct = matchPercent(rec.score);
  const skills = vacancy.skills ?? [];
  const compactSkills = skills.slice(0, 3);

  return (
    <div
      style={{
        position: "relative",
        background: "linear-gradient(135deg, #FFFFFF 0%, #F8FAFF 100%)",
        border: "1px solid #E6EAF2",
        borderRadius: 24,
        padding: 22,
        boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05)",
        overflow: "hidden",
        minHeight: 200,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        aria-hidden
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: topAccentGradient(pct),
        }}
      />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 12 }}>
        <span
          style={{
            ...matchChipStyles(pct),
            borderRadius: 999,
            padding: "8px 12px",
            fontSize: 14,
            fontWeight: 700,
          }}
        >
          {pct}% match
        </span>
        <button
          type="button"
          onClick={e => {
            e.preventDefault();
            e.stopPropagation();
            onToggleLike(vacancy);
          }}
          aria-label={isLiked ? "Убрать из понравившихся" : "Добавить в понравившиеся"}
          style={{
            width: 40,
            height: 40,
            borderRadius: 14,
            border: isLiked ? "1px solid #FBCFE8" : "1px solid #E6EAF2",
            background: isLiked ? "#FFF1F2" : "#FFFFFF",
            color: isLiked ? "#E11D48" : "#94A3B8",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 8px rgba(15,23,42,0.06)",
            flexShrink: 0,
            transition: "background 0.2s ease, border-color 0.2s ease",
          }}
        >
          <IconHeart filled={isLiked} />
        </button>
      </div>

      <div style={{ fontSize: 14, fontWeight: 600, color: "#4F46E5", marginBottom: 6 }}>{vacancy.company}</div>
      <h3
        style={{
          fontSize: 20,
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
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#64748B", fontSize: 14, marginBottom: 12 }}>
          <IconMapPin />
          {vacancy.location}
        </div>
      )}

      {compactSkills.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
          {compactSkills.map(s => (
            <span
              key={s}
              style={{
                background: "#FFFFFF",
                border: "1px solid #E6EAF2",
                color: "#64748B",
                borderRadius: 999,
                padding: "6px 10px",
                fontSize: 12,
                fontWeight: 500,
              }}
            >
              {s}
            </span>
          ))}
        </div>
      )}

      <div style={{ marginTop: "auto", paddingTop: 8 }}>
        <Link
          to={`/vacancies/${vacancy.id}`}
          state={{ returnTo }}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            color: "#5B5CEB",
            fontWeight: 600,
            fontSize: 15,
            textDecoration: "none",
          }}
        >
          Подробнее
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 36,
              height: 36,
              borderRadius: "50%",
              background: "#F8FAFF",
              border: "1px solid #E6EAF2",
              color: "#5B5CEB",
            }}
          >
            <IconArrowRight size={18} />
          </span>
        </Link>
      </div>
    </div>
  );
}

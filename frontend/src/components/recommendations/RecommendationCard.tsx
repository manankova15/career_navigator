import React from "react";
import { Link } from "react-router-dom";
import { Recommendation } from "../../api/recommendations";
import { Vacancy } from "../../api/vacancies";
import {
  matchPercent,
  matchChipTier,
  matchProgressColor,
  matchAccentBorderColor,
} from "./recommendationUtils";
import { IconHeart, IconMapPin, IconArrowRight } from "./RecIcons";

export interface RecommendationCardProps {
  rec: Recommendation;
  vacancy: Vacancy;
  returnTo: string;
  gridIndex: number;
  isLiked: boolean;
  onToggleLike: (v: Vacancy) => void;
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

export default function RecommendationCard({
  rec,
  vacancy,
  returnTo,
  gridIndex,
  isLiked,
  onToggleLike,
}: RecommendationCardProps) {
  const pct = matchPercent(rec.score);
  const fillColor = matchProgressColor(pct);
  const nth3 = (gridIndex + 1) % 3 === 0;
  const nth5 = (gridIndex + 1) % 5 === 0;

  const cardBg = nth3 ? "linear-gradient(180deg, #F8FAFF 0%, #FFFFFF 28%)" : "#FFFFFF";
  const borderLeft = nth5 ? `3px solid ${matchAccentBorderColor(pct)}` : undefined;

  return (
    <Link
      to={`/vacancies/${vacancy.id}`}
      state={{ returnTo }}
      className="recommendation-card-link"
      style={{
        background: cardBg,
        border: "1px solid #E6EAF2",
        borderRadius: 24,
        padding: 20,
        minHeight: 230,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05)",
        transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
        position: "relative",
        overflow: "hidden",
        textDecoration: "none",
        color: "inherit",
        borderLeft: borderLeft ?? undefined,
        paddingLeft: nth5 ? 17 : 20,
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = "translateY(-4px)";
        e.currentTarget.style.boxShadow = "0 18px 32px rgba(91, 92, 235, 0.12)";
        e.currentTarget.style.borderColor = "#D9E2F2";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "0 10px 26px rgba(15, 23, 42, 0.05)";
        e.currentTarget.style.borderColor = "#E6EAF2";
      }}
    >
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
          borderRadius: 14,
          border: isLiked ? "1px solid #FBCFE8" : "1px solid #E6EAF2",
          background: isLiked ? "#FFF1F2" : "#FFFFFF",
          color: isLiked ? "#E11D48" : "#94A3B8",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 2px 8px rgba(15,23,42,0.06)",
          transition: "background 0.2s ease, border-color 0.2s ease, color 0.2s ease",
        }}
        onMouseEnter={e => {
          if (!isLiked) {
            e.currentTarget.style.background = "#F8FAFF";
          }
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = isLiked ? "#FFF1F2" : "#FFFFFF";
        }}
      >
        <IconHeart filled={isLiked} />
      </button>

      <div style={{ paddingRight: 48 }}>
        <span
          style={{
            ...matchChipStyles(pct),
            display: "inline-block",
            borderRadius: 999,
            padding: "8px 12px",
            fontSize: 14,
            fontWeight: 700,
            marginBottom: 14,
          }}
        >
          Совпадение {pct}%
        </span>

        <h3
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: "#0F172A",
            margin: "0 0 8px",
            lineHeight: 1.35,
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {vacancy.title}
        </h3>
        <div style={{ fontSize: 16, fontWeight: 500, color: "#4F46E5", marginBottom: 6 }}>{vacancy.company}</div>
        {vacancy.location && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#64748B", fontSize: 14, fontWeight: 500 }}>
            <IconMapPin size={14} />
            {vacancy.location}
          </div>
        )}

        <div style={{ marginTop: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Совпадение с вашим профилем
            </span>
            <span style={{ fontSize: 14, fontWeight: 700, color: "#0F172A" }}>{pct}%</span>
          </div>
          <div style={{ background: "#E9EEF7", borderRadius: 999, height: 8, overflow: "hidden" }}>
            <div
              style={{
                width: `${Math.min(100, pct)}%`,
                height: "100%",
                borderRadius: 999,
                background: fillColor,
                transition: "width 0.35s ease",
              }}
            />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 18, gap: 10 }}>
        <span style={{ fontSize: 16, fontWeight: 600, color: "#5B5CEB" }}>Подробнее</span>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            background: "#F8FAFF",
            border: "1px solid #E6EAF2",
            borderRadius: 999,
            padding: "8px 12px",
            fontSize: 13,
            fontWeight: 600,
            color: "#475569",
          }}
        >
          Открыть
          <IconArrowRight size={14} />
        </span>
      </div>
    </Link>
  );
}

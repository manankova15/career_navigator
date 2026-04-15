import React from "react";
import { Recommendation } from "../../api/recommendations";
import { Vacancy } from "../../api/vacancies";
import FeaturedRecommendationCard from "./FeaturedRecommendationCard";

interface Props {
  items: { rec: Recommendation; vacancy: Vacancy }[];
  returnTo: string;
  isLiked: (id: string) => boolean;
  onToggleLike: (v: Vacancy) => void;
}

export default function TopMatchesStrip({ items, returnTo, isLiked, onToggleLike }: Props) {
  if (items.length === 0) return null;

  return (
    <section style={{ marginTop: 24 }}>
      <div style={{ marginBottom: 18 }}>
        <h2
          style={{
            fontSize: 30,
            fontWeight: 700,
            lineHeight: "36px",
            color: "#0F172A",
            margin: "0 0 8px",
            letterSpacing: "-0.3px",
          }}
        >
          Лучшие совпадения
        </h2>
        <p style={{ fontSize: 18, fontWeight: 400, lineHeight: "28px", color: "#64748B", margin: 0 }}>
          Вакансии, которые ближе всего к вашему текущему профилю
        </p>
      </div>
      <div
        className={`recommendations-featured-strip recommendations-featured-strip--${Math.min(items.length, 3)}`}
        style={{
          display: "grid",
          gap: 20,
        }}
      >
        {items.map(({ rec, vacancy }) => (
          <FeaturedRecommendationCard
            key={rec.id}
            rec={rec}
            vacancy={vacancy}
            returnTo={returnTo}
            isLiked={isLiked(String(vacancy.id))}
            onToggleLike={onToggleLike}
          />
        ))}
      </div>
    </section>
  );
}

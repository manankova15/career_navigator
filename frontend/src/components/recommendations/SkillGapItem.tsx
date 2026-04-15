import React from "react";
import { SkillGap } from "../../api/recommendations";
import { IconBookOpen, IconExternalLink } from "./RecIcons";

interface Props {
  gap: SkillGap;
  barWidthPercent: number;
  fillColor: string;
  index: number;
}

function isUrl(s: string): boolean {
  return /^https?:\/\//i.test(s.trim());
}

export default function SkillGapItem({ gap, barWidthPercent, fillColor, index }: Props) {
  const resources = gap.recommended_resources ?? [];

  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E6EAF2",
        borderRadius: 20,
        padding: 18,
        marginBottom: 14,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 12 }}>
        <span style={{ fontSize: 16, fontWeight: 700, color: "#0F172A" }}>{gap.skill_name}</span>
        <span
          style={{
            flexShrink: 0,
            background: "#EEF2FF",
            color: "#4338CA",
            border: "1px solid #C7D2FE",
            borderRadius: 999,
            padding: "6px 10px",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          {gap.frequency} вакансий
        </span>
      </div>
      <div style={{ background: "#E9EEF7", borderRadius: 999, height: 8, overflow: "hidden", marginBottom: 12 }}>
        <div
          style={{
            width: `${barWidthPercent}%`,
            height: "100%",
            borderRadius: 999,
            background: fillColor,
            transition: "width 0.35s ease",
          }}
        />
      </div>
      {resources.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {resources.slice(0, 2).map((r, i) => (
            <div
              key={`${index}-${i}`}
              style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 14, lineHeight: "22px" }}
            >
              {isUrl(r) ? <IconExternalLink size={14} /> : <IconBookOpen size={14} />}
              {isUrl(r) ? (
                <a href={r} target="_blank" rel="noopener noreferrer" style={{ color: "#4F46E5", fontWeight: 500, textDecoration: "none" }}>
                  {r}
                </a>
              ) : (
                <span style={{ color: "#64748B" }}>{r}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

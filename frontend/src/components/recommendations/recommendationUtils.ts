import { Recommendation } from "../../api/recommendations";
import { Vacancy } from "../../api/vacancies";

/** Backend score is 0–1; defensively handle already-percent values */
export function matchPercent(score: number): number {
  if (Number.isNaN(score)) return 0;
  if (score > 1) return Math.min(100, Math.round(score));
  return Math.round(score * 100);
}

export function matchChipTier(percent: number): "high" | "mid" | "low" {
  if (percent >= 50) return "high";
  if (percent >= 45) return "mid";
  return "low";
}

export function matchProgressColor(percent: number): string {
  const t = matchChipTier(percent);
  if (t === "high") return "#5B5CEB";
  if (t === "mid") return "#06B6D4";
  return "#F59E0B";
}

export function matchAccentBorderColor(percent: number): string {
  return matchProgressColor(percent);
}

export type QuickRecFilter =
  | "all"
  | "best_match"
  | "python"
  | "backend"
  | "remote"
  | "high_match";

export function filterRecommendations(
  recs: Recommendation[],
  vacancyMap: Map<string, Vacancy>,
  filter: QuickRecFilter,
): Recommendation[] {
  if (filter === "all") return recs;

  const textBlob = (r: Recommendation): string => {
    const v = vacancyMap.get(String(r.vacancy_id));
    const reasonsExtra = (r as unknown as { reasons?: unknown }).reasons;
    const reasonsArr = Array.isArray(reasonsExtra) ? reasonsExtra.map(String) : [];
    const parts = [
      v?.title,
      v?.company,
      v?.location,
      ...(v?.skills ?? []),
      r.reason,
      ...reasonsArr,
    ];
    return parts.filter(Boolean).join(" ").toLowerCase();
  };

  return recs.filter(r => {
    const blob = textBlob(r);
    const pct = matchPercent(r.score);
    switch (filter) {
      case "best_match":
        return pct >= 65;
      case "high_match":
        return pct >= 50;
      case "python":
        return blob.includes("python") || blob.includes("питон");
      case "backend":
        return blob.includes("backend") || blob.includes("бэкенд") || blob.includes("back-end");
      case "remote":
        return (
          blob.includes("удален") ||
          blob.includes("удалённ") ||
          blob.includes("remote") ||
          blob.includes("дистанц") ||
          blob.includes("hybrid") ||
          blob.includes("гибрид")
        );
      default:
        return true;
    }
  });
}

export function sortByMatchDesc(recs: Recommendation[]): Recommendation[] {
  return [...recs].sort((a, b) => b.score - a.score);
}

/** Preserve API feed order for items that remain after filtering */
export function orderAsInFeed(source: Recommendation[], subset: Recommendation[]): Recommendation[] {
  const order = new Map(source.map((r, i) => [r.id, i]));
  return [...subset].sort((a, b) => (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0));
}

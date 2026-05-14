import React from "react";
import { QuickRecFilter } from "./recommendationUtils";
import { IconRefreshCw } from "./RecIcons";

export type RecSortMode = "match" | "feed";

interface Props {
  activeFilter?: QuickRecFilter;
  onFilterChange?: (f: QuickRecFilter) => void;
  sortMode?: RecSortMode;
  onSortModeChange?: (m: RecSortMode) => void;
  onRefresh: () => void;
  refreshing: boolean;
  loading: boolean;
  disabled?: boolean;
}

export default function RecommendationsToolbar({
  onRefresh,
  refreshing,
  loading,
  disabled,
}: Props) {
  return (
    <div
      className="recommendations-toolbar"
      style={{
        marginTop: -24,
        position: "relative",
        zIndex: 3,
        background: "rgba(255,255,255,0.96)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        border: "1px solid rgba(230,234,242,0.95)",
        borderRadius: 24,
        padding: "18px 20px",
        boxShadow: "0 16px 32px rgba(15, 23, 42, 0.06)",
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16,
      }}
    >
      <div className="recommendations-toolbar-actions" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12, marginLeft: "auto" }}>
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing || loading || disabled}
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
            background: refreshing || loading ? "#EEF2FF" : "#5B5CEB",
            color: refreshing || loading ? "#94A3B8" : "#fff",
            border: "none",
            borderRadius: 18,
            height: 48,
            padding: "0 18px",
            fontSize: 15,
            fontWeight: 600,
            cursor: refreshing || loading ? "not-allowed" : "pointer",
            boxShadow: refreshing || loading ? "none" : "0 8px 20px rgba(91, 92, 235, 0.25)",
            transition: "background 0.2s ease, box-shadow 0.2s ease",
          }}
          onMouseEnter={e => {
            if (refreshing || loading || disabled) return;
            e.currentTarget.style.background = "#4F46E5";
          }}
          onMouseLeave={e => {
            if (refreshing || loading) return;
            e.currentTarget.style.background = "#5B5CEB";
          }}
        >
          <IconRefreshCw size={18} />
          {refreshing ? "Обновляем…" : "Обновить"}
        </button>
      </div>
    </div>
  );
}

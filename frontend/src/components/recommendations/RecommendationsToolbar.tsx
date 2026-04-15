import React from "react";
import { QuickRecFilter } from "./recommendationUtils";
import { IconRefreshCw } from "./RecIcons";

const PILLS: { id: QuickRecFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "best_match", label: "Лучшее совпадение" },
  { id: "python", label: "Python" },
  { id: "backend", label: "Backend" },
  { id: "remote", label: "Удаленно" },
  { id: "high_match", label: "Высокий match" },
];

export type RecSortMode = "match" | "feed";

interface Props {
  activeFilter: QuickRecFilter;
  onFilterChange: (f: QuickRecFilter) => void;
  sortMode: RecSortMode;
  onSortModeChange: (m: RecSortMode) => void;
  onRefresh: () => void;
  refreshing: boolean;
  loading: boolean;
  disabled?: boolean;
}

export default function RecommendationsToolbar({
  activeFilter,
  onFilterChange,
  sortMode,
  onSortModeChange,
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
      <div className="recommendations-toolbar-pills" style={{ display: "flex", flexWrap: "wrap", gap: 8, flex: 1, minWidth: 200 }}>
        {PILLS.map(p => {
          const active = activeFilter === p.id;
          return (
            <button
              key={p.id}
              type="button"
              disabled={disabled}
              onClick={() => onFilterChange(p.id)}
              style={{
                background: active ? "#EEF2FF" : "#FFFFFF",
                border: `1px solid ${active ? "#C7D2FE" : "#E6EAF2"}`,
                color: active ? "#4338CA" : "#475569",
                borderRadius: 999,
                padding: "10px 14px",
                fontSize: 14,
                fontWeight: 600,
                cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.5 : 1,
                transition: "background 0.2s ease, border-color 0.2s ease, color 0.2s ease",
              }}
              onMouseEnter={e => {
                if (disabled || active) return;
                e.currentTarget.style.background = "#F8FAFF";
              }}
              onMouseLeave={e => {
                if (active) return;
                e.currentTarget.style.background = "#FFFFFF";
              }}
            >
              {p.label}
            </button>
          );
        })}
      </div>

      <div className="recommendations-toolbar-actions" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12 }}>
        <label
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            background: "#FFFFFF",
            border: "1px solid #E6EAF2",
            borderRadius: 16,
            height: 44,
            padding: "0 14px",
            fontSize: 14,
            fontWeight: 500,
            color: "#475569",
          }}
        >
          <span style={{ color: "#94A3B8", whiteSpace: "nowrap" }}>Сортировка:</span>
          <select
            disabled={disabled}
            value={sortMode}
            aria-label="Сортировка рекомендаций"
            onChange={e => onSortModeChange(e.target.value as RecSortMode)}
            style={{
              border: "none",
              background: "transparent",
              fontSize: 14,
              fontWeight: 600,
              color: "#0F172A",
              cursor: disabled ? "not-allowed" : "pointer",
              paddingRight: 4,
              outline: "none",
            }}
          >
            <option value="match">по совпадению</option>
            <option value="feed">как в ленте</option>
          </select>
        </label>

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

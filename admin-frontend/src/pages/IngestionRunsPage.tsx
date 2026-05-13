import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  deleteIngestionRun,
  listIngestionRuns,
  type IngestionRun,
} from "../api/ingestion";
import AdminLayout from "../components/AdminLayout";

const STATUS_COLORS: Record<string, string> = {
  success: "#15803d",
  skipped: "#b45309",
  failed: "#b91c1c",
  running: "#2563eb",
  pending: "#64748b",
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("ru-RU");
  } catch {
    return iso;
  }
}

function formatDuration(start: string, finish: string | null): string {
  if (!finish) return "—";
  const ms = new Date(finish).getTime() - new Date(start).getTime();
  if (Number.isNaN(ms) || ms < 0) return "—";
  if (ms < 1000) return `${ms} мс`;
  const sec = Math.round(ms / 1000);
  if (sec < 60) return `${sec} с`;
  const min = Math.floor(sec / 60);
  return `${min} мин ${sec % 60} с`;
}

export default function IngestionRunsPage() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<IngestionRun[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(30);
  const [statusFilter, setStatusFilter] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState("");

  const load = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const resp = await listIngestionRuns(page, pageSize, {
        status: statusFilter || undefined,
      });
      setRuns(resp.items);
      setTotal(resp.total);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter]);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      navigate("/login");
      return;
    }
    void load();
  }, [load, navigate]);

  async function removeRun(id: string) {
    if (!window.confirm("Удалить запись о запуске?")) return;
    setErr("");
    setInfo("");
    try {
      await deleteIngestionRun(id);
      setInfo("Запись удалена.");
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка удаления");
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <AdminLayout>
      <h1 style={{ fontSize: 22, marginBottom: 12 }}>История запусков дозагрузки</h1>
      <p style={{ fontSize: 14, color: "#64748b", marginBottom: 16 }}>
        Здесь отображаются все запуски: ручные и фоновые (по расписанию). Записи о Telegram-источниках без
        активной сессии помечаются статусом «skipped».
      </p>

      {err ? <p style={{ color: "#b91c1c", marginBottom: 12 }}>{err}</p> : null}
      {info ? <p style={{ color: "#15803d", marginBottom: 12 }}>{info}</p> : null}

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
        <label style={{ fontSize: 13 }}>
          Статус:{" "}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            style={{ padding: 6, borderRadius: 6, border: "1px solid #cbd5e1" }}
          >
            <option value="">Все</option>
            <option value="success">success</option>
            <option value="failed">failed</option>
            <option value="skipped">skipped</option>
            <option value="running">running</option>
            <option value="pending">pending</option>
          </select>
        </label>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          style={{
            padding: "6px 14px",
            borderRadius: 6,
            border: "1px solid #cbd5e1",
            background: "#fff",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "…" : "Обновить"}
        </button>
        <div style={{ marginLeft: "auto", fontSize: 13, color: "#64748b" }}>
          Всего: {total}
        </div>
      </div>

      <div style={{ overflowX: "auto", border: "1px solid #e2e8f0", borderRadius: 8 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, background: "#fff" }}>
          <thead>
            <tr style={{ background: "#e2e8f0", textAlign: "left" }}>
              <th style={{ padding: 10 }}>Источник</th>
              <th style={{ padding: 10 }}>Тип</th>
              <th style={{ padding: 10 }}>Статус</th>
              <th style={{ padding: 10 }}>Добавлено</th>
              <th style={{ padding: 10 }}>Лимит</th>
              <th style={{ padding: 10 }}>Старт</th>
              <th style={{ padding: 10 }}>Длительность</th>
              <th style={{ padding: 10 }}>Причина / ошибка</th>
              <th style={{ padding: 10 }} />
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ padding: 16, textAlign: "center", color: "#94a3b8" }}>
                  Нет записей.
                </td>
              </tr>
            ) : (
              runs.map((r) => (
                <tr key={r.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: 10 }}>{r.source_name ?? "—"}</td>
                  <td style={{ padding: 10 }}>{r.source_type ?? "—"}</td>
                  <td style={{ padding: 10, color: STATUS_COLORS[r.status] ?? "#0f172a", fontWeight: 600 }}>
                    {r.status}
                  </td>
                  <td style={{ padding: 10 }}>{r.new_vacancies}</td>
                  <td style={{ padding: 10 }}>{r.max_vacancies ?? "—"}</td>
                  <td style={{ padding: 10, whiteSpace: "nowrap" }}>{formatDate(r.started_at)}</td>
                  <td style={{ padding: 10 }}>{formatDuration(r.started_at, r.finished_at)}</td>
                  <td style={{ padding: 10, maxWidth: 280, color: "#64748b" }}>
                    {r.error ?? r.reason ?? "—"}
                  </td>
                  <td style={{ padding: 10 }}>
                    <button
                      type="button"
                      onClick={() => void removeRun(r.id)}
                      style={{
                        padding: "4px 10px",
                        background: "#fee2e2",
                        color: "#b91c1c",
                        border: "1px solid #fecaca",
                        borderRadius: 6,
                        cursor: "pointer",
                        fontSize: 12,
                      }}
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 16, alignItems: "center" }}>
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          style={{ padding: "6px 12px", borderRadius: 6, border: "1px solid #cbd5e1", background: "#fff" }}
        >
          ←
        </button>
        <span style={{ fontSize: 13 }}>
          стр. {page} / {totalPages}
        </span>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => p + 1)}
          style={{ padding: "6px 12px", borderRadius: 6, border: "1px solid #cbd5e1", background: "#fff" }}
        >
          →
        </button>
      </div>
    </AdminLayout>
  );
}

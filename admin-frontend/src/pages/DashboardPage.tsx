import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import {
  getIngestionSchedule,
  updateIngestionSchedule,
  type IngestionSchedule,
} from "../api/ingestion";
import AdminLayout from "../components/AdminLayout";

type Stats = {
  total_users: number;
  completed_attempts: number;
  users_with_completed_attempts: number;
};

type SourceRow = {
  id: string;
  name: string;
  source_type: string;
  enabled: boolean;
};

type SyncTriggerResponse = {
  source_id: string;
  status: string;
  message: string;
  task_id?: string | null;
  max_vacancies?: number | null;
};

type SyncJobResult = {
  source_id?: string;
  source_name?: string;
  source_type?: string;
  status?: string;
  new_vacancies?: number;
  max_vacancies?: number;
  reason?: string | null;
  error?: string | null;
};

type SyncJobStatus = {
  task_id: string;
  state: string;
  ready: boolean;
  result?: SyncJobResult | null;
  error?: string | null;
};

type SyncJob = SyncJobStatus & {
  max_vacancies_requested?: number | null;
  started_at: number;
  finished_at?: number;
};

const POLL_INTERVAL_MS = 2500;

function formatDuration(ms: number): string {
  const sec = Math.round(ms / 1000);
  if (sec < 60) return `${sec} с`;
  const min = Math.floor(sec / 60);
  const rest = sec % 60;
  return `${min} мин ${rest} с`;
}

function describeJob(job: SyncJob): { label: string; color: string; detail: string } {
  if (job.ready) {
    if (job.state === "SUCCESS") {
      const r = job.result ?? {};
      const added = typeof r.new_vacancies === "number" ? r.new_vacancies : 0;
      const cap = typeof r.max_vacancies === "number" ? r.max_vacancies : job.max_vacancies_requested ?? undefined;
      const status = r.status ?? "success";
      if (status === "skipped") {
        return {
          label: "Пропущено",
          color: "#b45309",
          detail: r.reason ? `причина: ${r.reason}` : "нет адаптера для этого источника",
        };
      }
      if (status === "failed") {
        return {
          label: "Ошибка",
          color: "#b91c1c",
          detail: r.error ?? "неизвестная ошибка",
        };
      }
      const duration = job.finished_at && job.started_at ? ` за ${formatDuration(job.finished_at - job.started_at)}` : "";
      const capPart = cap ? `, лимит ${cap}` : "";
      return {
        label: "Готово",
        color: "#15803d",
        detail: `добавлено ${added}${capPart}${duration}`,
      };
    }
    return {
      label: "Ошибка",
      color: "#b91c1c",
      detail: job.error ?? `состояние ${job.state}`,
    };
  }

  const runningFor = formatDuration(Date.now() - job.started_at);
  switch (job.state) {
    case "PENDING":
      return { label: "В очереди", color: "#64748b", detail: `ждёт воркер · ${runningFor}` };
    case "RECEIVED":
    case "STARTED":
      return { label: "Выполняется", color: "#2563eb", detail: `worker обрабатывает · ${runningFor}` };
    case "RETRY":
      return { label: "Повтор", color: "#b45309", detail: `повторная попытка · ${runningFor}` };
    default:
      return { label: job.state || "В работе", color: "#2563eb", detail: runningFor };
  }
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [err, setErr] = useState("");
  const [info, setInfo] = useState("");
  const [syncing, setSyncing] = useState<string | null>(null);
  const [maxVacanciesInput, setMaxVacanciesInput] = useState("200");
  const [jobs, setJobs] = useState<Record<string, SyncJob>>({});
  const [, setTick] = useState(0);
  const jobsRef = useRef(jobs);
  jobsRef.current = jobs;

  const [schedule, setSchedule] = useState<IngestionSchedule | null>(null);
  const [fetchHoursInput, setFetchHoursInput] = useState("");
  const [normalizeMinInput, setNormalizeMinInput] = useState("");
  const [savingSchedule, setSavingSchedule] = useState(false);

  const load = useCallback(async () => {
    setErr("");
    try {
      const s = await api.get<Stats>("/admin/stats");
      setStats(s);
      const raw = await api.get<SourceRow[] | { items?: SourceRow[] }>("/admin/sources");
      setSources(Array.isArray(raw) ? raw : raw.items ?? []);
      try {
        const sch = await getIngestionSchedule();
        setSchedule(sch);
        setFetchHoursInput(String(sch.fetch_interval_hours));
        setNormalizeMinInput(String(sch.normalize_interval_minutes));
      } catch {
        /* schedule endpoint optional */
      }
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка загрузки");
    }
  }, []);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      navigate("/login");
      return;
    }
    void load();
  }, [load, navigate]);

  useEffect(() => {
    const interval = setInterval(async () => {
      const current = jobsRef.current;
      const activeEntries = Object.entries(current).filter(([, j]) => !j.ready);
      if (activeEntries.length === 0) {
        setTick((t) => t + 1);
        return;
      }

      const updated: Record<string, SyncJob> = {};
      await Promise.all(
        activeEntries.map(async ([sourceId, job]) => {
          try {
            const statusResp = await api.get<SyncJobStatus>(`/admin/sources/sync/jobs/${job.task_id}`);
            updated[sourceId] = {
              ...job,
              ...statusResp,
              finished_at: statusResp.ready ? Date.now() : job.finished_at,
            };
          } catch (e) {
            updated[sourceId] = {
              ...job,
              ready: true,
              state: "FAILURE",
              error: e instanceof Error ? e.message : "Не удалось получить статус",
              finished_at: Date.now(),
            };
          }
        }),
      );

      if (Object.keys(updated).length > 0) {
        setJobs((prev) => ({ ...prev, ...updated }));
      } else {
        setTick((t) => t + 1);
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, []);

  async function triggerSync(sourceId: string) {
    setSyncing(sourceId);
    setErr("");
    try {
      const trimmed = maxVacanciesInput.trim();
      let requestedMax: number | null = null;
      const body =
        trimmed === ""
          ? {}
          : (() => {
              const n = Number.parseInt(trimmed, 10);
              if (Number.isNaN(n) || n < 1 || n > 5000) {
                throw new Error("Лимит вакансий: число от 1 до 5000 или пусто для значения по умолчанию.");
              }
              requestedMax = n;
              return { max_vacancies: n };
            })();
      const resp = await api.post<SyncTriggerResponse>(`/admin/sources/${sourceId}/sync`, body);
      if (!resp?.task_id) {
        throw new Error("Сервис не вернул task_id — обновите admin-service/source-service до последней версии.");
      }
      const newJob: SyncJob = {
        task_id: resp.task_id,
        state: "PENDING",
        ready: false,
        max_vacancies_requested: requestedMax ?? resp.max_vacancies ?? null,
        started_at: Date.now(),
      };
      setJobs((prev) => ({ ...prev, [sourceId]: newJob }));
      setInfo(`Задача дозагрузки поставлена в очередь (task_id=${resp.task_id}).`);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка sync");
    } finally {
      setSyncing(null);
    }
  }

  async function saveSchedule(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setInfo("");
    setSavingSchedule(true);
    try {
      const fh = Number.parseInt(fetchHoursInput, 10);
      const nm = Number.parseInt(normalizeMinInput, 10);
      if (Number.isNaN(fh) || fh < 1 || fh > 168) {
        throw new Error("Частота дозагрузки: целое число часов от 1 до 168.");
      }
      if (Number.isNaN(nm) || nm < 5 || nm > 1440) {
        throw new Error("Период нормализации: целое число минут от 5 до 1440.");
      }
      const result = await updateIngestionSchedule({
        fetch_interval_hours: fh,
        normalize_interval_minutes: nm,
      });
      setSchedule(result);
      setInfo("Расписание обновлено. Для применения требуется перезапуск celery-beat.");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка сохранения расписания");
    } finally {
      setSavingSchedule(false);
    }
  }

  return (
    <AdminLayout>
      {err ? <p style={{ color: "#b91c1c", marginBottom: 16 }}>{err}</p> : null}
      {info ? <p style={{ color: "#15803d", marginBottom: 16 }}>{info}</p> : null}

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>Статистика</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))", gap: 12 }}>
          <StatCard label="Всего пользователей" value={stats?.total_users ?? "—"} />
          <StatCard label="Завершённых прохождений тестов" value={stats?.completed_attempts ?? "—"} />
          <StatCard
            label="Пользователей с ≥1 завершённым тестом"
            value={stats?.users_with_completed_attempts ?? "—"}
          />
        </div>
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>Расписание автоматической дозагрузки</h2>
        {schedule ? (
          <form
            onSubmit={(e) => void saveSchedule(e)}
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 16,
              alignItems: "flex-end",
              padding: 16,
              background: "#fff",
              borderRadius: 8,
              border: "1px solid #e2e8f0",
            }}
          >
            <label style={{ display: "flex", flexDirection: "column", fontSize: 13 }}>
              Частота дозагрузки (часы)
              <input
                type="number"
                min={1}
                max={168}
                value={fetchHoursInput}
                onChange={(e) => setFetchHoursInput(e.target.value)}
                style={{ marginTop: 4, padding: 8, width: 120 }}
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", fontSize: 13 }}>
              Период нормализации (минуты)
              <input
                type="number"
                min={5}
                max={1440}
                value={normalizeMinInput}
                onChange={(e) => setNormalizeMinInput(e.target.value)}
                style={{ marginTop: 4, padding: 8, width: 120 }}
              />
            </label>
            <button
              type="submit"
              disabled={savingSchedule}
              style={{
                padding: "10px 16px",
                background: savingSchedule ? "#94a3b8" : "#0f766e",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                cursor: savingSchedule ? "not-allowed" : "pointer",
              }}
            >
              {savingSchedule ? "Сохранение…" : "Сохранить"}
            </button>
            <div style={{ flexBasis: "100%", fontSize: 12, color: "#64748b" }}>
              Сейчас: каждые {schedule.fetch_interval_hours} ч — дозагрузка, каждые{" "}
              {schedule.normalize_interval_minutes} мин — нормализация. Telegram-источники, у которых не настроена
              сессия, пропускаются автоматически (статус «skipped») и не считаются ошибкой.
            </div>
          </form>
        ) : (
          <p style={{ fontSize: 13, color: "#64748b" }}>Параметры расписания недоступны.</p>
        )}
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>Источники вакансий</h2>
        <label style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14, fontSize: 14 }}>
          <span style={{ color: "#334155" }}>Макс. новых вакансий за запуск</span>
          <input
            type="text"
            inputMode="numeric"
            placeholder="пусто = по умолчанию (worker)"
            value={maxVacanciesInput}
            onChange={(e) => setMaxVacanciesInput(e.target.value)}
            style={{ width: 120, padding: "6px 10px", borderRadius: 6, border: "1px solid #cbd5e1" }}
          />
          <span style={{ fontSize: 12, color: "#94a3b8" }}>1–5000</span>
        </label>
        <div style={{ overflowX: "auto", borderRadius: 8, border: "1px solid #e2e8f0" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14, background: "#fff" }}>
            <thead>
              <tr style={{ background: "#e2e8f0", textAlign: "left" }}>
                <th style={{ padding: 10 }}>Название</th>
                <th style={{ padding: 10 }}>Тип</th>
                <th style={{ padding: 10 }}>Вкл.</th>
                <th style={{ padding: 10 }}>Статус дозагрузки</th>
                <th style={{ padding: 10 }} />
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => {
                const job = jobs[s.id];
                const jinfo = job ? describeJob(job) : null;
                const active = Boolean(job && !job.ready);
                return (
                  <tr key={s.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                    <td style={{ padding: 10 }}>{s.name}</td>
                    <td style={{ padding: 10 }}>{s.source_type}</td>
                    <td style={{ padding: 10 }}>{s.enabled ? "да" : "нет"}</td>
                    <td style={{ padding: 10 }}>
                      {jinfo ? (
                        <div>
                          <div style={{ color: jinfo.color, fontWeight: 600 }}>{jinfo.label}</div>
                          <div style={{ fontSize: 12, color: "#64748b" }}>{jinfo.detail}</div>
                        </div>
                      ) : (
                        <span style={{ color: "#94a3b8" }}>—</span>
                      )}
                    </td>
                    <td style={{ padding: 10 }}>
                      <button
                        type="button"
                        disabled={!s.enabled || syncing === s.id || active}
                        onClick={() => void triggerSync(s.id)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: 6,
                          border: "none",
                          background: !s.enabled || active ? "#94a3b8" : "#2563eb",
                          color: "#fff",
                          cursor: !s.enabled || active ? "not-allowed" : "pointer",
                        }}
                      >
                        {syncing === s.id ? "…" : active ? "Выполняется…" : "Дозагрузить"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 13, color: "#64748b", marginTop: 10 }}>
          Полная история запусков (включая фоновые автоматические) доступна на странице{" "}
          <Link to="/ingestion-runs">«История дозагрузок»</Link>.
        </p>
      </section>

      <section>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>Тесты</h2>
        <p style={{ fontSize: 14, color: "#475569", marginBottom: 12 }}>
          Создание, редактирование и публикация тестов вынесены на отдельную страницу.
        </p>
        <Link
          to="/tests"
          style={{
            display: "inline-block",
            padding: "10px 16px",
            background: "#0f766e",
            color: "#fff",
            borderRadius: 8,
            textDecoration: "none",
            fontWeight: 600,
          }}
        >
          Перейти к управлению тестами →
        </Link>
      </section>
    </AdminLayout>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ padding: 16, background: "#fff", borderRadius: 8, border: "1px solid #e2e8f0" }}>
      <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { logout } from "../api/auth";

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
  const [syncing, setSyncing] = useState<string | null>(null);
  /** Пустая строка = лимит по умолчанию в worker (SYNC_DEFAULT_MAX_VACANCIES). */
  const [maxVacanciesInput, setMaxVacanciesInput] = useState("200");
  const [testTitle, setTestTitle] = useState("Новый тест");
  const [testTopic, setTestTopic] = useState("soft_skills");
  const [testMsg, setTestMsg] = useState("");
  const [jobs, setJobs] = useState<Record<string, SyncJob>>({});
  const [, setTick] = useState(0);
  const jobsRef = useRef(jobs);
  jobsRef.current = jobs;

  const load = useCallback(async () => {
    setErr("");
    try {
      const s = await api.get<Stats>("/admin/stats");
      setStats(s);
      const raw = await api.get<SourceRow[] | { items?: SourceRow[] }>("/admin/sources");
      setSources(Array.isArray(raw) ? raw : raw.items ?? []);
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

  // Периодически опрашиваем статус активных задач дозагрузки.
  useEffect(() => {
    const interval = setInterval(async () => {
      const current = jobsRef.current;
      const activeEntries = Object.entries(current).filter(([, j]) => !j.ready);
      if (activeEntries.length === 0) {
        // пересчитать UI, чтобы таймеры бегущих задач освежились (даже если их уже нет)
        setTick((t) => t + 1);
        return;
      }

      const updated: Record<string, SyncJob> = {};
      await Promise.all(
        activeEntries.map(async ([sourceId, job]) => {
          try {
            const status = await api.get<SyncJobStatus>(`/admin/sources/sync/jobs/${job.task_id}`);
            updated[sourceId] = {
              ...job,
              ...status,
              finished_at: status.ready ? Date.now() : job.finished_at,
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
      setTestMsg(`Задача дозагрузки поставлена в очередь (task_id=${resp.task_id}).`);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка sync");
    } finally {
      setSyncing(null);
    }
  }

  async function createMinimalTest(e: React.FormEvent) {
    e.preventDefault();
    setTestMsg("");
    setErr("");
    try {
      await api.post("/assessments", {
        title: testTitle,
        description: "Создано из админ-панели",
        topic: testTopic,
        difficulty: "medium",
        related_skills: [],
        is_published: false,
        items: [
          {
            position: 0,
            prompt: "Пример: выберите верный вариант.",
            mode: "quiz",
            options: [
              { id: "a", text: "Вариант А" },
              { id: "b", text: "Вариант Б" },
            ],
            correct_option_ids: ["a"],
            max_score: 1,
            related_skills: [],
          },
        ],
      });
      setTestMsg("Тест создан (черновик). Опубликуйте через PATCH или основной API.");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка создания теста");
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "system-ui, sans-serif" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 24px",
          background: "#0f172a",
          color: "#f8fafc",
        }}
      >
        <strong>Career Navigator — админ</strong>
        <button
          type="button"
          onClick={() => {
            logout();
            navigate("/login");
          }}
          style={{
            background: "#334155",
            color: "#f8fafc",
            border: "none",
            padding: "8px 14px",
            borderRadius: 8,
            cursor: "pointer",
          }}
        >
          Выйти
        </button>
      </header>

      <main style={{ maxWidth: 960, margin: "24px auto", padding: "0 16px" }}>
        {err ? (
          <p style={{ color: "#b91c1c", marginBottom: 16 }}>{err}</p>
        ) : null}
        {testMsg ? (
          <p style={{ color: "#15803d", marginBottom: 16 }}>{testMsg}</p>
        ) : null}

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
          <h2 style={{ fontSize: 18, marginBottom: 12 }}>Источники вакансий</h2>
          <p style={{ fontSize: 14, color: "#64748b", marginBottom: 12 }}>
            Дозагрузка: Celery <code>fetch_source</code>. Для <b>hh.ru</b> — новые записи в raw → normalize. Для{" "}
            <b>telegram</b> — Telethon + тот же парсер, что в <code>scripts/seed_telegram_vacancies.py</code>, запись
            напрямую в canonical (нужны <code>TELEGRAM_API_ID</code> / <code>TELEGRAM_API_HASH</code> и файл сессии в
            volume <code>tg-ingest-session</code>).
          </p>
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
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
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
                  const info = job ? describeJob(job) : null;
                  const active = Boolean(job && !job.ready);
                  return (
                    <tr key={s.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                      <td style={{ padding: 10 }}>{s.name}</td>
                      <td style={{ padding: 10 }}>{s.source_type}</td>
                      <td style={{ padding: 10 }}>{s.enabled ? "да" : "нет"}</td>
                      <td style={{ padding: 10 }}>
                        {info ? (
                          <div>
                            <div style={{ color: info.color, fontWeight: 600 }}>{info.label}</div>
                            <div style={{ fontSize: 12, color: "#64748b" }}>{info.detail}</div>
                            {job?.task_id ? (
                              <div style={{ fontSize: 11, color: "#94a3b8", fontFamily: "monospace" }}>
                                task_id: {job.task_id.slice(0, 8)}…
                              </div>
                            ) : null}
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
        </section>

        <section>
          <h2 style={{ fontSize: 18, marginBottom: 12 }}>Быстрое создание теста</h2>
          <p style={{ fontSize: 14, color: "#64748b", marginBottom: 12 }}>
            Создаётся черновик с одним вопросом-квизом; при необходимости дополните вопросы через API или
            расширьте форму.
          </p>
          <form
            onSubmit={(e) => void createMinimalTest(e)}
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 12,
              alignItems: "flex-end",
              padding: 16,
              background: "#fff",
              borderRadius: 8,
              border: "1px solid #e2e8f0",
            }}
          >
            <label style={{ display: "flex", flexDirection: "column", fontSize: 13 }}>
              Название
              <input
                value={testTitle}
                onChange={(e) => setTestTitle(e.target.value)}
                style={{ marginTop: 4, padding: 8, minWidth: 220 }}
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", fontSize: 13 }}>
              Тема (topic)
              <input
                value={testTopic}
                onChange={(e) => setTestTopic(e.target.value)}
                style={{ marginTop: 4, padding: 8, minWidth: 160 }}
              />
            </label>
            <button
              type="submit"
              style={{
                padding: "10px 16px",
                background: "#0f766e",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                cursor: "pointer",
              }}
            >
              Создать черновик
            </button>
          </form>
        </section>
      </main>
    </div>
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

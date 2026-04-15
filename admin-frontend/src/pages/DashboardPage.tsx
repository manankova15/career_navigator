import { useCallback, useEffect, useState } from "react";
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

  async function triggerSync(sourceId: string) {
    setSyncing(sourceId);
    setErr("");
    try {
      const trimmed = maxVacanciesInput.trim();
      const body =
        trimmed === ""
          ? {}
          : (() => {
              const n = Number.parseInt(trimmed, 10);
              if (Number.isNaN(n) || n < 1 || n > 5000) {
                throw new Error("Лимит вакансий: число от 1 до 5000 или пусто для значения по умолчанию.");
              }
              return { max_vacancies: n };
            })();
      await api.post(`/admin/sources/${sourceId}/sync`, body);
      setTestMsg("Задача дозагрузки поставлена в очередь (Celery).");
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
                  <th style={{ padding: 10 }} />
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                    <td style={{ padding: 10 }}>{s.name}</td>
                    <td style={{ padding: 10 }}>{s.source_type}</td>
                    <td style={{ padding: 10 }}>{s.enabled ? "да" : "нет"}</td>
                    <td style={{ padding: 10 }}>
                      <button
                        type="button"
                        disabled={!s.enabled || syncing === s.id}
                        onClick={() => void triggerSync(s.id)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: 6,
                          border: "none",
                          background: s.enabled ? "#2563eb" : "#94a3b8",
                          color: "#fff",
                          cursor: s.enabled ? "pointer" : "not-allowed",
                        }}
                      >
                        {syncing === s.id ? "…" : "Дозагрузить"}
                      </button>
                    </td>
                  </tr>
                ))}
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

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  deleteAssessment,
  listAssessments,
  publishAssessment,
  type Assessment,
} from "../api/assessments";
import AdminLayout from "../components/AdminLayout";

export default function AssessmentsListPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Assessment[]>([]);
  const [err, setErr] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const resp = await listAssessments(1, 100);
      setItems(resp.items);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      navigate("/login");
      return;
    }
    void load();
  }, [load, navigate]);

  async function togglePublish(item: Assessment) {
    setBusyId(item.id);
    setErr("");
    setInfo("");
    try {
      await publishAssessment(item.id, !item.is_published);
      setInfo(item.is_published ? "Тест снят с публикации." : "Тест опубликован.");
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка публикации");
    } finally {
      setBusyId(null);
    }
  }

  async function remove(item: Assessment) {
    if (!window.confirm(`Удалить тест «${item.title}» и все вопросы?`)) return;
    setBusyId(item.id);
    setErr("");
    setInfo("");
    try {
      await deleteAssessment(item.id);
      setInfo("Тест удалён.");
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Ошибка удаления");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AdminLayout>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>Тесты</h1>
        <Link
          to="/tests/new"
          style={{
            padding: "10px 16px",
            background: "#0f766e",
            color: "#fff",
            borderRadius: 8,
            textDecoration: "none",
            fontWeight: 600,
          }}
        >
          + Создать тест
        </Link>
      </div>

      {err ? <p style={{ color: "#b91c1c", marginBottom: 12 }}>{err}</p> : null}
      {info ? <p style={{ color: "#15803d", marginBottom: 12 }}>{info}</p> : null}

      <div style={{ overflowX: "auto", border: "1px solid #e2e8f0", borderRadius: 8 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14, background: "#fff" }}>
          <thead>
            <tr style={{ background: "#e2e8f0", textAlign: "left" }}>
              <th style={{ padding: 10 }}>Название</th>
              <th style={{ padding: 10 }}>Тема</th>
              <th style={{ padding: 10 }}>Сложность</th>
              <th style={{ padding: 10 }}>Вопросов</th>
              <th style={{ padding: 10 }}>Опубликован</th>
              <th style={{ padding: 10 }} />
            </tr>
          </thead>
          <tbody>
            {loading && items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: 16, textAlign: "center", color: "#94a3b8" }}>
                  Загрузка…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: 16, textAlign: "center", color: "#94a3b8" }}>
                  Тестов ещё нет. Создайте первый.
                </td>
              </tr>
            ) : (
              items.map((a) => (
                <tr key={a.id} style={{ borderTop: "1px solid #e2e8f0" }}>
                  <td style={{ padding: 10 }}>
                    <Link to={`/tests/${a.id}/edit`} style={{ color: "#0f766e", fontWeight: 600 }}>
                      {a.title}
                    </Link>
                    {a.description ? (
                      <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 2 }}>{a.description}</div>
                    ) : null}
                  </td>
                  <td style={{ padding: 10 }}>{a.topic}</td>
                  <td style={{ padding: 10 }}>{a.difficulty}</td>
                  <td style={{ padding: 10 }}>{a.item_count}</td>
                  <td style={{ padding: 10 }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: 12,
                        fontSize: 12,
                        fontWeight: 600,
                        background: a.is_published ? "#dcfce7" : "#fef3c7",
                        color: a.is_published ? "#15803d" : "#b45309",
                      }}
                    >
                      {a.is_published ? "опубликован" : "черновик"}
                    </span>
                  </td>
                  <td style={{ padding: 10, whiteSpace: "nowrap" }}>
                    <button
                      type="button"
                      disabled={busyId === a.id}
                      onClick={() => void togglePublish(a)}
                      style={{
                        marginRight: 6,
                        padding: "4px 10px",
                        background: a.is_published ? "#fde68a" : "#bbf7d0",
                        color: "#0f172a",
                        border: "none",
                        borderRadius: 6,
                        cursor: "pointer",
                        fontSize: 12,
                      }}
                    >
                      {a.is_published ? "Снять" : "Опубликовать"}
                    </button>
                    <Link
                      to={`/tests/${a.id}/edit`}
                      style={{
                        marginRight: 6,
                        padding: "4px 10px",
                        background: "#e0f2fe",
                        color: "#0369a1",
                        border: "none",
                        borderRadius: 6,
                        fontSize: 12,
                        textDecoration: "none",
                      }}
                    >
                      Редактировать
                    </Link>
                    <button
                      type="button"
                      disabled={busyId === a.id}
                      onClick={() => void remove(a)}
                      style={{
                        padding: "4px 10px",
                        background: "#fee2e2",
                        color: "#b91c1c",
                        border: "none",
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
    </AdminLayout>
  );
}

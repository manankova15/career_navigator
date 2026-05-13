import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import AdminLayout from "../components/AdminLayout";
import {
  Assessment,
  AssessmentItem,
  AssessmentItemPayload,
  AssessmentMode,
  Difficulty,
  Option,
  RubricCriterion,
  addAssessmentItem,
  createAssessment,
  deleteAssessmentItem,
  getAssessment,
  updateAssessment,
  updateAssessmentItem,
} from "../api/assessments";

type DraftItem = {
  // local-only id for React keys; absent for new items not yet saved
  localId: string;
  // server id; absent for new items not yet persisted
  serverId?: string;
  position: number;
  prompt: string;
  mode: AssessmentMode;
  options: Option[];
  correct_option_ids: string[];
  expected_keywords: string[];
  rubric_checklist: RubricCriterion[];
  max_score: number;
  related_skills: string[];
  explanation: string;
};

const MODE_LABELS: Record<AssessmentMode, string> = {
  quiz: "Один правильный ответ (quiz)",
  multi_select: "Несколько правильных (multi_select)",
  short_text: "Короткий текст (short_text)",
  case: "Кейс с рубрикой (case)",
};

const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  easy: "Лёгкий",
  medium: "Средний",
  hard: "Сложный",
};

function genLocalId() {
  return `local-${Math.random().toString(36).slice(2, 10)}-${Date.now().toString(36)}`;
}

function genOptionId() {
  return `opt-${Math.random().toString(36).slice(2, 8)}`;
}

function emptyItem(position: number): DraftItem {
  return {
    localId: genLocalId(),
    position,
    prompt: "",
    mode: "quiz",
    options: [
      { id: genOptionId(), text: "" },
      { id: genOptionId(), text: "" },
    ],
    correct_option_ids: [],
    expected_keywords: [],
    rubric_checklist: [],
    max_score: 1,
    related_skills: [],
    explanation: "",
  };
}

function itemFromServer(it: AssessmentItem): DraftItem {
  return {
    localId: genLocalId(),
    serverId: it.id,
    position: it.position,
    prompt: it.prompt,
    mode: it.mode,
    options: it.options?.length ? it.options : [],
    correct_option_ids: it.correct_option_ids || [],
    expected_keywords: it.expected_keywords || [],
    rubric_checklist: it.rubric_checklist || [],
    max_score: it.max_score ?? 1,
    related_skills: it.related_skills || [],
    explanation: it.explanation || "",
  };
}

function buildItemPayload(it: DraftItem): AssessmentItemPayload {
  const base: AssessmentItemPayload = {
    position: it.position,
    prompt: it.prompt,
    mode: it.mode,
    max_score: it.max_score,
    related_skills: it.related_skills,
    explanation: it.explanation || null,
  };
  if (it.mode === "quiz" || it.mode === "multi_select") {
    base.options = it.options.filter((o) => o.text.trim() !== "");
    base.correct_option_ids = it.correct_option_ids.filter((id) =>
      base.options!.some((o) => o.id === id),
    );
  } else if (it.mode === "short_text") {
    base.expected_keywords = it.expected_keywords.filter((k) => k.trim() !== "");
  } else if (it.mode === "case") {
    base.rubric_checklist = it.rubric_checklist.filter((c) => c.criterion.trim() !== "");
  }
  return base;
}

export default function AssessmentEditorPage() {
  const { id } = useParams<{ id?: string }>();
  const isEditing = Boolean(id);
  const navigate = useNavigate();

  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedFlash, setSavedFlash] = useState<string | null>(null);

  // Assessment-level fields
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState<Difficulty>("medium");
  const [relatedSkillsStr, setRelatedSkillsStr] = useState("");
  const [isPublished, setIsPublished] = useState(false);

  const [items, setItems] = useState<DraftItem[]>([]);
  // Items deleted in edit mode but still present on server; flushed on save
  const [pendingDeletes, setPendingDeletes] = useState<string[]>([]);
  // To distinguish "new" items in edit mode for proper API call
  const [originalItemIds, setOriginalItemIds] = useState<Set<string>>(new Set());

  const loadExisting = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAssessment(id);
      setTitle(data.title);
      setDescription(data.description || "");
      setTopic(data.topic);
      setDifficulty(data.difficulty);
      setRelatedSkillsStr((data.related_skills || []).join(", "));
      setIsPublished(data.is_published);
      const sorted = [...data.items].sort((a, b) => a.position - b.position);
      const drafts = sorted.map(itemFromServer);
      setItems(drafts);
      setOriginalItemIds(new Set(drafts.map((d) => d.serverId!).filter(Boolean)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить тест");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (isEditing) {
      void loadExisting();
    } else {
      setItems([emptyItem(1)]);
    }
  }, [isEditing, loadExisting]);

  // ----- Item helpers -----
  const updateItem = (localId: string, patch: Partial<DraftItem>) => {
    setItems((prev) => prev.map((it) => (it.localId === localId ? { ...it, ...patch } : it)));
  };

  const addItem = () => {
    setItems((prev) => [...prev, emptyItem(prev.length + 1)]);
  };

  const removeItem = (localId: string) => {
    setItems((prev) => {
      const target = prev.find((p) => p.localId === localId);
      if (target?.serverId && originalItemIds.has(target.serverId)) {
        setPendingDeletes((d) => [...d, target.serverId!]);
      }
      const filtered = prev.filter((p) => p.localId !== localId);
      // re-number positions
      return filtered.map((p, idx) => ({ ...p, position: idx + 1 }));
    });
  };

  const moveItem = (localId: string, dir: -1 | 1) => {
    setItems((prev) => {
      const idx = prev.findIndex((p) => p.localId === localId);
      const newIdx = idx + dir;
      if (idx < 0 || newIdx < 0 || newIdx >= prev.length) return prev;
      const copy = [...prev];
      [copy[idx], copy[newIdx]] = [copy[newIdx], copy[idx]];
      return copy.map((p, i) => ({ ...p, position: i + 1 }));
    });
  };

  const setOptionText = (localId: string, optionId: string, text: string) => {
    setItems((prev) =>
      prev.map((it) =>
        it.localId === localId
          ? {
              ...it,
              options: it.options.map((o) => (o.id === optionId ? { ...o, text } : o)),
            }
          : it,
      ),
    );
  };

  const addOption = (localId: string) => {
    setItems((prev) =>
      prev.map((it) =>
        it.localId === localId
          ? { ...it, options: [...it.options, { id: genOptionId(), text: "" }] }
          : it,
      ),
    );
  };

  const removeOption = (localId: string, optionId: string) => {
    setItems((prev) =>
      prev.map((it) =>
        it.localId === localId
          ? {
              ...it,
              options: it.options.filter((o) => o.id !== optionId),
              correct_option_ids: it.correct_option_ids.filter((cid) => cid !== optionId),
            }
          : it,
      ),
    );
  };

  const toggleCorrect = (localId: string, optionId: string) => {
    setItems((prev) =>
      prev.map((it) => {
        if (it.localId !== localId) return it;
        if (it.mode === "quiz") {
          return { ...it, correct_option_ids: [optionId] };
        }
        const exists = it.correct_option_ids.includes(optionId);
        return {
          ...it,
          correct_option_ids: exists
            ? it.correct_option_ids.filter((cid) => cid !== optionId)
            : [...it.correct_option_ids, optionId],
        };
      }),
    );
  };

  // ----- Save logic -----
  const buildCreatePayload = () => ({
    title: title.trim(),
    description: description.trim() || null,
    topic: topic.trim(),
    difficulty,
    related_skills: relatedSkillsStr
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    is_published: isPublished,
    items: items.map(buildItemPayload),
  });

  const validate = (): string | null => {
    if (!title.trim()) return "Введите название теста";
    if (!topic.trim()) return "Укажите тему теста";
    if (items.length === 0) return "Тест должен содержать хотя бы один вопрос";
    for (const [i, it] of items.entries()) {
      if (!it.prompt.trim()) return `Вопрос #${i + 1}: пустая формулировка`;
      if (it.mode === "quiz" || it.mode === "multi_select") {
        const opts = it.options.filter((o) => o.text.trim() !== "");
        if (opts.length < 2)
          return `Вопрос #${i + 1}: нужно минимум 2 варианта ответа`;
        const validIds = new Set(opts.map((o) => o.id));
        const correct = it.correct_option_ids.filter((cid) => validIds.has(cid));
        if (correct.length === 0)
          return `Вопрос #${i + 1}: отметьте правильный вариант`;
        if (it.mode === "quiz" && correct.length !== 1)
          return `Вопрос #${i + 1}: для режима quiz должен быть ровно один правильный ответ`;
      }
      if (it.mode === "short_text" && it.expected_keywords.filter((k) => k.trim()).length === 0) {
        return `Вопрос #${i + 1}: укажите хотя бы одно ключевое слово`;
      }
      if (it.mode === "case" && it.rubric_checklist.filter((c) => c.criterion.trim()).length === 0) {
        return `Вопрос #${i + 1}: добавьте критерии оценки кейса`;
      }
    }
    return null;
  };

  const handleSave = async () => {
    const err = validate();
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setSaving(true);
    setSavedFlash(null);
    try {
      if (!isEditing) {
        const created = await createAssessment(buildCreatePayload());
        navigate(`/tests/${created.id}/edit`, { replace: true });
        setSavedFlash("Тест создан");
        return;
      }
      // editing
      await updateAssessment(id!, {
        title: title.trim(),
        description: description.trim() || null,
        topic: topic.trim(),
        difficulty,
        related_skills: relatedSkillsStr
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        is_published: isPublished,
      });
      // process deletes
      for (const sid of pendingDeletes) {
        try {
          await deleteAssessmentItem(sid);
        } catch (e) {
          // continue, but surface later
          console.error("delete item failed", sid, e);
        }
      }
      // process items
      const newServerIds = new Set<string>();
      for (const it of items) {
        const payload = buildItemPayload(it);
        if (it.serverId && originalItemIds.has(it.serverId)) {
          const updated = await updateAssessmentItem(it.serverId, payload);
          newServerIds.add(updated.id);
        } else {
          const created = await addAssessmentItem(id!, payload);
          newServerIds.add(created.id);
          // bind serverId back to local
          updateItem(it.localId, { serverId: created.id });
        }
      }
      setOriginalItemIds(newServerIds);
      setPendingDeletes([]);
      setSavedFlash("Изменения сохранены");
      // refresh from server to align positions/ids
      await loadExisting();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  // ----- Render helpers -----
  const sectionStyle: React.CSSProperties = {
    background: "#fff",
    border: "1px solid #e2e8f0",
    borderRadius: 10,
    padding: 18,
    marginBottom: 18,
  };

  const inputStyle: React.CSSProperties = {
    padding: "8px 10px",
    border: "1px solid #cbd5e1",
    borderRadius: 6,
    fontSize: 14,
    width: "100%",
    boxSizing: "border-box",
  };

  const labelStyle: React.CSSProperties = {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    fontSize: 13,
    color: "#334155",
  };

  const btn = (variant: "primary" | "secondary" | "danger" = "secondary"): React.CSSProperties => ({
    padding: "8px 14px",
    borderRadius: 6,
    border: "1px solid",
    cursor: "pointer",
    fontSize: 13,
    background:
      variant === "primary" ? "#2563eb" : variant === "danger" ? "#fee2e2" : "#f1f5f9",
    color: variant === "primary" ? "#fff" : variant === "danger" ? "#b91c1c" : "#1f2937",
    borderColor:
      variant === "primary" ? "#1d4ed8" : variant === "danger" ? "#fecaca" : "#cbd5e1",
  });

  const renderModeFields = (it: DraftItem) => {
    if (it.mode === "quiz" || it.mode === "multi_select") {
      return (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>
            {it.mode === "quiz"
              ? "Отметьте один правильный вариант."
              : "Отметьте все правильные варианты."}
          </div>
          {it.options.map((opt) => (
            <div
              key={opt.id}
              style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}
            >
              <input
                type={it.mode === "quiz" ? "radio" : "checkbox"}
                name={`correct-${it.localId}`}
                checked={it.correct_option_ids.includes(opt.id)}
                onChange={() => toggleCorrect(it.localId, opt.id)}
              />
              <input
                type="text"
                placeholder="Текст варианта"
                value={opt.text}
                onChange={(e) => setOptionText(it.localId, opt.id, e.target.value)}
                style={{ ...inputStyle, flex: 1 }}
              />
              <button
                type="button"
                onClick={() => removeOption(it.localId, opt.id)}
                style={btn("danger")}
                disabled={it.options.length <= 2}
              >
                ✕
              </button>
            </div>
          ))}
          <button type="button" onClick={() => addOption(it.localId)} style={btn()}>
            + Вариант
          </button>
        </div>
      );
    }
    if (it.mode === "short_text") {
      return (
        <div style={{ marginTop: 10 }}>
          <label style={labelStyle}>
            Ключевые слова (через запятую)
            <input
              type="text"
              value={it.expected_keywords.join(", ")}
              onChange={(e) =>
                updateItem(it.localId, {
                  expected_keywords: e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                })
              }
              style={inputStyle}
              placeholder="например: python, async, pytest"
            />
          </label>
        </div>
      );
    }
    if (it.mode === "case") {
      return (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>
            Критерии оценивания и их веса (сумма весов = max_score).
          </div>
          {it.rubric_checklist.map((cr, idx) => (
            <div
              key={idx}
              style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}
            >
              <input
                type="text"
                placeholder="Критерий"
                value={cr.criterion}
                onChange={(e) => {
                  const next = [...it.rubric_checklist];
                  next[idx] = { ...next[idx], criterion: e.target.value };
                  updateItem(it.localId, { rubric_checklist: next });
                }}
                style={{ ...inputStyle, flex: 1 }}
              />
              <input
                type="number"
                min={0}
                step={0.5}
                value={cr.weight}
                onChange={(e) => {
                  const next = [...it.rubric_checklist];
                  next[idx] = { ...next[idx], weight: Number(e.target.value) };
                  updateItem(it.localId, { rubric_checklist: next });
                }}
                style={{ ...inputStyle, width: 100 }}
              />
              <button
                type="button"
                onClick={() => {
                  const next = it.rubric_checklist.filter((_, i) => i !== idx);
                  updateItem(it.localId, { rubric_checklist: next });
                }}
                style={btn("danger")}
              >
                ✕
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() =>
              updateItem(it.localId, {
                rubric_checklist: [...it.rubric_checklist, { criterion: "", weight: 1 }],
              })
            }
            style={btn()}
          >
            + Критерий
          </button>
        </div>
      );
    }
    return null;
  };

  const totalScore = useMemo(
    () => items.reduce((sum, it) => sum + (Number(it.max_score) || 0), 0),
    [items],
  );

  if (loading) {
    return (
      <AdminLayout>
        <div style={{ padding: 30 }}>Загрузка теста…</div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>
          {isEditing ? "Редактирование теста" : "Новый тест"}
        </h1>
        <Link to="/tests" style={{ fontSize: 13, color: "#2563eb" }}>
          ← Назад к списку
        </Link>
      </div>

      {error && (
        <div
          style={{
            background: "#fee2e2",
            border: "1px solid #fecaca",
            color: "#991b1b",
            padding: "10px 14px",
            borderRadius: 8,
            marginBottom: 14,
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}
      {savedFlash && (
        <div
          style={{
            background: "#dcfce7",
            border: "1px solid #86efac",
            color: "#166534",
            padding: "10px 14px",
            borderRadius: 8,
            marginBottom: 14,
            fontSize: 13,
          }}
        >
          {savedFlash}
        </div>
      )}

      <section style={sectionStyle}>
        <h2 style={{ fontSize: 16, marginTop: 0, marginBottom: 14 }}>Основные параметры</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <label style={labelStyle}>
            Название*
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={inputStyle}
              maxLength={300}
            />
          </label>
          <label style={labelStyle}>
            Тема*
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              style={inputStyle}
              maxLength={150}
              placeholder="напр. python, sql, soft-skills"
            />
          </label>
          <label style={labelStyle}>
            Сложность
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as Difficulty)}
              style={inputStyle}
            >
              {(Object.keys(DIFFICULTY_LABELS) as Difficulty[]).map((d) => (
                <option key={d} value={d}>
                  {DIFFICULTY_LABELS[d]}
                </option>
              ))}
            </select>
          </label>
          <label style={labelStyle}>
            Связанные навыки (через запятую)
            <input
              type="text"
              value={relatedSkillsStr}
              onChange={(e) => setRelatedSkillsStr(e.target.value)}
              style={inputStyle}
              placeholder="python, fastapi, sql"
            />
          </label>
          <label style={{ ...labelStyle, gridColumn: "1 / span 2" }}>
            Описание
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ ...inputStyle, minHeight: 80, fontFamily: "inherit" }}
            />
          </label>
          <label
            style={{
              ...labelStyle,
              flexDirection: "row",
              alignItems: "center",
              gap: 8,
              gridColumn: "1 / span 2",
            }}
          >
            <input
              type="checkbox"
              checked={isPublished}
              onChange={(e) => setIsPublished(e.target.checked)}
            />
            <span>Опубликован (виден пользователям)</span>
          </label>
        </div>
      </section>

      <section style={sectionStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h2 style={{ fontSize: 16, margin: 0 }}>
            Вопросы ({items.length}, суммарный балл {totalScore})
          </h2>
          <button type="button" onClick={addItem} style={btn("primary")}>
            + Добавить вопрос
          </button>
        </div>

        {items.length === 0 && (
          <div style={{ color: "#64748b", fontSize: 13 }}>Пока нет вопросов.</div>
        )}

        {items.map((it, idx) => (
          <div
            key={it.localId}
            style={{
              border: "1px solid #e2e8f0",
              borderRadius: 8,
              padding: 14,
              marginBottom: 12,
              background: "#f8fafc",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <strong style={{ fontSize: 14 }}>Вопрос #{idx + 1}</strong>
              <div style={{ display: "flex", gap: 6 }}>
                <button
                  type="button"
                  onClick={() => moveItem(it.localId, -1)}
                  style={btn()}
                  disabled={idx === 0}
                  title="Вверх"
                >
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => moveItem(it.localId, 1)}
                  style={btn()}
                  disabled={idx === items.length - 1}
                  title="Вниз"
                >
                  ↓
                </button>
                <button
                  type="button"
                  onClick={() => removeItem(it.localId)}
                  style={btn("danger")}
                >
                  Удалить
                </button>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 200px 120px", gap: 10, marginBottom: 10 }}>
              <label style={labelStyle}>
                Режим
                <select
                  value={it.mode}
                  onChange={(e) =>
                    updateItem(it.localId, { mode: e.target.value as AssessmentMode })
                  }
                  style={inputStyle}
                >
                  {(Object.keys(MODE_LABELS) as AssessmentMode[]).map((m) => (
                    <option key={m} value={m}>
                      {MODE_LABELS[m]}
                    </option>
                  ))}
                </select>
              </label>
              <label style={labelStyle}>
                Связанные навыки (через запятую)
                <input
                  type="text"
                  value={it.related_skills.join(", ")}
                  onChange={(e) =>
                    updateItem(it.localId, {
                      related_skills: e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean),
                    })
                  }
                  style={inputStyle}
                />
              </label>
              <label style={labelStyle}>
                Макс. балл
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  value={it.max_score}
                  onChange={(e) =>
                    updateItem(it.localId, { max_score: Number(e.target.value) })
                  }
                  style={inputStyle}
                />
              </label>
            </div>

            <label style={labelStyle}>
              Формулировка*
              <textarea
                value={it.prompt}
                onChange={(e) => updateItem(it.localId, { prompt: e.target.value })}
                style={{ ...inputStyle, minHeight: 70, fontFamily: "inherit" }}
              />
            </label>

            {renderModeFields(it)}

            <label style={{ ...labelStyle, marginTop: 10 }}>
              Пояснение (показывается после ответа)
              <textarea
                value={it.explanation}
                onChange={(e) => updateItem(it.localId, { explanation: e.target.value })}
                style={{ ...inputStyle, minHeight: 50, fontFamily: "inherit" }}
              />
            </label>
          </div>
        ))}
      </section>

      <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
        <Link to="/tests" style={{ ...btn(), display: "inline-block", textDecoration: "none" }}>
          Отмена
        </Link>
        <button
          type="button"
          onClick={handleSave}
          style={btn("primary")}
          disabled={saving}
        >
          {saving ? "Сохранение…" : isEditing ? "Сохранить изменения" : "Создать тест"}
        </button>
      </div>
    </AdminLayout>
  );
}

"""
Auto-check engine for assessment items.

Objective modes (quiz, multi-select) → deterministic score + is_correct.
Subjective modes (short-text, case) → keyword/rubric-based partial score,
  is_correct stays None, auto_feedback contains per-criterion notes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CheckResult:
    earned_score: float
    is_correct: bool | None
    auto_feedback: str


def check_quiz(item_data: dict[str, Any], selected_option_ids: list[str]) -> CheckResult:
    """Single-choice: full score if the one selected option is correct."""
    correct: list[str] = item_data.get("correct_option_ids") or []
    max_score: float = float(item_data.get("max_score", 1.0))
    options: list[dict] = item_data.get("options") or []
    explanation: str = item_data.get("explanation") or ""

    opt_map = {o.get("id"): o.get("text", o.get("id")) for o in options}
    correct_texts = [opt_map.get(c, c) for c in correct]
    correct_label = "; ".join(correct_texts) if correct_texts else str(correct)

    if not selected_option_ids:
        parts = [f"Правильный ответ: {correct_label}."]
        if explanation:
            parts.append(explanation)
        return CheckResult(0.0, False, "\n\n".join(parts))

    chosen = selected_option_ids[0]
    is_correct = chosen in correct
    earned = max_score if is_correct else 0.0

    if is_correct:
        parts = [f"Правильный ответ: {correct_label}."]
    else:
        chosen_text = opt_map.get(chosen, chosen)
        parts = [f"Правильный ответ: {correct_label}."]
    if explanation:
        parts.append(explanation)
    return CheckResult(round(earned, 3), is_correct, "\n\n".join(parts))


def check_multi_select(item_data: dict[str, Any], selected_option_ids: list[str]) -> CheckResult:
    """
    Partial credit: score = max_score * (matched - false_positives) / len(correct).
    Penalising wrong selections prevents guessing all options.
    """
    correct_set: set[str] = set(item_data.get("correct_option_ids") or [])
    max_score: float = float(item_data.get("max_score", 1.0))

    if not correct_set:
        return CheckResult(0.0, None, "No correct options defined for this item.")

    selected_set = set(selected_option_ids)
    matched = len(selected_set & correct_set)
    false_pos = len(selected_set - correct_set)
    ratio = max(0.0, (matched - false_pos) / len(correct_set))
    earned = round(max_score * ratio, 3)
    is_correct = selected_set == correct_set
    feedback = (
        f"Matched {matched}/{len(correct_set)} correct options"
        + (f"; {false_pos} incorrect option(s) selected." if false_pos else ".")
    )
    return CheckResult(earned, is_correct, feedback)


def check_short_text(item_data: dict[str, Any], text_answer: str) -> CheckResult:
    """
    Keyword coverage: partial score proportional to how many expected keywords
    appear in the lowercased answer text.
    """
    keywords: list[str] = [kw.lower() for kw in (item_data.get("expected_keywords") or [])]
    max_score: float = float(item_data.get("max_score", 1.0))
    text_lower = (text_answer or "").lower()

    if not keywords:
        return CheckResult(
            round(max_score * 0.5, 3),
            None,
            "No keywords defined – answer submitted for manual review.",
        )

    rubric: list[dict] = item_data.get("rubric_checklist") or []
    rubric_notes: list[str] = []

    if rubric:
        # Rubric-guided: each criterion adds weighted partial score
        total_weight = sum(float(r.get("weight", 1.0)) for r in rubric)
        earned_weight = 0.0
        for criterion in rubric:
            crit = (criterion.get("criterion") or "").lower()
            weight = float(criterion.get("weight", 1.0))
            found = any(kw in text_lower for kw in crit.split() if len(kw) > 3)
            if found:
                earned_weight += weight
                rubric_notes.append(f"✓ {criterion['criterion']}")
            else:
                rubric_notes.append(f"✗ {criterion['criterion']} – not addressed")
        ratio = earned_weight / total_weight if total_weight > 0 else 0.0
        earned = round(max_score * ratio, 3)
        return CheckResult(earned, None, "; ".join(rubric_notes))

    # Simple keyword matching
    matched_keywords = [kw for kw in keywords if kw in text_lower]
    ratio = len(matched_keywords) / len(keywords)
    earned = round(max_score * ratio, 3)
    feedback = (
        f"Matched {len(matched_keywords)}/{len(keywords)} keywords"
        + (f": {', '.join(matched_keywords)}." if matched_keywords else ".")
    )
    return CheckResult(earned, None, feedback)


def check_case(item_data: dict[str, Any], text_answer: str) -> CheckResult:
    """
    Rubric-based: each checklist criterion is checked for keyword presence.
    Weight controls the relative importance of each criterion.
    """
    rubric: list[dict] = item_data.get("rubric_checklist") or []
    max_score: float = float(item_data.get("max_score", 1.0))
    text_lower = (text_answer or "").lower()

    if not rubric:
        return CheckResult(
            round(max_score * 0.5, 3),
            None,
            "No rubric defined – answer submitted for manual review.",
        )

    total_weight = sum(float(r.get("weight", 1.0)) for r in rubric)
    earned_weight = 0.0
    notes: list[str] = []

    for criterion in rubric:
        crit_text = (criterion.get("criterion") or "").lower()
        weight = float(criterion.get("weight", 1.0))
        # Check each meaningful word (>3 chars) from the criterion
        significant_words = [w for w in crit_text.split() if len(w) > 3]
        found = bool(significant_words) and any(w in text_lower for w in significant_words)
        if found:
            earned_weight += weight
            notes.append(f"✓ {criterion['criterion']}")
        else:
            notes.append(f"✗ {criterion['criterion']} – not covered")

    ratio = earned_weight / total_weight if total_weight > 0 else 0.0
    earned = round(max_score * ratio, 3)
    return CheckResult(earned, None, "; ".join(notes))


# ── Public entry point ────────────────────────────────────────────────────────

def check_answer(
    item_data: dict[str, Any],
    selected_option_ids: list[str],
    text_answer: str | None,
) -> CheckResult:
    """Dispatch to the appropriate checker based on item mode."""
    mode: str = item_data.get("mode", "quiz")

    if mode == "quiz":
        return check_quiz(item_data, selected_option_ids)
    if mode == "multi-select":
        return check_multi_select(item_data, selected_option_ids)
    if mode == "short-text":
        return check_short_text(item_data, text_answer or "")
    if mode == "case":
        return check_case(item_data, text_answer or "")

    return CheckResult(0.0, None, f"Unknown item mode '{mode}'.")


# ── Attempt-level aggregation ─────────────────────────────────────────────────

_SKILL_PASS_THRESHOLD = 0.5  # earn < 50% of item max_score → skill is "weak"


def build_weak_skills(
    item_data_list: list[dict[str, Any]],
    results: list[CheckResult],
) -> list[str]:
    """Return deduplicated skill names from items where the user scored below threshold."""
    weak: set[str] = set()
    for item_data, result in zip(item_data_list, results):
        max_s = float(item_data.get("max_score", 1.0))
        if max_s > 0 and result.earned_score < max_s * _SKILL_PASS_THRESHOLD:
            for skill in item_data.get("related_skills") or []:
                weak.add(skill)
    return sorted(weak)


def build_summary(percentage: float) -> str:
    if percentage >= 90:
        return f"Excellent! You scored {percentage:.1f}%. Outstanding performance."
    if percentage >= 75:
        return f"Good job! You scored {percentage:.1f}%. Solid understanding of the material."
    if percentage >= 50:
        return f"Satisfactory. You scored {percentage:.1f}%. Review the topics you missed."
    return f"Needs improvement. You scored {percentage:.1f}%. Consider revisiting the material."


def build_recommended_materials(weak_skills: list[str]) -> list[str]:
    """
    Return basic learning resource suggestions for each weak skill.
    In Phase 2 this will query the courses catalog via recommendation-service.
    """
    suggestions: list[str] = []
    for skill in weak_skills:
        suggestions.append(f"Review learning materials for: {skill}")
    return suggestions

"""Assessment listing and quiz-taking handlers."""
from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..clients import assessment as assessment_client
from ..keyboards.main_menu import (
    assessment_list_keyboard,
    quiz_options_keyboard,
    quiz_result_keyboard,
    quiz_skip_keyboard,
)
from ..state import QuizState, clear_quiz_state, get_quiz_state, get_session, save_quiz_state
from .states import AssessmentStates

router = Router(name="assessments")

DIFFICULTY_ICON = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}


def _format_attempt_history(attempts: list[dict]) -> str:
    if not attempts:
        return "Вы ещё не проходили задания."
    lines = ["📜 <b>История заданий</b>\n"]
    for a in attempts[:8]:
        pct = a.get("percentage", 0)
        icon = "🟢" if pct >= 75 else "🟡" if pct >= 50 else "🔴"
        lines.append(
            f"{icon} {pct:.1f}% — {a.get('status', '')} "
            f"(<code>{str(a.get('assessment_id', ''))[:8]}…</code>)"
        )
    return "\n".join(lines)


# ── List ───────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({"📝 Задания", "📝 Assessments"}))
@router.message(Command("assessments"))
async def show_assessments(message: Message, state: FSMContext) -> None:
    await state.clear()  # сброс режима прохождения теста
    session = await get_session(message.from_user.id)
    if not session:
        await message.answer("Пожалуйста, войдите через /start.")
        return
    assessments = await assessment_client.list_assessments(session.access_token)
    if not assessments:
        await message.answer("Пока нет доступных заданий. Проверьте позже!")
        return
    await message.answer(
        "📝 <b>Доступные задания</b>\n\nВыберите задание чтобы начать:",
        reply_markup=assessment_list_keyboard(assessments),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "assessment:list")
async def cb_assessment_list(call: CallbackQuery) -> None:
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    assessments = await assessment_client.list_assessments(session.access_token)
    if not assessments:
        await call.answer("Нет доступных заданий.", show_alert=True)
        return
    await call.message.answer(
        "📝 <b>Доступные задания</b>\n\nВыберите задание:",
        reply_markup=assessment_list_keyboard(assessments),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "assessment:history")
async def cb_assessment_history(call: CallbackQuery) -> None:
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    attempts = await assessment_client.get_my_attempts(session.access_token)
    text = _format_attempt_history(attempts)
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()


# ── Start quiz ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("assessment:start:"))
async def cb_start_assessment(call: CallbackQuery, state: FSMContext) -> None:
    assessment_id = call.data.split(":", 2)[2]
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    await call.answer("⏳ Загружаю задание…")
    data = await assessment_client.get_assessment(session.access_token, assessment_id)
    if not data:
        await call.message.answer("❌ Не удалось загрузить задание. Попробуйте позже.")
        return
    items = data.get("items", [])
    if not items:
        await call.message.answer("В этом задании нет вопросов.")
        return

    quiz = QuizState(
        assessment_id=assessment_id,
        title=data.get("title", "Задание"),
        items=items,
        current_idx=0,
        answers=[],
    )
    await save_quiz_state(call.from_user.id, quiz)
    await state.set_state(AssessmentStates.taking_quiz)

    diff = DIFFICULTY_ICON.get(data.get("difficulty", ""), "")
    topic = data.get("topic") or ""
    await call.message.answer(
        f"📝 <b>{data['title']}</b>\n"
        f"{diff} {topic} · {len(items)} вопрос(ов)\n\n"
        f"Отвечайте по очереди. Начинаем!",
        parse_mode="HTML",
    )
    await _send_question(call.message, quiz)


async def _send_question(message: Message, quiz: QuizState) -> None:
    """Send the current question to the user."""
    item = quiz.items[quiz.current_idx]
    total = len(quiz.items)
    item_id = str(item.get("id", ""))
    prompt = item.get("prompt", "")
    mode = item.get("mode", "quiz")
    options = item.get("options") or []

    header = f"<b>Вопрос {quiz.current_idx + 1} из {total}</b>\n\n"

    if mode in ("quiz", "multi_select") and options:
        letters = "ABCDEFGHIJ"
        opt_lines = []
        for i, opt in enumerate(options):
            letter = letters[i] if i < len(letters) else str(i + 1)
            raw = (opt.get("text") or "").strip()
            # Убрать дублирующий префикс варианта (A), A. …)
            cleaned = re.sub(r"^[A-Za-zА-Яа-я]\s*[.)]\s*", "", raw).strip() or raw
            opt_lines.append(f"{letter}. {cleaned}")
        text = header + prompt + "\n\n" + "\n".join(opt_lines)
        await message.answer(
            text,
            reply_markup=quiz_options_keyboard(options, item_id),
            parse_mode="HTML",
        )
    else:
        # Режим short_text / case — ответ текстом
        text = header + prompt + "\n\n<i>Введите ваш ответ текстом или нажмите «Пропустить».</i>"
        await message.answer(
            text,
            reply_markup=quiz_skip_keyboard(item_id),
            parse_mode="HTML",
        )


# ── Answer handling ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("qanswer:"), AssessmentStates.taking_quiz)
async def cb_quiz_answer(call: CallbackQuery, state: FSMContext) -> None:
    _, item_id, option_id = call.data.split(":", 2)
    tg_id = call.from_user.id
    quiz = await get_quiz_state(tg_id)
    if not quiz:
        await call.answer("Сессия задания истекла. Начните заново.", show_alert=True)
        await state.clear()
        return

    quiz.answers.append({
        "item_id": item_id,
        "selected_option_ids": [option_id],
        "free_text": None,
    })
    quiz.current_idx += 1
    await save_quiz_state(tg_id, quiz)
    await call.answer("✅")

    if quiz.current_idx >= len(quiz.items):
        await _submit_and_finish(call.message, state, tg_id, quiz)
    else:
        await _send_question(call.message, quiz)


@router.callback_query(F.data.startswith("qskip:"), AssessmentStates.taking_quiz)
async def cb_quiz_skip(call: CallbackQuery, state: FSMContext) -> None:
    _, item_id = call.data.split(":", 1)
    tg_id = call.from_user.id
    quiz = await get_quiz_state(tg_id)
    if not quiz:
        await call.answer("Сессия задания истекла.", show_alert=True)
        await state.clear()
        return

    quiz.answers.append({
        "item_id": item_id,
        "selected_option_ids": [],
        "free_text": None,
    })
    quiz.current_idx += 1
    await save_quiz_state(tg_id, quiz)
    await call.answer("⏭")

    if quiz.current_idx >= len(quiz.items):
        await _submit_and_finish(call.message, state, tg_id, quiz)
    else:
        await _send_question(call.message, quiz)


@router.message(AssessmentStates.taking_quiz)
async def quiz_free_text_answer(message: Message, state: FSMContext) -> None:
    """Handle free-text answer typed by the user."""
    tg_id = message.from_user.id
    quiz = await get_quiz_state(tg_id)
    if not quiz:
        await state.clear()
        return

    item = quiz.items[quiz.current_idx]
    item_id = str(item.get("id", ""))
    quiz.answers.append({
        "item_id": item_id,
        "selected_option_ids": [],
        "free_text": message.text or "",
    })
    quiz.current_idx += 1
    await save_quiz_state(tg_id, quiz)

    if quiz.current_idx >= len(quiz.items):
        await _submit_and_finish(message, state, tg_id, quiz)
    else:
        await _send_question(message, quiz)


# ── Submit & results ──────────────────────────────────────────────────────────

async def _submit_and_finish(
    message: Message,
    state: FSMContext,
    tg_id: int,
    quiz: QuizState,
) -> None:
    await state.clear()
    await clear_quiz_state(tg_id)

    session = await get_session(tg_id)
    if not session:
        await message.answer("Ошибка сессии. Войдите снова через /start.")
        return

    await message.answer("⏳ Подсчитываю результаты…")
    result = await assessment_client.submit_assessment(
        session.access_token, quiz.assessment_id, quiz.answers
    )

    if not result:
        await message.answer(
            "❌ Не удалось отправить ответы. Попробуйте пройти задание снова.",
            reply_markup=quiz_result_keyboard(),
        )
        return

    pct = result.get("percentage", 0)
    passed = result.get("passed", False)
    correct = result.get("correct_count", "?")
    total = result.get("total_count", len(quiz.items))

    icon = "🏆" if pct >= 80 else "✅" if pct >= 60 else "📚"
    result_label = "Отлично!" if pct >= 80 else "Хорошо!" if pct >= 60 else "Нужна практика"

    lines = [
        f"{icon} <b>{quiz.title}</b> — завершено!",
        "",
        f"Результат: <b>{pct:.1f}%</b> ({correct} из {total})",
        f"Статус: {'✅ Пройдено' if passed else '❌ Не пройдено'}",
        f"\n<i>{result_label}</i>",
    ]

    answers_detail = result.get("answers") or []
    if answers_detail:
        lines.append("\n<b>Разбор ответов:</b>")
        for i, ans in enumerate(answers_detail[:10], 1):
            is_correct = ans.get("is_correct", False)
            expl = ans.get("explanation") or ""
            lines.append(f"{'✅' if is_correct else '❌'} Вопрос {i}" + (f": {expl[:80]}" if expl else ""))

    await message.answer(
        "\n".join(lines),
        reply_markup=quiz_result_keyboard(),
        parse_mode="HTML",
    )

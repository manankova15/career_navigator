"""Recommendations and skill-gap handlers."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..clients import recommendation as rec_client
from ..keyboards.main_menu import recommendation_keyboard
from ..state import get_session

router = Router(name="recommendations")


def _format_recommendations(data: dict) -> str:
    recs = data.get("items", [])
    if not recs:
        return (
            "Рекомендаций пока нет. "
            "Нажмите <b>Получить рекомендации</b> для формирования подборки."
        )
    lines = [
        f"⭐ <b>Ваши рекомендации</b> "
        f"(алгоритм: {data.get('algorithm', 'content_ahp_v2')})\n"
    ]
    for i, r in enumerate(recs[:5], 1):
        score = r.get("score", 0)
        matched = r.get("matched_skills", [])[:3]
        title = r.get("title") or f"Вакансия #{str(r.get('vacancy_id', ''))[:6]}"
        company = r.get("company") or ""
        skills_str = ", ".join(matched) if matched else "—"
        lines.append(
            f"{i}. <b>{title}</b>"
            + (f" · {company}" if company else "")
            + f"\n   Оценка: {score:.2f} | Навыки: {skills_str}"
        )
    lines.append(f"\n<i>Показано {min(5, len(recs))} из {data.get('total', len(recs))}</i>")
    return "\n".join(lines)


def _format_skill_gap(data: dict) -> str:
    gaps = data.get("gaps", [])
    if not gaps:
        return "Анализ навыков пока недоступен. Сначала получите рекомендации."
    lines = ["📊 <b>Анализ пробелов в навыках</b>\n"]
    for gap in gaps[:8]:
        importance = gap.get("importance_score", 0)
        freq = gap.get("frequency", 0)
        skill = gap.get("skill_name", "?")
        lines.append(
            f"  #{gap.get('rank', '?')} <b>{skill}</b> "
            f"— важность {importance:.2f}, встречается в {freq} вакансиях"
        )
    return "\n".join(lines)


@router.message(F.text.in_({"⭐ Рекомендации", "⭐ Recommendations"}))
@router.message(Command("recommendations"))
async def show_recommendations(message: Message, state: FSMContext) -> None:
    await state.clear()
    session = await get_session(message.from_user.id)
    if not session:
        await message.answer("Пожалуйста, войдите через /start.")
        return
    data = await rec_client.get_my_recommendations(session.access_token)
    items = (data or {}).get("items") or []
    has_data = bool(items)
    text = _format_recommendations(data or {})
    await message.answer(
        text,
        reply_markup=recommendation_keyboard(has_data, items),
        parse_mode="HTML",
    )


@router.message(F.text.in_({"📊 Анализ навыков", "📊 Skill Gap"}))
@router.message(Command("skillgap"))
async def show_skill_gap(message: Message, state: FSMContext) -> None:
    await state.clear()
    session = await get_session(message.from_user.id)
    if not session:
        await message.answer("Пожалуйста, войдите через /start.")
        return
    data = await rec_client.get_skill_gap(session.access_token)
    text = _format_skill_gap(data or {})
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "rec:refresh")
async def cb_rec_refresh(call: CallbackQuery) -> None:
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    await call.answer("⏳ Формирую рекомендации…")
    data = await rec_client.refresh_recommendations(session.access_token)
    items = (data or {}).get("items") or []
    has_data = bool(items)
    text = _format_recommendations(data or {})
    await call.message.edit_text(
        text,
        reply_markup=recommendation_keyboard(has_data, items),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "rec:skillgap")
async def cb_rec_skillgap(call: CallbackQuery) -> None:
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    data = await rec_client.get_skill_gap(session.access_token)
    text = _format_skill_gap(data or {})
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()


async def _send_refreshed_feed(call: CallbackQuery, token: str) -> None:
    data = await rec_client.get_my_recommendations(token)
    items = (data or {}).get("items") or []
    has_data = bool(items)
    text = _format_recommendations(data or {})
    try:
        await call.message.edit_text(
            text,
            reply_markup=recommendation_keyboard(has_data, items),
            parse_mode="HTML",
        )
    except Exception:
        await call.message.answer(
            text,
            reply_markup=recommendation_keyboard(has_data, items),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("rec:like:"))
async def cb_rec_like(call: CallbackQuery) -> None:
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    vacancy_id = call.data.split(":", 2)[2]
    await rec_client.register_interaction(
        session.access_token, vacancy_id, sentiment="positive"
    )
    await call.answer("👍 Учтено. Пересчитываю подборку…")
    await _send_refreshed_feed(call, session.access_token)


@router.callback_query(F.data.startswith("rec:dislike:"))
async def cb_rec_dislike(call: CallbackQuery) -> None:
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    vacancy_id = call.data.split(":", 2)[2]
    await rec_client.register_interaction(
        session.access_token, vacancy_id, sentiment="negative"
    )
    await call.answer("👎 Учтено. Эта и похожие вакансии опустятся ниже.")
    await _send_refreshed_feed(call, session.access_token)

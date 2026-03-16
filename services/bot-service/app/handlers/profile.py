"""Profile and notifications handlers."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..clients import profile as profile_client
from ..keyboards.main_menu import notification_settings_keyboard, web_link_keyboard
from ..state import get_session

router = Router(name="profile")


def _format_profile(profile: dict, full_name: str) -> str:
    first_name = profile.get("first_name") or ""
    last_name = profile.get("last_name") or ""
    display = f"{first_name} {last_name}".strip() or full_name
    headline = profile.get("headline") or "—"
    location = profile.get("location") or "—"
    target_role = profile.get("target_role") or "—"
    bio = profile.get("bio") or ""
    lines = [
        f"👤 <b>{display}</b>",
        f"💼 {headline}",
        f"📍 {location}",
        f"🎯 Желаемая должность: {target_role}",
    ]
    if bio:
        lines.append(f"\n{bio[:200]}")
    lines.append("\n<i>Для редактирования откройте веб-версию.</i>")
    return "\n".join(lines)


@router.message(F.text.in_({"👤 Профиль", "👤 Profile"}))
@router.message(Command("profile"))
async def show_profile(message: Message, state: FSMContext) -> None:
    await state.clear()  # выходим из режима теста/поиска, показываем профиль
    session = await get_session(message.from_user.id)
    if not session:
        await message.answer("Пожалуйста, войдите через /start.")
        return
    profile = await profile_client.get_my_profile(session.access_token)
    if not profile:
        await message.answer(
            "Профиль пока не заполнен. Заполните его в веб-версии:",
            reply_markup=web_link_keyboard("🌐 Открыть профиль", "https://career-navigator.local/profile"),
        )
        return
    text = _format_profile(profile, session.full_name)
    await message.answer(
        text,
        reply_markup=web_link_keyboard("✏️ Редактировать профиль", "https://career-navigator.local/profile"),
        parse_mode="HTML",
    )


@router.message(F.text.in_({"🔔 Уведомления", "🔔 Notifications"}))
@router.message(Command("notifications"))
async def show_notification_settings(message: Message, state: FSMContext) -> None:
    await state.clear()
    session = await get_session(message.from_user.id)
    if not session:
        await message.answer("Пожалуйста, войдите через /start.")
        return
    await message.answer(
        "🔔 <b>Настройки уведомлений</b>\n\nВключайте или отключайте каналы уведомлений:",
        reply_markup=notification_settings_keyboard(email_on=True, tg_on=True, digest_on=True),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("notif:toggle_"))
async def cb_toggle_notification(call: CallbackQuery) -> None:
    await call.answer(
        "Управление уведомлениями доступно в веб-версии.", show_alert=True
    )

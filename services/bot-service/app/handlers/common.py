"""
/start, /help, /logout handlers. Авторизация по Telegram при /start (без email/пароля).
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..clients import auth as auth_client
from ..clients import profile as profile_client
from ..keyboards.main_menu import main_menu_keyboard
from ..state import UserSession, delete_session, get_session, has_session, save_session

router = Router(name="common")

_HELP = (
    "📖 <b>Доступные команды:</b>\n\n"
    "/start — главное меню\n"
    "/help — справка\n"
    "/logout — выйти из аккаунта\n\n"
    "<b>Кнопки меню:</b>\n"
    "📋 <b>Вакансии</b> — поиск и просмотр вакансий\n"
    "⭐ <b>Рекомендации</b> — персональная AI-подборка\n"
    "📝 <b>Задания</b> — тесты и отслеживание прогресса\n"
    "👤 <b>Профиль</b> — ваш карьерный профиль\n"
    "📊 <b>Анализ навыков</b> — что стоит прокачать\n"
    "🔔 <b>Уведомления</b> — настройки уведомлений"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    tg_user = message.from_user
    tg_id = tg_user.id
    if await has_session(tg_id):
        session = await get_session(tg_id)
        first = session.first_name or (session.full_name or "").split()[0] or session.full_name
        await message.answer(
            f"Привет, <b>{first}</b>! Рад снова тебя видеть.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    # Авторизация по Telegram: один запрос к auth-service — получаем токен (или создаётся пользователь)
    result = await auth_client.login_by_telegram(
        tg_id,
        tg_user.username,
        tg_user.first_name,
        tg_user.last_name,
    )
    if not result:
        await message.answer(
            "❌ Не удалось войти. Попробуйте позже или напишите в поддержку.",
            parse_mode="HTML",
        )
        return

    token = result["access_token"]
    me = await auth_client.get_me(token)
    name = (me or {}).get("full_name", tg_user.full_name or "Пользователь")
    user_id = (me or {}).get("user_id", "")
    profile = await profile_client.get_my_profile(token)
    first_name = (profile or {}).get("first_name") or (name.split()[0] if name else "") or name

    session = UserSession(
        telegram_id=tg_id,
        access_token=token,
        user_id=str(user_id),
        full_name=name,
        first_name=first_name or "",
    )
    await save_session(session)
    await message.answer(
        f"👋 Добро пожаловать, <b>{first_name or name}</b>! Вы вошли по аккаунту Telegram.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    """Показать основное меню (кнопки)."""
    await state.clear()
    session = await get_session(message.from_user.id)
    if not session:
        await message.answer("Сначала войдите через /start.")
        return
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP, parse_mode="HTML")


@router.message(Command("logout"))
async def cmd_logout(message: Message, state: FSMContext) -> None:
    tg_id = message.from_user.id
    await state.clear()
    await delete_session(tg_id)
    await message.answer("✅ Вы вышли из аккаунта. Используйте /start чтобы войти снова.")



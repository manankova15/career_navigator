"""Vacancy browse, search and one-by-one navigation handlers."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..clients import vacancy as vacancy_client
from ..keyboards.main_menu import (
    seniority_keyboard,
    vacancy_count_keyboard,
    vacancy_filter_keyboard,
    vacancy_nav_keyboard,
    web_link_keyboard,
)
from ..state import VacancyNavState, get_session, get_vacancy_nav, save_vacancy_nav
from .states import VacancyFilterStates

router = Router(name="vacancies")

SENIORITY_LABELS = {
    "intern": "Intern",
    "junior": "Junior",
    "middle": "Middle",
    "senior": "Senior",
    "lead": "Lead",
}


def _format_vacancy(v: dict, pos: int, total: int) -> str:
    title = v.get("title") or "Вакансия"
    company = v.get("company") or "—"
    location = v.get("location") or "Не указан"
    seniority = SENIORITY_LABELS.get(v.get("seniority") or "", v.get("seniority") or "")
    skills = (v.get("skills") or [])[:6]
    sal_from = v.get("salary_from")
    sal_to = v.get("salary_to")
    currency = v.get("currency") or "RUB"

    salary_str = "Не указана"
    if sal_from or sal_to:
        parts = [str(sal_from) if sal_from else None,
                 str(sal_to) if sal_to else None]
        salary_str = " – ".join(p for p in parts if p) + f" {currency}"

    lines = [
        f"<b>{title}</b>",
        f"🏢 {company}",
        f"📍 {location}",
    ]
    if seniority:
        lines.append(f"🎯 Уровень: {seniority}")
    lines.append(f"💰 {salary_str}")
    if skills:
        lines.append(f"🛠 Навыки: {', '.join(skills)}")
    lines.append(f"\n<i>Вакансия {pos + 1} из {total}</i>")
    return "\n".join(lines)


# ── Entry point ────────────────────────────────────────────────────────────────

@router.message(F.text.in_({"📋 Вакансии", "📋 Vacancies"}))
@router.message(Command("vacancies"))
async def show_vacancy_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    session = await get_session(message.from_user.id)
    if not session:
        await message.answer("Пожалуйста, войдите через /start.")
        return
    await message.answer(
        "📋 <b>Вакансии</b>\n\nВыберите, сколько вакансий загрузить, "
        "или воспользуйтесь поиском по фильтрам:",
        reply_markup=vacancy_count_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "vacancy:menu")
async def cb_vacancy_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.answer(
        "📋 <b>Вакансии</b>\n\nВыберите количество или воспользуйтесь фильтрами:",
        reply_markup=vacancy_count_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


# ── Count selection ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vcount:"))
async def cb_vacancy_count(call: CallbackQuery) -> None:
    count = int(call.data.split(":")[1])
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    await call.answer("⏳ Загружаю вакансии…")
    nav = await get_vacancy_nav(call.from_user.id)
    filters = nav.filters if nav else {}
    vacancies = await vacancy_client.search_vacancies(
        session.access_token,
        query=filters.get("query", ""),
        location=filters.get("location"),
        seniority=filters.get("seniority"),
        limit=count,
    )
    if not vacancies:
        await call.message.answer(
            "😔 Вакансии не найдены. Попробуйте изменить фильтры.",
            reply_markup=vacancy_count_keyboard(),
        )
        return
    nav_state = VacancyNavState(vacancies=vacancies, pos=0, filters=filters)
    await save_vacancy_nav(call.from_user.id, nav_state)
    text = _format_vacancy(vacancies[0], 0, len(vacancies))
    await call.message.answer(
        text,
        reply_markup=vacancy_nav_keyboard(0, len(vacancies), str(vacancies[0].get("id", ""))),
        parse_mode="HTML",
    )


# ── One-by-one navigation ──────────────────────────────────────────────────────

@router.callback_query(F.data.in_({"vnav:next", "vnav:prev"}))
async def cb_vacancy_nav(call: CallbackQuery) -> None:
    nav = await get_vacancy_nav(call.from_user.id)
    if not nav or not nav.vacancies:
        await call.answer("Список вакансий устарел. Начните заново.", show_alert=True)
        return
    if call.data == "vnav:next":
        nav.pos = min(nav.pos + 1, len(nav.vacancies) - 1)
    else:
        nav.pos = max(nav.pos - 1, 0)
    await save_vacancy_nav(call.from_user.id, nav)
    v = nav.vacancies[nav.pos]
    text = _format_vacancy(v, nav.pos, len(nav.vacancies))
    await call.message.edit_text(
        text,
        reply_markup=vacancy_nav_keyboard(nav.pos, len(nav.vacancies), str(v.get("id", ""))),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("vdetail:"))
async def cb_vacancy_apply(call: CallbackQuery) -> None:
    vacancy_id = call.data.split(":", 1)[1]
    nav = await get_vacancy_nav(call.from_user.id)
    # Find vacancy in nav list to get canonical_url
    canonical = None
    if nav:
        for v in nav.vacancies:
            if str(v.get("id", "")) == vacancy_id:
                canonical = v.get("canonical_url")
                break
    if canonical:
        await call.message.answer(
            "🔗 Ссылка для отклика на вакансию:",
            reply_markup=web_link_keyboard("Откликнуться на источнике →", canonical),
        )
    else:
        await call.message.answer("Ссылка на вакансию недоступна.")
    await call.answer()


# ── Filters ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "vacancy:filter")
async def cb_vacancy_filter_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    nav = await get_vacancy_nav(call.from_user.id)
    filters = nav.filters if nav else {}
    filter_summary = _filter_summary(filters)
    await call.message.answer(
        f"🔍 <b>Поиск по фильтрам</b>\n{filter_summary}\nВыберите фильтр:",
        reply_markup=vacancy_filter_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


def _filter_summary(filters: dict) -> str:
    parts = []
    if filters.get("query"):
        parts.append(f"Ключевое слово: <b>{filters['query']}</b>")
    if filters.get("location"):
        parts.append(f"Город: <b>{filters['location']}</b>")
    if filters.get("seniority"):
        parts.append(f"Уровень: <b>{SENIORITY_LABELS.get(filters['seniority'], filters['seniority'])}</b>")
    return ("\n".join(parts) + "\n") if parts else "Фильтры не заданы.\n"


@router.callback_query(F.data == "vfilter:query")
async def cb_filter_query(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer("Введите ключевое слово (например: Python, Data Analyst, Backend):")
    await state.set_state(VacancyFilterStates.waiting_query)
    await call.answer()


@router.message(VacancyFilterStates.waiting_query)
async def filter_query_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    nav = await get_vacancy_nav(message.from_user.id) or VacancyNavState()
    nav.filters["query"] = message.text.strip()
    await save_vacancy_nav(message.from_user.id, nav)
    await message.answer(
        f"✅ Ключевое слово: <b>{nav.filters['query']}</b>\n\nПродолжить настройку фильтров или начать поиск:",
        reply_markup=vacancy_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "vfilter:location")
async def cb_filter_location(call: CallbackQuery, state: FSMContext) -> None:
    await call.message.answer("Введите город (например: Москва, Санкт-Петербург, remote):")
    await state.set_state(VacancyFilterStates.waiting_location)
    await call.answer()


@router.message(VacancyFilterStates.waiting_location)
async def filter_location_input(message: Message, state: FSMContext) -> None:
    await state.clear()
    nav = await get_vacancy_nav(message.from_user.id) or VacancyNavState()
    nav.filters["location"] = message.text.strip()
    await save_vacancy_nav(message.from_user.id, nav)
    await message.answer(
        f"✅ Город: <b>{nav.filters['location']}</b>\n\nПродолжить или начать поиск:",
        reply_markup=vacancy_filter_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "vfilter:seniority")
async def cb_filter_seniority(call: CallbackQuery) -> None:
    await call.message.answer("Выберите уровень:", reply_markup=seniority_keyboard())
    await call.answer()


@router.callback_query(F.data.startswith("vseniority:"))
async def cb_seniority_selected(call: CallbackQuery) -> None:
    val = call.data.split(":")[1]
    nav = await get_vacancy_nav(call.from_user.id) or VacancyNavState()
    if val == "any":
        nav.filters.pop("seniority", None)
        label = "любой"
    else:
        nav.filters["seniority"] = val
        label = SENIORITY_LABELS.get(val, val)
    await save_vacancy_nav(call.from_user.id, nav)
    await call.message.answer(
        f"✅ Уровень: <b>{label}</b>\n\nПродолжить или начать поиск:",
        reply_markup=vacancy_filter_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "vfilter:reset")
async def cb_filter_reset(call: CallbackQuery) -> None:
    nav = await get_vacancy_nav(call.from_user.id) or VacancyNavState()
    nav.filters = {}
    await save_vacancy_nav(call.from_user.id, nav)
    await call.message.answer("🔁 Фильтры сброшены.", reply_markup=vacancy_filter_keyboard())
    await call.answer()


@router.callback_query(F.data == "vfilter:go")
async def cb_filter_go(call: CallbackQuery) -> None:
    session = await get_session(call.from_user.id)
    if not session:
        await call.answer("Пожалуйста, войдите.", show_alert=True)
        return
    nav = await get_vacancy_nav(call.from_user.id) or VacancyNavState()
    await call.answer("⏳ Ищу вакансии…")
    vacancies = await vacancy_client.search_vacancies(
        session.access_token,
        query=nav.filters.get("query", ""),
        location=nav.filters.get("location"),
        seniority=nav.filters.get("seniority"),
        limit=10,
    )
    if not vacancies:
        await call.message.answer(
            "😔 По вашим фильтрам вакансий не найдено. Попробуйте изменить критерии.",
            reply_markup=vacancy_filter_keyboard(),
        )
        return
    nav.vacancies = vacancies
    nav.pos = 0
    await save_vacancy_nav(call.from_user.id, nav)
    text = _format_vacancy(vacancies[0], 0, len(vacancies))
    await call.message.answer(
        text,
        reply_markup=vacancy_nav_keyboard(0, len(vacancies), str(vacancies[0].get("id", ""))),
        parse_mode="HTML",
    )

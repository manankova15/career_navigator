"""Keyboard layouts for the Telegram bot."""
import re

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard shown at the bottom."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📋 Вакансии"),
        KeyboardButton(text="⭐ Рекомендации"),
    )
    builder.row(
        KeyboardButton(text="📝 Задания"),
        KeyboardButton(text="👤 Профиль"),
    )
    builder.row(
        KeyboardButton(text="📊 Анализ навыков"),
        KeyboardButton(text="🔔 Уведомления"),
    )
    builder.row(KeyboardButton(text="❓ Помощь"))
    return builder.as_markup(resize_keyboard=True)


# ── Vacancies ──────────────────────────────────────────────────────────────────

def vacancy_count_keyboard() -> InlineKeyboardMarkup:
    """Let user pick how many vacancies to browse."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="5 вакансий", callback_data="vcount:5"),
        InlineKeyboardButton(text="10 вакансий", callback_data="vcount:10"),
        InlineKeyboardButton(text="20 вакансий", callback_data="vcount:20"),
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск по фильтрам", callback_data="vacancy:filter"),
    )
    return builder.as_markup()


def vacancy_nav_keyboard(pos: int, total: int, vacancy_id: str) -> InlineKeyboardMarkup:
    """Navigation for one-by-one vacancy browsing."""
    builder = InlineKeyboardBuilder()
    nav_row = []
    if pos > 0:
        nav_row.append(InlineKeyboardButton(text="← Предыдущая", callback_data=f"vnav:prev"))
    if pos < total - 1:
        nav_row.append(InlineKeyboardButton(text="Следующая →", callback_data=f"vnav:next"))
    if nav_row:
        builder.row(*nav_row)
    builder.row(
        InlineKeyboardButton(
            text="🔗 Откликнуться",
            callback_data=f"vdetail:{vacancy_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="📋 Список вакансий", callback_data="vacancy:menu"),
        InlineKeyboardButton(text="🔍 Новый поиск", callback_data="vacancy:filter"),
    )
    return builder.as_markup()


def vacancy_filter_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔤 По ключевому слову", callback_data="vfilter:query"),
    )
    builder.row(
        InlineKeyboardButton(text="📍 По городу", callback_data="vfilter:location"),
    )
    builder.row(
        InlineKeyboardButton(text="🎯 По уровню", callback_data="vfilter:seniority"),
    )
    builder.row(
        InlineKeyboardButton(text="🔁 Сбросить фильтры", callback_data="vfilter:reset"),
    )
    builder.row(
        InlineKeyboardButton(text="▶ Найти вакансии", callback_data="vfilter:go"),
    )
    return builder.as_markup()


def seniority_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    levels = [("intern", "Intern"), ("junior", "Junior"), ("middle", "Middle"),
              ("senior", "Senior"), ("lead", "Lead")]
    for val, label in levels:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"vseniority:{val}"))
    builder.row(InlineKeyboardButton(text="Любой уровень", callback_data="vseniority:any"))
    return builder.as_markup()


# ── Assessments ───────────────────────────────────────────────────────────────

def assessment_list_keyboard(assessments: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for a in assessments[:8]:
        title = (a.get("title") or "Assessment")[:35]
        aid = str(a.get("id", ""))
        diff = a.get("difficulty", "")
        icon = "🟢" if diff == "easy" else "🟡" if diff == "medium" else "🔴"
        cnt = a.get("item_count", 0)
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {title} ({cnt} вопр.)",
                callback_data=f"assessment:start:{aid}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="📜 История", callback_data="assessment:history"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="assessment:list"),
    )
    return builder.as_markup()


def _clean_option_text(raw: str) -> str:
    """Убрать ведущие 'A)', 'A.' и т.д., чтобы не дублировать букву в 'A. A) текст'."""
    s = (raw or "").strip()
    return re.sub(r"^[A-Za-zА-Яа-я]\s*[.)]\s*", "", s).strip() or s


def quiz_options_keyboard(options: list[dict], item_id: str) -> InlineKeyboardMarkup:
    """Keyboard with answer options for a quiz question."""
    builder = InlineKeyboardBuilder()
    letters = "ABCDEFGHIJ"
    for i, opt in enumerate(options):
        letter = letters[i] if i < len(letters) else str(i + 1)
        label = _clean_option_text(opt.get("text", ""))[:60]
        builder.row(
            InlineKeyboardButton(
                text=f"{letter}. {label}",
                callback_data=f"qanswer:{item_id}:{opt['id']}",
            )
        )
    return builder.as_markup()


def quiz_skip_keyboard(item_id: str) -> InlineKeyboardMarkup:
    """Keyboard for free-text / unsupported question types."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить вопрос", callback_data=f"qskip:{item_id}"),
    )
    return builder.as_markup()


def quiz_result_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Пройти ещё задание", callback_data="assessment:list"),
        InlineKeyboardButton(text="📊 Анализ навыков", callback_data="rec:skillgap"),
    )
    return builder.as_markup()


# ── Common ────────────────────────────────────────────────────────────────────

def recommendation_keyboard(
    has_data: bool, items: list[dict] | None = None
) -> InlineKeyboardMarkup:
    """Controls shown under the recommendation list.

    For every vacancy in the displayed list we also render a 👍 / 👎 pair
    that posts an 'interested' / 'not interested' signal back to the
    recommendation service. The personalization layer picks it up on the
    next /rec/me refresh.
    """
    builder = InlineKeyboardBuilder()
    items = items or []
    for i, item in enumerate(items[:5], 1):
        vid = str(item.get("vacancy_id") or "")
        if not vid:
            continue
        builder.row(
            InlineKeyboardButton(
                text=f"#{i} 👍",
                callback_data=f"rec:like:{vid}",
            ),
            InlineKeyboardButton(
                text=f"#{i} 👎",
                callback_data=f"rec:dislike:{vid}",
            ),
        )
    if has_data:
        builder.row(InlineKeyboardButton(text="🔄 Обновить", callback_data="rec:refresh"))
        builder.row(InlineKeyboardButton(text="📊 Анализ навыков", callback_data="rec:skillgap"))
    else:
        builder.row(InlineKeyboardButton(text="🚀 Получить рекомендации", callback_data="rec:refresh"))
    return builder.as_markup()


def notification_settings_keyboard(
    email_on: bool, tg_on: bool, digest_on: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if email_on else '❌'} Email",
            callback_data="notif:toggle_email",
        ),
        InlineKeyboardButton(
            text=f"{'✅' if tg_on else '❌'} Telegram",
            callback_data="notif:toggle_telegram",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{'✅' if digest_on else '❌'} Еженедельный дайджест",
            callback_data="notif:toggle_digest",
        ),
    )
    return builder.as_markup()


def back_keyboard(callback: str = "menu:main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="← Назад", callback_data=callback))
    return builder.as_markup()


def web_link_keyboard(text: str, url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=text, url=url))
    return builder.as_markup()

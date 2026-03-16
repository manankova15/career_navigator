"""
In-memory session store for the bot.

Maps telegram_id → JWT access token (set after /login flow).
In production this should be backed by Redis with TTL matching
the JWT access token expiry.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class UserSession:
    telegram_id: int
    access_token: str
    user_id: str
    full_name: str
    first_name: str = ""  # для приветствия: «Привет, {first_name}!»
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class VacancyNavState:
    """Stores a fetched list of vacancies and the current browse position."""
    vacancies: list[dict] = field(default_factory=list)
    pos: int = 0
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class QuizState:
    """Stores progress while user is answering an assessment."""
    assessment_id: str = ""
    title: str = ""
    items: list[dict] = field(default_factory=list)
    current_idx: int = 0
    # collected answers: list of {item_id, selected_option_ids, free_text}
    answers: list[dict] = field(default_factory=list)


# Global in-memory stores
_sessions: dict[int, UserSession] = {}
_vacancy_nav: dict[int, VacancyNavState] = {}
_quiz_state: dict[int, QuizState] = {}
_lock = asyncio.Lock()


async def save_session(session: UserSession) -> None:
    async with _lock:
        _sessions[session.telegram_id] = session


async def get_session(telegram_id: int) -> UserSession | None:
    async with _lock:
        return _sessions.get(telegram_id)


async def delete_session(telegram_id: int) -> None:
    async with _lock:
        _sessions.pop(telegram_id, None)
        _vacancy_nav.pop(telegram_id, None)
        _quiz_state.pop(telegram_id, None)


async def has_session(telegram_id: int) -> bool:
    async with _lock:
        return telegram_id in _sessions


# ── Vacancy navigation ─────────────────────────────────────────────────────────

async def save_vacancy_nav(telegram_id: int, state: VacancyNavState) -> None:
    async with _lock:
        _vacancy_nav[telegram_id] = state


async def get_vacancy_nav(telegram_id: int) -> VacancyNavState | None:
    async with _lock:
        return _vacancy_nav.get(telegram_id)


# ── Quiz state ────────────────────────────────────────────────────────────────

async def save_quiz_state(telegram_id: int, state: QuizState) -> None:
    async with _lock:
        _quiz_state[telegram_id] = state


async def get_quiz_state(telegram_id: int) -> QuizState | None:
    async with _lock:
        return _quiz_state.get(telegram_id)


async def clear_quiz_state(telegram_id: int) -> None:
    async with _lock:
        _quiz_state.pop(telegram_id, None)

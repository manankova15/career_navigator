"""FSM state groups for multi-step bot dialogues."""
from aiogram.fsm.state import State, StatesGroup


class AuthStates(StatesGroup):
    waiting_email = State()
    waiting_password = State()
    waiting_register_name = State()
    waiting_register_email = State()
    waiting_register_password = State()


class VacancyStates(StatesGroup):
    waiting_search_query = State()


class NotificationStates(StatesGroup):
    pass

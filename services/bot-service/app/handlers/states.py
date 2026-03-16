"""FSM state groups for multi-step conversations."""
from aiogram.fsm.state import State, StatesGroup


class VacancySearchStates(StatesGroup):
    waiting_query = State()
    waiting_location = State()


class VacancyFilterStates(StatesGroup):
    waiting_query = State()
    waiting_location = State()


class AssessmentStates(StatesGroup):
    """State for taking an assessment question by question."""
    taking_quiz = State()

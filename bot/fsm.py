from aiogram.fsm.state import State, StatesGroup

class ReportStates(StatesGroup):
    waiting_for_question = State()

class AdminStates(StatesGroup):
    waiting_for_answer = State()


class CourseStates(StatesGroup):
    waiting_for_lang = State()
    waiting_for_slug = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_photo = State()


class BroadcastStates(StatesGroup):
    waiting_for_broadcast = State()

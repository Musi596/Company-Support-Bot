from aiogram.fsm.state import State, StatesGroup

class ReportStates(StatesGroup):
    waiting_for_question = State()

class AdminStates(StatesGroup):
    waiting_for_answer = State()

class BroadcastStates(StatesGroup):
    waiting_for_broadcast = State()
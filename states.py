from aiogram.fsm.state import StatesGroup, State

class SearchState(StatesGroup):
    form = State()
    current_input = State()
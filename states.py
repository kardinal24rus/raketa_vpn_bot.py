from aiogram.fsm.state import StatesGroup, State

class SearchState(StatesGroup):
    language_selection = State()
    form = State()
    current_input = State()
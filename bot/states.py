from aiogram.fsm.state import State, StatesGroup


class SettingsStates(StatesGroup):
    waiting_location = State()
    waiting_timezone = State()

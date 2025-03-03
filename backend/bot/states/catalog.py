from aiogram.fsm.state import State, StatesGroup


class CatalogState(StatesGroup):
    count = State()
    confirmation = State()
    delivery_location = State()

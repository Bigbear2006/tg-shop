from aiogram.fsm.state import StatesGroup, State


class CatalogState(StatesGroup):
    count = State()
    confirmation = State()
    delivery_location = State()

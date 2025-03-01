from aiogram.fsm.state import StatesGroup, State


class CatalogState(StatesGroup):
    page = State()
    category_id = State()
    product_message = State()
    product_id = State()
    count = State()
    confirmation = State()
    cart = State()
    delivery_location = State()

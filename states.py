from aiogram.fsm.state import State, StatesGroup


class AddMovieState(StatesGroup):
    waiting_code = State()
    waiting_media = State()


class SubscriptionState(StatesGroup):
    waiting_telegram_link = State()
    waiting_private_link = State()
    waiting_external_link = State()
    waiting_delete_link_id = State()


class MovieSearchState(StatesGroup):
    waiting_code = State()


class MovieDeleteState(StatesGroup):
    waiting_code = State()

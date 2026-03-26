# Foydalanuvchi holatlari (state machine)
user_states = {}

# Holatlar
IDLE = None
WAITING_MOVIE_CODE = "waiting_movie_code"
WAITING_MOVIE_TITLE = "waiting_movie_title"
WAITING_MOVIE_FILE = "waiting_movie_file"
WAITING_MOVIE_CAPTION = "waiting_movie_caption"
WAITING_MOVIE_EDIT_CODE = "waiting_movie_edit_code"
WAITING_MOVIE_EDIT_VALUE = "waiting_movie_edit_value"
WAITING_MOVIE_DELETE_CODE = "waiting_movie_delete_code"
WAITING_CHANNEL_ID = "waiting_channel_id"
WAITING_CHANNEL_NAME = "waiting_channel_name"
WAITING_CHANNEL_LINK = "waiting_channel_link"
WAITING_CHANNEL_DELETE = "waiting_channel_delete"
WAITING_ADMIN_ID = "waiting_admin_id"
WAITING_ADMIN_REMOVE_ID = "waiting_admin_remove_id"
WAITING_BROADCAST_MSG = "waiting_broadcast_msg"
WAITING_BROADCAST_CONFIRM = "waiting_broadcast_confirm"
WAITING_TARIFF_NAME = "waiting_tariff_name"
WAITING_TARIFF_DAYS = "waiting_tariff_days"
WAITING_TARIFF_PRICE = "waiting_tariff_price"
WAITING_TARIFF_EDIT_VALUE = "waiting_tariff_edit_value"
WAITING_GIVE_PREMIUM_ID = "waiting_give_premium_id"
WAITING_GIVE_PREMIUM_DAYS = "waiting_give_premium_days"


def set_state(user_id: int, state: str, data: dict = None):
    user_states[user_id] = {"state": state, "data": data or {}}


def get_state(user_id: int):
    return user_states.get(user_id, {"state": IDLE, "data": {}})


def clear_state(user_id: int):
    user_states.pop(user_id, None)


def update_data(user_id: int, **kwargs):
    if user_id not in user_states:
        user_states[user_id] = {"state": IDLE, "data": {}}
    user_states[user_id]["data"].update(kwargs)


def get_data(user_id: int):
    return user_states.get(user_id, {}).get("data", {})

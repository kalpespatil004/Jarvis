from memory.local_cache import read_cache, write_cache
from datetime import datetime

USER_KEY = "user_profile"


def get_user_profile() -> dict:
    data = read_cache()
    return data.get(USER_KEY, {})


def update_user_profile(**kwargs):
    data = read_cache()
    profile = data.get(USER_KEY, {})

    profile.update(kwargs)
    profile["updated_at"] = datetime.now().isoformat()

    data[USER_KEY] = profile
    write_cache(data)


def get_preference(key: str):
    return get_user_profile().get(key)


def set_preference(key: str, value):
    update_user_profile(**{key: value})
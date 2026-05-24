from maxapi.types import User as MaxUser


def max_user_id(user: MaxUser) -> str:
    return str(user.user_id)


def display_name(user: MaxUser) -> str:
    parts = [user.first_name]
    if user.last_name:
        parts.append(user.last_name)
    name = " ".join(parts).strip()
    return name or max_user_id(user)

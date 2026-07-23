"""Authorization policy for incoming Telegram updates."""


def is_authorized(user_id: int | None, chat_type: str, allowed_user_id: int) -> bool:
    """Return whether a request may access this Mac's camera."""
    return chat_type == "private" and user_id == allowed_user_id

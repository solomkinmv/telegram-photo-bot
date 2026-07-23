import pytest

from maccam_bot.auth import is_authorized


@pytest.mark.parametrize(
    ("user_id", "chat_type", "allowed_user_id", "expected"),
    [
        (123, "private", 123, True),
        (999, "private", 123, False),
        (None, "private", 123, False),
        (123, "group", 123, False),
        (123, "supergroup", 123, False),
        (123, "channel", 123, False),
    ],
)
def test_authorizes_only_the_allowed_user_in_a_private_chat(
    user_id: int | None,
    chat_type: str,
    allowed_user_id: int,
    expected: bool,
) -> None:
    assert is_authorized(user_id, chat_type, allowed_user_id) is expected

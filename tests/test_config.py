from collections.abc import Mapping

import pytest

from maccam_bot.config import Config, ConfigError


def valid_environment(**overrides: str) -> Mapping[str, str]:
    values = {
        "TELEGRAM_BOT_TOKEN": "123456:secret-token",
        "TELEGRAM_ALLOWED_USER_ID": "123456789",
    }
    values.update(overrides)
    return values


def test_loads_required_values_and_safe_defaults() -> None:
    config = Config.from_mapping(valid_environment())

    assert config.bot_token == "123456:secret-token"
    assert config.allowed_user_id == 123456789
    assert config.camera_device == "0"
    assert config.video_seconds == 10
    assert config.ffmpeg_path == "ffmpeg"


@pytest.mark.parametrize("key", ["TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USER_ID"])
def test_rejects_missing_required_values(key: str) -> None:
    values = dict(valid_environment())
    del values[key]

    with pytest.raises(ConfigError, match=key):
        Config.from_mapping(values)


@pytest.mark.parametrize("value", ["nope", "0", "-1"])
def test_rejects_invalid_allowed_user_id(value: str) -> None:
    with pytest.raises(ConfigError, match="TELEGRAM_ALLOWED_USER_ID"):
        Config.from_mapping(valid_environment(TELEGRAM_ALLOWED_USER_ID=value))


@pytest.mark.parametrize("value", ["0", "11", "many"])
def test_rejects_video_duration_outside_one_to_ten_seconds(value: str) -> None:
    with pytest.raises(ConfigError, match="MACCAM_VIDEO_SECONDS"):
        Config.from_mapping(valid_environment(MACCAM_VIDEO_SECONDS=value))


def test_loads_capture_overrides() -> None:
    config = Config.from_mapping(
        valid_environment(
            MACCAM_CAMERA_DEVICE="FaceTime HD Camera",
            MACCAM_VIDEO_SECONDS="8",
            MACCAM_FFMPEG_PATH="/opt/homebrew/bin/ffmpeg",
        )
    )

    assert config.camera_device == "FaceTime HD Camera"
    assert config.video_seconds == 8
    assert config.ffmpeg_path == "/opt/homebrew/bin/ffmpeg"


@pytest.mark.parametrize("key", ["MACCAM_CAMERA_DEVICE", "MACCAM_FFMPEG_PATH"])
def test_rejects_empty_capture_values(key: str) -> None:
    with pytest.raises(ConfigError, match=key):
        Config.from_mapping(valid_environment(**{key: "  "}))

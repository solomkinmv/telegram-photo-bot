"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Config:
    """Validated MacCam Bot settings."""

    bot_token: str
    allowed_user_id: int
    camera_device: str = "0"
    video_seconds: int = 10
    ffmpeg_path: str = "ffmpeg"

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> Config:
        """Create configuration from environment-like string values."""
        token = _required(values, "TELEGRAM_BOT_TOKEN")
        user_id_text = _required(values, "TELEGRAM_ALLOWED_USER_ID")

        try:
            allowed_user_id = int(user_id_text)
        except ValueError as error:
            raise ConfigError("TELEGRAM_ALLOWED_USER_ID must be a positive integer") from error
        if allowed_user_id <= 0:
            raise ConfigError("TELEGRAM_ALLOWED_USER_ID must be a positive integer")

        duration_text = values.get("MACCAM_VIDEO_SECONDS", "10").strip()
        try:
            video_seconds = int(duration_text)
        except ValueError as error:
            raise ConfigError("MACCAM_VIDEO_SECONDS must be an integer from 1 to 10") from error
        if not 1 <= video_seconds <= 10:
            raise ConfigError("MACCAM_VIDEO_SECONDS must be from 1 to 10")

        camera_device = values.get("MACCAM_CAMERA_DEVICE", "0").strip()
        if not camera_device:
            raise ConfigError("MACCAM_CAMERA_DEVICE cannot be empty")
        ffmpeg_path = values.get("MACCAM_FFMPEG_PATH", "ffmpeg").strip()
        if not ffmpeg_path:
            raise ConfigError("MACCAM_FFMPEG_PATH cannot be empty")

        return cls(
            bot_token=token,
            allowed_user_id=allowed_user_id,
            camera_device=camera_device,
            video_seconds=video_seconds,
            ffmpeg_path=ffmpeg_path,
        )


def _required(values: Mapping[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value:
        raise ConfigError(f"{key} is required")
    return value

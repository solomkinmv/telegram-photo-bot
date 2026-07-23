"""MacCam Bot command-line entry point."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ExtBot, JobQueue, filters

from maccam_bot.bot import (
    BotContext,
    BotData,
    CaptureDevice,
    ChatData,
    MacCamBot,
    UserData,
)
from maccam_bot.capture import CameraCapture
from maccam_bot.config import Config, ConfigError

MacCamApplication = Application[
    ExtBot[None],
    BotContext,
    UserData,
    ChatData,
    BotData,
    JobQueue[BotContext],
]


def ensure_ffmpeg_available(configured_path: str) -> str:
    """Resolve an executable FFmpeg path or raise a setup-focused error."""
    candidate = configured_path
    if not Path(configured_path).is_absolute():
        candidate = shutil.which(configured_path) or configured_path

    path = Path(candidate)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError(
            f"FFmpeg executable not found at {configured_path!r}. "
            "Install it with: brew install ffmpeg"
        )
    return str(path)


def build_application(config: Config, capture: CaptureDevice) -> MacCamApplication:
    """Build the Telegram polling application without making network requests."""
    handlers = MacCamBot(config.allowed_user_id, capture)
    owner_private_chat = filters.ChatType.PRIVATE & filters.User(user_id=config.allowed_user_id)
    application = cast(
        MacCamApplication,
        Application.builder().token(config.bot_token).concurrent_updates(False).build(),
    )
    application.add_handler(CommandHandler("start", handlers.start, filters=owner_private_chat))
    application.add_handler(CommandHandler("status", handlers.status, filters=owner_private_chat))
    application.add_handler(CommandHandler("photo", handlers.photo, filters=owner_private_chat))
    application.add_handler(CommandHandler("video", handlers.video, filters=owner_private_chat))
    return application


def configure_logging() -> None:
    """Configure useful logs without printing Telegram request URLs."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main() -> None:
    """Validate local setup and run MacCam Bot visibly in the foreground."""
    load_dotenv()
    try:
        config = Config.from_mapping(os.environ)
        ffmpeg_path = ensure_ffmpeg_available(config.ffmpeg_path)
    except (ConfigError, RuntimeError) as error:
        print(f"MacCam Bot setup error: {error}", file=sys.stderr)
        raise SystemExit(2) from error

    configure_logging()
    capture = CameraCapture(
        ffmpeg_path,
        config.camera_device,
        config.video_seconds,
    )
    application = build_application(config, capture)
    logging.getLogger(__name__).info("MacCam Bot is running in the foreground")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()

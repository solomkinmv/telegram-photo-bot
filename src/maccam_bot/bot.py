"""Telegram command handlers for MacCam Bot."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, Protocol

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import CallbackContext, ExtBot

from maccam_bot.auth import is_authorized
from maccam_bot.capture import CaptureError

logger = logging.getLogger(__name__)

UserData = dict[str, object]
ChatData = dict[str, object]
BotData = dict[str, object]
BotContext = CallbackContext[ExtBot[None], UserData, ChatData, BotData]


class CaptureDevice(Protocol):
    """Camera behavior needed by the Telegram handlers."""

    def photo(self, directory: Path) -> Path: ...

    def video(self, directory: Path) -> Path: ...


class MacCamBot:
    """Authorized Telegram commands backed by one macOS camera."""

    def __init__(self, allowed_user_id: int, capture: CaptureDevice) -> None:
        self._allowed_user_id = allowed_user_id
        self._capture = capture
        self.capture_lock = asyncio.Lock()

    async def start(self, update: Update, context: BotContext) -> None:
        """Explain the bot's small command surface."""
        chat_id = self._authorized_chat_id(update)
        if chat_id is None:
            return
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "MacCam Bot is ready.\n\n"
                "/photo — take a photo\n"
                "/video — record a short silent video\n"
                "/status — check whether the camera is busy"
            ),
        )

    async def status(self, update: Update, context: BotContext) -> None:
        """Report process and camera availability without exposing configuration."""
        chat_id = self._authorized_chat_id(update)
        if chat_id is None:
            return
        state = "busy." if self.capture_lock.locked() else "ready."
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"MacCam Bot is online. Camera is {state}",
        )

    async def photo(self, update: Update, context: BotContext) -> None:
        """Capture and upload a current webcam photo."""
        await self._capture_and_send(update, context, "photo", self._capture.photo)

    async def video(self, update: Update, context: BotContext) -> None:
        """Capture and upload a short silent webcam video."""
        await self._capture_and_send(update, context, "video", self._capture.video)

    async def _capture_and_send(
        self,
        update: Update,
        context: BotContext,
        kind: Literal["photo", "video"],
        capture: Callable[[Path], Path],
    ) -> None:
        chat_id = self._authorized_chat_id(update)
        if chat_id is None:
            return
        if self.capture_lock.locked():
            await context.bot.send_message(
                chat_id=chat_id,
                text="Camera is busy with another request. Try again shortly.",
            )
            return

        async with self.capture_lock:
            action = ChatAction.UPLOAD_PHOTO if kind == "photo" else ChatAction.UPLOAD_VIDEO
            await context.bot.send_chat_action(chat_id=chat_id, action=action)
            try:
                with TemporaryDirectory(prefix="maccam-") as directory:
                    media = await asyncio.to_thread(capture, Path(directory))
                    with media.open("rb") as stream:
                        if kind == "photo":
                            await context.bot.send_photo(
                                chat_id=chat_id,
                                photo=stream,
                                caption="Captured now by MacCam Bot.",
                                write_timeout=60.0,
                            )
                        else:
                            await context.bot.send_video(
                                chat_id=chat_id,
                                video=stream,
                                caption="Captured now by MacCam Bot.",
                                supports_streaming=True,
                                write_timeout=60.0,
                            )
            except CaptureError:
                logger.exception("Camera capture failed")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Camera capture failed. Check the MacCam Bot terminal for details.",
                )

    def _authorized_chat_id(self, update: Update) -> int | None:
        user = update.effective_user
        chat = update.effective_chat
        if user is None or chat is None:
            return None
        if not is_authorized(user.id, chat.type, self._allowed_user_id):
            return None
        return chat.id

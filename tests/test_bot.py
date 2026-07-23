from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import IO, cast

import pytest
from telegram import Chat, Message, Update, User

from maccam_bot.bot import BotContext, MacCamBot
from maccam_bot.capture import CaptureError


class FakeBotApi:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.actions: list[str] = []
        self.photos: list[bytes] = []
        self.videos: list[bytes] = []

    async def send_message(self, *, chat_id: int, text: str) -> object:
        self.messages.append(text)
        return object()

    async def send_chat_action(self, *, chat_id: int, action: str) -> object:
        self.actions.append(action)
        return object()

    async def send_photo(
        self,
        *,
        chat_id: int,
        photo: IO[bytes],
        caption: str,
        write_timeout: float,
    ) -> object:
        self.photos.append(photo.read())
        return object()

    async def send_video(
        self,
        *,
        chat_id: int,
        video: IO[bytes],
        caption: str,
        supports_streaming: bool,
        write_timeout: float,
    ) -> object:
        self.videos.append(video.read())
        return object()


class FakeCapture:
    def __init__(self, error: CaptureError | None = None) -> None:
        self.error = error
        self.calls: list[str] = []
        self.created_paths: list[Path] = []

    def photo(self, directory: Path) -> Path:
        return self._create(directory / "photo.jpg", "photo", b"photo-bytes")

    def video(self, directory: Path) -> Path:
        return self._create(directory / "video.mp4", "video", b"video-bytes")

    def _create(self, path: Path, kind: str, content: bytes) -> Path:
        self.calls.append(kind)
        if self.error:
            raise self.error
        path.write_bytes(content)
        self.created_paths.append(path)
        return path


def make_update(user_id: int = 123, chat_type: str = "private") -> Update:
    user = User(id=user_id, first_name="Owner", is_bot=False)
    chat = Chat(id=user_id, type=chat_type)
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text="/command",
    )
    return Update(update_id=1, message=message)


def make_context(bot: FakeBotApi) -> BotContext:
    return cast(BotContext, SimpleNamespace(bot=bot))


@pytest.mark.asyncio
async def test_start_explains_available_commands() -> None:
    api = FakeBotApi()
    handler = MacCamBot(123, FakeCapture())

    await handler.start(make_update(), make_context(api))

    assert api.messages == [
        "MacCam Bot is ready.\n\n"
        "/photo — take a photo\n"
        "/video — record a short silent video\n"
        "/status — check whether the camera is busy"
    ]


@pytest.mark.asyncio
async def test_unauthorized_request_is_ignored_without_touching_camera() -> None:
    api = FakeBotApi()
    capture = FakeCapture()
    handler = MacCamBot(123, capture)

    await handler.photo(make_update(user_id=999), make_context(api))

    assert capture.calls == []
    assert api.messages == []
    assert api.photos == []


@pytest.mark.asyncio
async def test_status_reports_ready_camera() -> None:
    api = FakeBotApi()
    handler = MacCamBot(123, FakeCapture())

    await handler.status(make_update(), make_context(api))

    assert api.messages == ["MacCam Bot is online. Camera is ready."]


@pytest.mark.asyncio
async def test_busy_camera_rejects_a_second_capture() -> None:
    api = FakeBotApi()
    capture = FakeCapture()
    handler = MacCamBot(123, capture)
    await handler.capture_lock.acquire()

    try:
        await handler.photo(make_update(), make_context(api))
    finally:
        handler.capture_lock.release()

    assert capture.calls == []
    assert api.messages == ["Camera is busy with another request. Try again shortly."]


@pytest.mark.asyncio
async def test_photo_uploads_media_then_removes_temporary_file() -> None:
    api = FakeBotApi()
    capture = FakeCapture()
    handler = MacCamBot(123, capture)

    await handler.photo(make_update(), make_context(api))

    assert api.actions == ["upload_photo"]
    assert api.photos == [b"photo-bytes"]
    assert all(not path.exists() for path in capture.created_paths)


@pytest.mark.asyncio
async def test_video_uploads_media_then_removes_temporary_file() -> None:
    api = FakeBotApi()
    capture = FakeCapture()
    handler = MacCamBot(123, capture)

    await handler.video(make_update(), make_context(api))

    assert api.actions == ["upload_video"]
    assert api.videos == [b"video-bytes"]
    assert all(not path.exists() for path in capture.created_paths)


@pytest.mark.asyncio
async def test_capture_error_returns_safe_message() -> None:
    api = FakeBotApi()
    handler = MacCamBot(123, FakeCapture(CaptureError("private FFmpeg details")))

    await handler.photo(make_update(), make_context(api))

    assert api.messages == ["Camera capture failed. Check the MacCam Bot terminal for details."]

import logging
from pathlib import Path

import pytest
from telegram.ext import CommandHandler

import maccam_bot.__main__ as main_module
from maccam_bot.__main__ import (
    build_application,
    configure_logging,
    ensure_ffmpeg_available,
    main,
)
from maccam_bot.config import Config


class UnusedCapture:
    def photo(self, directory: Path) -> Path:
        raise AssertionError("capture must not run while building the application")

    def video(self, directory: Path) -> Path:
        raise AssertionError("capture must not run while building the application")


def test_build_application_registers_commands_and_sequential_updates() -> None:
    config = Config(bot_token="123456:secret-token", allowed_user_id=123)

    application = build_application(config, UnusedCapture())

    commands = {
        command
        for handler in application.handlers[0]
        if isinstance(handler, CommandHandler)
        for command in handler.commands
    }
    assert commands == {"start", "status", "photo", "video"}
    assert application.update_processor.max_concurrent_updates == 1


def test_ensure_ffmpeg_available_accepts_an_executable(tmp_path: Path) -> None:
    executable = tmp_path / "ffmpeg"
    executable.touch(mode=0o755)

    assert ensure_ffmpeg_available(str(executable)) == str(executable)


def test_ensure_ffmpeg_available_rejects_a_missing_executable(tmp_path: Path) -> None:
    missing = tmp_path / "ffmpeg"

    with pytest.raises(RuntimeError, match="brew install ffmpeg"):
        ensure_ffmpeg_available(str(missing))


def test_main_exits_safely_when_configuration_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_module, "load_dotenv", lambda: False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_ALLOWED_USER_ID", raising=False)

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 2
    assert "TELEGRAM_BOT_TOKEN is required" in capsys.readouterr().err


def test_configure_logging_suppresses_http_request_urls() -> None:
    configure_logging()

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING

from collections.abc import Sequence
from pathlib import Path
from subprocess import CompletedProcess

import pytest

from maccam_bot.capture import (
    CameraCapture,
    CaptureError,
    build_photo_command,
    build_video_command,
)


def test_photo_command_uses_macos_avfoundation_and_camera_warmup(tmp_path: Path) -> None:
    output = tmp_path / "photo.jpg"

    command = build_photo_command("/opt/homebrew/bin/ffmpeg", "2", output)

    assert command[0] == "/opt/homebrew/bin/ffmpeg"
    assert command[command.index("-f") + 1] == "avfoundation"
    assert command[command.index("-i") + 1] == "2:none"
    assert command[command.index("-vf") + 1] == "thumbnail=30"
    assert command[-1] == str(output)


def test_video_command_creates_a_short_silent_telegram_compatible_mp4(tmp_path: Path) -> None:
    output = tmp_path / "video.mp4"

    command = build_video_command("ffmpeg", "FaceTime HD Camera", 5, output)

    assert command[command.index("-f") + 1] == "avfoundation"
    assert command[command.index("-i") + 1] == "FaceTime HD Camera:none"
    assert command[command.index("-t") + 1] == "5"
    assert command[command.index("-c:v") + 1] == "libx264"
    assert command[command.index("-pix_fmt") + 1] == "yuv420p"
    assert "-an" in command
    assert command[-1] == str(output)


@pytest.mark.parametrize("seconds", [0, 11])
def test_video_command_enforces_short_recording_limit(seconds: int, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="1 to 10"):
        build_video_command("ffmpeg", "0", seconds, tmp_path / "video.mp4")


def test_capture_returns_media_created_by_ffmpeg(tmp_path: Path) -> None:
    commands: list[Sequence[str]] = []

    def successful_runner(command: Sequence[str], **_: object) -> CompletedProcess[str]:
        commands.append(command)
        Path(command[-1]).write_bytes(b"jpeg-data")
        return CompletedProcess(command, 0, "", "")

    capture = CameraCapture("ffmpeg", "0", 5, runner=successful_runner)

    output = capture.photo(tmp_path)

    assert output == tmp_path / "photo.jpg"
    assert output.read_bytes() == b"jpeg-data"
    assert len(commands) == 1


def test_capture_translates_ffmpeg_failure(tmp_path: Path) -> None:
    def failing_runner(command: Sequence[str], **_: object) -> CompletedProcess[str]:
        return CompletedProcess(command, 1, "", "camera permission denied")

    capture = CameraCapture("ffmpeg", "0", 5, runner=failing_runner)

    with pytest.raises(CaptureError, match="camera permission denied"):
        capture.photo(tmp_path)


def test_capture_rejects_success_without_an_output_file(tmp_path: Path) -> None:
    def empty_runner(command: Sequence[str], **_: object) -> CompletedProcess[str]:
        return CompletedProcess(command, 0, "", "")

    capture = CameraCapture("ffmpeg", "0", 5, runner=empty_runner)

    with pytest.raises(CaptureError, match="did not create"):
        capture.video(tmp_path)

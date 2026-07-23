"""macOS webcam capture through FFmpeg's AVFoundation input."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

Runner = Callable[..., subprocess.CompletedProcess[str]]


class CaptureError(RuntimeError):
    """Raised when FFmpeg cannot produce requested camera media."""


def build_photo_command(ffmpeg_path: str, camera_device: str, output: Path) -> list[str]:
    """Build an FFmpeg command that warms the camera and saves one JPEG."""
    return [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "avfoundation",
        "-framerate",
        "30",
        "-i",
        f"{camera_device}:none",
        "-vf",
        "thumbnail=30",
        "-frames:v",
        "1",
        "-q:v",
        "2",
        "-y",
        str(output),
    ]


def build_video_command(
    ffmpeg_path: str,
    camera_device: str,
    seconds: int,
    output: Path,
) -> list[str]:
    """Build an FFmpeg command for a short, silent MP4 video."""
    if not 1 <= seconds <= 10:
        raise ValueError("video duration must be from 1 to 10 seconds")

    return [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "avfoundation",
        "-framerate",
        "30",
        "-i",
        f"{camera_device}:none",
        "-t",
        str(seconds),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-y",
        str(output),
    ]


class CameraCapture:
    """Capture photos and videos into a caller-owned temporary directory."""

    def __init__(
        self,
        ffmpeg_path: str,
        camera_device: str,
        video_seconds: int,
        *,
        runner: Runner = subprocess.run,
    ) -> None:
        self._ffmpeg_path = ffmpeg_path
        self._camera_device = camera_device
        self._video_seconds = video_seconds
        self._runner = runner

    def photo(self, directory: Path) -> Path:
        """Capture one JPEG into directory."""
        output = directory / "photo.jpg"
        return self._run(
            build_photo_command(self._ffmpeg_path, self._camera_device, output), output, 15
        )

    def video(self, directory: Path) -> Path:
        """Capture one short, silent MP4 into directory."""
        output = directory / "video.mp4"
        command = build_video_command(
            self._ffmpeg_path,
            self._camera_device,
            self._video_seconds,
            output,
        )
        return self._run(command, output, self._video_seconds + 15)

    def _run(self, command: list[str], output: Path, timeout: float) -> Path:
        try:
            result = self._runner(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CaptureError(f"FFmpeg could not run: {error}") from error

        if result.returncode != 0:
            detail = result.stderr.strip() or f"FFmpeg exited with status {result.returncode}"
            raise CaptureError(detail)
        if not output.is_file() or output.stat().st_size == 0:
            raise CaptureError("FFmpeg did not create a media file")
        return output

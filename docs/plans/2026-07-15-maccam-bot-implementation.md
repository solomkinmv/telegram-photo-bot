# MacCam Bot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a foreground-only macOS Telegram bot that sends an authorized user a current webcam photo or a short silent video.

**Architecture:** A Python package loads validated environment configuration, constructs FFmpeg AVFoundation capture commands, and exposes asynchronous Telegram command handlers. Authorization and capture orchestration remain separate so security behavior and cleanup can be tested without a webcam or network.

**Tech Stack:** Python 3.12+, uv, python-telegram-bot 22.x, FFmpeg AVFoundation, pytest, pytest-asyncio, Ruff, Pyright

---

### Task 1: Project metadata and configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/maccam_bot/config.py`
- Test: `tests/test_config.py`

**Steps:**
1. Add failing tests for required token/user ID, integer parsing, video duration bounds, and defaults.
2. Run `uv run pytest tests/test_config.py -v` and confirm imports or assertions fail for the missing implementation.
3. Implement an immutable `Config` dataclass and `Config.from_env()` with explicit validation errors.
4. Re-run the focused test and confirm it passes.
5. Run Ruff and Pyright against the new files.

### Task 2: Authorization policy

**Files:**
- Create: `src/maccam_bot/auth.py`
- Test: `tests/test_auth.py`

**Steps:**
1. Add failing table-driven tests proving only the configured user in a private chat is authorized.
2. Run the focused test and confirm the missing function failure.
3. Implement `is_authorized(user_id, chat_type, allowed_user_id)` as a small pure function.
4. Re-run the focused test and confirm it passes.

### Task 3: macOS camera capture

**Files:**
- Create: `src/maccam_bot/capture.py`
- Test: `tests/test_capture.py`

**Steps:**
1. Add failing tests for photo and video FFmpeg arguments, the ten-second maximum, subprocess error translation, and temporary-file cleanup.
2. Run the focused test and verify expected failures.
3. Implement command builders using `-f avfoundation`, a camera-only input, JPEG output, and H.264/yuv420p MP4 output.
4. Implement an injectable subprocess runner and `CameraCapture` methods that validate output existence.
5. Re-run the focused tests and refactor only while green.

### Task 4: Telegram command handlers

**Files:**
- Create: `src/maccam_bot/bot.py`
- Test: `tests/test_bot.py`

**Steps:**
1. Add failing async tests for unauthorized requests, status, busy capture rejection, successful uploads, error replies, and cleanup.
2. Run the focused test and verify it fails for missing behavior.
3. Implement a `MacCamBot` handler object with a single `asyncio.Lock`, injected capture component, and private-chat authorization guard.
4. Upload open file objects with explicit Telegram media timeouts, then leave the temporary directory scope so media is deleted.
5. Re-run the focused tests and confirm all branches pass.

### Task 5: Application entry point and documentation

**Files:**
- Create: `src/maccam_bot/__init__.py`
- Create: `src/maccam_bot/__main__.py`
- Create: `README.md`

**Steps:**
1. Add a failing test for application construction and registered command names.
2. Implement `build_application()` with sequential update processing and long polling.
3. Add startup logging, FFmpeg validation, and clear configuration errors.
4. Document BotFather setup, user-ID discovery, camera discovery, permissions, commands, and foreground operation.
5. Run the full test, lint, and type-check suite.

### Task 6: Verification and Git handoff

**Files:**
- Verify all project files.

**Steps:**
1. Run `uv sync --all-groups` from a clean dependency state.
2. Run `uv run pytest -v` and confirm zero failures.
3. Run `uv run ruff check .` and `uv run ruff format --check .`.
4. Run `uv run pyright` and confirm zero errors.
5. Run the CLI with intentionally missing configuration and verify it exits with a safe, useful error without contacting Telegram or the camera.
6. Inspect `git diff --check`, secret patterns, and `git status`.
7. Commit with a conventional commit message.

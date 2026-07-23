# MacCam Bot

MacCam Bot is a private Telegram bot that takes an on-demand photo or short
silent video from a Mac webcam and sends it to one authorized Telegram user.

## Motivation

The original motivation was to check in on a dog while away from the Mac:
request a current photo or 10-second video only when needed, instead of running
a continuous camera stream.

This is not a GPS tracker. It can only show what is currently visible to the
configured webcam.

## Privacy and security model

- Commands are accepted only from one numeric Telegram user ID in a private
  chat.
- Requests from other users, groups, channels, or missing user identities are
  ignored.
- The bot uses Telegram long polling and does not open an inbound port.
- The microphone is never opened.
- Recording is never continuous; videos are limited to 1–10 seconds.
- Only one capture can run at a time.
- Media is written to a private temporary directory and deleted after the
  upload attempt.
- HTTP request logging is suppressed so Telegram request URLs do not print the
  bot token.
- There is no launch agent, webhook, motion detector, or additional cloud
  storage.

Captured media is uploaded to Telegram and therefore leaves the Mac. Review
Telegram's privacy and retention model before using this for sensitive spaces.
The Mac's green camera indicator turns on whenever its webcam is active.

Use this only on a Mac and in a location where you are authorized to operate
the camera.

## Requirements

- macOS
- [uv](https://docs.astral.sh/uv/)
- [FFmpeg](https://ffmpeg.org/) with AVFoundation support
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your numeric Telegram user ID

Install the local tools with Homebrew:

```bash
brew install uv ffmpeg
```

## Setup

### 1. Create a Telegram bot

1. Open [@BotFather](https://t.me/BotFather).
2. Send `/newbot`.
3. Choose a display name and an available username ending in `bot`.
4. Copy the generated token and treat it like a password.

To obtain your numeric Telegram user ID, use a user-information bot such as
`@userinfobot`. The value must be your personal user ID, not the new bot's ID
or username.

### 2. Clone and configure the project

```bash
git clone https://github.com/your-account/telegram-photo-bot.git
cd telegram-photo-bot
uv sync --all-groups
cp .env.example .env
chmod 600 .env
```

Edit `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=replace-with-token-from-botfather
TELEGRAM_ALLOWED_USER_ID=replace-with-your-numeric-user-id
MACCAM_CAMERA_DEVICE=0
MACCAM_VIDEO_SECONDS=10
MACCAM_FFMPEG_PATH=ffmpeg
```

`.env` is ignored by Git. Never commit or paste a real token into source code,
logs, screenshots, issues, or chat messages. If a token is disclosed, revoke
it with BotFather and create a replacement.

### 3. Select the webcam

List AVFoundation devices:

```bash
ffmpeg -hide_banner -f avfoundation -list_devices true -i ""
```

FFmpeg exits with an error after printing the list; that is normal. Find the
camera under `AVFoundation video devices` and use its index for
`MACCAM_CAMERA_DEVICE`. The built-in FaceTime camera is commonly `0`, but the
actual list is authoritative.

### 4. Run the bot

```bash
uv run maccam-bot
```

Keep that terminal open and stop the bot with `Ctrl-C`. The first `/photo` or
`/video` request should trigger the normal macOS camera permission prompt.
Allow access for the terminal application that launched MacCam Bot.

To keep it running in a detachable Zellij session:

```bash
zellij --session maccam
uv run maccam-bot
```

Detach with Zellij's session shortcut and later reconnect with:

```bash
zellij attach maccam
```

MacCam Bot does not launch automatically at login.

## Commands

- `/start` — show available commands
- `/status` — report whether the camera is ready or busy
- `/photo` — take and send a current JPEG photo
- `/video` — record and send a silent 10-second MP4

## How it works

1. The bot receives Telegram updates through long polling.
2. It verifies both the sender's numeric user ID and private-chat type.
3. It runs FFmpeg with macOS AVFoundation in a worker thread.
4. It uploads the resulting JPEG or MP4 to the authorized chat.
5. It closes the file and removes the temporary directory.

## Troubleshooting

### Camera capture failed

Read the FFmpeg details in the MacCam Bot terminal. Common causes are:

- Camera permission was denied for the terminal application.
- Another application is using the camera.
- `MACCAM_CAMERA_DEVICE` does not match the current AVFoundation device list.

After changing camera permission, quit and reopen the terminal application.

### The bot does not respond

- Confirm `uv run maccam-bot` is still running.
- Open a private chat with the bot and send `/start`.
- Verify that `TELEGRAM_ALLOWED_USER_ID` is your numeric user ID.
- Confirm no other process is polling with the same bot token.

## Development

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

The design and implementation plan are in [`docs/plans`](docs/plans).

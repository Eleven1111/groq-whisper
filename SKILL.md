---
name: groq-whisper
description: Transcribe local audio files with Groq Whisper Turbo via the OpenAI-compatible audio API. Best for Telegram voice notes (.ogg/.opus) and common audio files (.mp3/.wav/.m4a/.flac), with optimized defaults for Chinese and English speech.
user-invocable: true
metadata: {"clawdbot":{"emoji":"🎙️","requires":{"bins":["python3"],"optional_bins":["ffmpeg","openclaw","crontab"]}}}
---

# Groq Whisper

A small, deterministic skill for two jobs:

1. **Transcribe local audio files** with Groq Whisper (`scripts/transcribe.py`)
2. **Run a Telegram/Discord voice bridge** for voice→text and text→voice (`scripts/groq_voice_bridge.py`)

This skill is best when you want predictable CLI behavior instead of an agent improvising the API call.

## Prepare API key

Store the Groq API key at `~/.config/groq/api_key` with strict permissions:

```bash
mkdir -p ~/.config/groq
printf '%s' 'YOUR_GROQ_API_KEY' > ~/.config/groq/api_key
chmod 600 ~/.config/groq/api_key
```

Do **not** store the key inside workspace or repo files.

You can also save the key interactively:

```bash
python3 skills/groq-whisper/scripts/transcribe.py --set-api-key
```

## 1) Local transcription CLI

Basic usage:

```bash
python3 skills/groq-whisper/scripts/transcribe.py --file /path/to/audio.ogg
```

Default behavior:
- endpoint: `https://api.groq.com/openai/v1/audio/transcriptions`
- model: `whisper-large-v3-turbo`
- language: `auto`
- prompt: `請用簡體中文輸出，不要包含任何繁體字。`
- response_format: `text`

Useful options:
- `--model <name>`: switch model if Groq changes availability
- `--language <code>`: `auto | zh | en`
- `--prompt <text>`: override the transcription style hint
- `--api-key-file <path>`: use a non-default key file
- `--response-format <fmt>`: `text | json | verbose_json | srt | vtt`
- `--set-api-key`: securely prompt for and save the API key

Example:

```bash
python3 skills/groq-whisper/scripts/transcribe.py \
  --file /path/to/meeting.m4a \
  --language zh \
  --prompt '请输出纯文本，不要加时间戳。'
```

## 2) Telegram / Discord voice bridge

Script: `skills/groq-whisper/scripts/groq_voice_bridge.py`

What it does:
- **Voice message → text**: download audio, transcribe with Groq Whisper, reply with transcript
- **Text with prefix → voice**: if message starts with `语音回复：`, `語音回覆：`, `voice reply:`, or `tts:`, generate TTS audio and reply back
- **Cleanup**: always uses temporary directories and removes audio artifacts after each job

### Configure

1. Copy the example config:
   ```bash
   cp skills/groq-whisper/config/groq_voice_bridge.example.json skills/groq-whisper/config/groq_voice_bridge.json
   ```
2. Fill in the fields you actually use:
   - `telegram.bot_token`
   - `telegram.chat_ids`
   - optionally `discord.bot_user_id` and `discord.channel_ids`
3. Enable only the platforms you want

### Run once manually

```bash
python3 skills/groq-whisper/scripts/groq_voice_bridge.py --config skills/groq-whisper/config/groq_voice_bridge.json
```

### Install cron

This installs a once-per-minute cron entry and logs to `~/.openclaw/workspace/logs/groq_voice_bridge.log`:

```bash
bash skills/groq-whisper/scripts/install_voice_bridge_cron.sh
```

## Audio compatibility

Telegram voice notes are usually OGG/Opus and work directly.

If you need manual conversion, use ffmpeg:

```bash
ffmpeg -i input.ogg -ar 16000 -ac 1 output.wav
```

## Notes

- The transcription CLI is intentionally dependency-light and uses Python stdlib HTTP calls.
- The voice bridge assumes `openclaw` is available in runtime PATH for message send/read operations.
- For unattended bridge mode, keep the config file out of version control if it contains real bot credentials.

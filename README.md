# groq-whisper

Groq-powered speech tools for OpenClaw: **transcribe local audio** and **run a Telegram/Discord voice bridge** with minimal dependencies and predictable CLI behavior.

## What it does

- **Transcribe local audio** with Groq Whisper
- **Reply to voice messages with text transcripts**
- **Turn prefixed text into TTS audio replies**
- **Run unattended with cron**

Good fit for:
- Telegram voice notes
- Chinese / English audio transcription
- lightweight automation instead of a bloated speech stack

---

## Features

### 1. Local transcription
Transcribe local audio files such as:

- `.ogg`
- `.opus`
- `.mp3`
- `.wav`
- `.m4a`
- `.flac`

Default model:
- `whisper-large-v3-turbo`

Typical use cases:
- Telegram voice notes
- Meeting recordings
- Quick Chinese/English transcription
- Converting audio into plain text for later summarization

### 2. Voice bridge
Run a small polling bridge that:

- downloads incoming Telegram/Discord audio
- transcribes it with Groq Whisper
- replies with text
- converts prefixed text messages into TTS audio replies

Supported TTS triggers:
- `语音回复：`
- `語音回覆：`
- `voice reply:`
- `tts:`

---

## Requirements

Required:
- `python3`

Optional but recommended:
- `ffmpeg`
- `openclaw`
- `crontab`

---

## Setup

### Save your Groq API key

```bash
mkdir -p ~/.config/groq
printf '%s' 'YOUR_GROQ_API_KEY' > ~/.config/groq/api_key
chmod 600 ~/.config/groq/api_key
```

Or save it interactively:

```bash
python3 scripts/transcribe.py --set-api-key
```

Do not commit API keys into the repo.

---

## Usage

### Transcribe a local audio file

```bash
python3 scripts/transcribe.py --file /path/to/audio.ogg
```

Example:

```bash
python3 scripts/transcribe.py \
  --file /path/to/interview.m4a \
  --language zh \
  --prompt '请输出纯文本，不要加时间戳。'
```

### Common options

```bash
--model <name>
--language auto|zh|en
--prompt <text>
--response-format text|json|verbose_json|srt|vtt
--api-key-file <path>
--set-api-key
```

### Friendly wrapper

For simple shell integration, you can also use:

```bash
bash scripts/openclaw_audio_cli.sh /path/to/audio.ogg
```

This wrapper returns friendly Chinese error text instead of raw Python stack traces.

---

## Voice bridge setup

### 1. Copy config template

```bash
cp config/groq_voice_bridge.example.json config/groq_voice_bridge.json
```

### 2. Edit the config

Fill in what you need:

- `telegram.bot_token`
- `telegram.chat_ids`
- `discord.bot_user_id`
- `discord.channel_ids`

Enable only the platform you actually use.

### 3. Run once manually

```bash
python3 scripts/groq_voice_bridge.py --config config/groq_voice_bridge.json
```

### 4. Install cron

```bash
bash scripts/install_voice_bridge_cron.sh
```

This creates a once-per-minute cron job and writes logs to:

```bash
~/.openclaw/workspace/logs/groq_voice_bridge.log
```

---

## How the bridge works

### Voice → Text
When a supported audio message arrives:

1. download audio
2. transcribe via Groq Whisper
3. reply to the original message with transcript text

### Text → Voice
When a text message starts with one of the supported prefixes:

- `语音回复：`
- `語音回覆：`
- `voice reply:`
- `tts:`

the bridge sends the remaining text to Groq TTS and replies with generated audio.

### Cleanup
Temporary audio files are written to temporary directories and deleted after each job.

---

## Audio compatibility

Telegram voice notes are usually OGG/Opus and work directly.

If conversion is needed:

```bash
ffmpeg -i input.ogg -ar 16000 -ac 1 output.wav
```

---

## Known limitations

- The bridge depends on `openclaw` CLI availability for send/read operations.
- Long-running polling via cron is simple and robust, but not fancy.
- Real credentials should stay out of version control.
- Current defaults are optimized for Chinese/English speech workflows, not every language under the sun.

---

## Why this exists

Because “just transcribe this audio” should not require a bloated stack, six wrappers, and a prayer.

This repo keeps the path short:
- one API key
- one script for transcription
- one script for bridge automation
- predictable behavior

# groq-whisper

> Groq-powered speech tools for OpenClaw: local transcription plus a lightweight Telegram or Discord voice bridge.
>
> 基于 Groq 的 OpenClaw 语音工具：既可做本地音频转写，也可作为轻量的 Telegram / Discord 语音桥接器。

---

## English

### What this repo does

- Transcribe local audio files with Groq Whisper
- Reply to Telegram or Discord voice messages with text transcripts
- Turn prefixed text into TTS audio replies
- Run unattended with cron or macOS LaunchAgent

Good fit for:
- Telegram voice notes
- Chinese and English speech transcription
- Small automation flows with predictable CLI behavior

### Features

#### 1. Local transcription
Supported audio formats include:
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
- Quick Chinese or English transcription
- Converting audio into plain text for summarization

#### 2. Voice bridge
The bridge can:
- download incoming Telegram or Discord audio
- transcribe it with Groq Whisper
- reply with text
- convert prefixed text messages into TTS audio replies

Supported TTS prefixes:
- `语音回复：`
- `語音回覆：`
- `voice reply:`
- `tts:`

### Requirements

Required:
- `python3`

Optional but recommended:
- `ffmpeg`
- `openclaw`
- `crontab`
- `watchdog` for `scripts/audio_watcher.py`

### Setup

#### Save your Groq API key

```bash
mkdir -p ~/.config/groq
printf %s YOUR_GROQ_API_KEY > ~/.config/groq/api_key
chmod 600 ~/.config/groq/api_key
```

Or save it interactively:

```bash
python3 scripts/transcribe.py --set-api-key
```

You can also use an environment variable for ephemeral runs:

```bash
export GROQ_API_KEY=YOUR_GROQ_API_KEY
```

Do not commit API keys into the repo.

### Usage

#### Transcribe a local audio file

```bash
python3 scripts/transcribe.py --file /path/to/audio.ogg
```

Example:

```bash
python3 scripts/transcribe.py \
  --file /path/to/interview.m4a \
  --language zh \
  --prompt "请输出纯文本，不要加时间戳。"
```

#### Common options

```bash
--model <name>
--language auto|zh|en
--prompt <text>
--response-format text|json|verbose_json|srt|vtt
--api-key-file <path>
--set-api-key
```

#### Friendly wrapper

```bash
bash scripts/openclaw_audio_cli.sh /path/to/audio.ogg
```

This wrapper returns readable Chinese error text instead of raw Python stack traces.

### Voice bridge setup

#### 1. Copy config template

```bash
cp config/groq_voice_bridge.example.json config/groq_voice_bridge.json
```

#### 2. Edit the config

The example config ships with all platforms disabled. Enable only what you actually use.

Common fields:
- `telegram.bot_token`
- `telegram.chat_ids`
- `discord.bot_user_id`
- `discord.channel_ids`

#### 3. Run once manually

```bash
python3 scripts/groq_voice_bridge.py --config config/groq_voice_bridge.json
```

Recommended single-run wrapper for unattended use:

```bash
bash scripts/run_voice_bridge_once.sh
```

This wrapper bootstraps logs, creates the config from the example if missing, and uses a best effort lock to avoid overlapping runs.

#### 4. Install cron

```bash
bash scripts/install_voice_bridge_cron.sh
```

Logs are written to:

```bash
~/.openclaw/workspace/logs/groq_voice_bridge.log
```

#### 5. Install macOS LaunchAgent

```bash
bash scripts/install_voice_bridge_launchd.sh
```

This installs a LaunchAgent that runs the same single-run wrapper every 60 seconds.

### Local watcher

For fast local folder-based ingestion, you can run the watcher with configurable paths:

```bash
bash scripts/run_audio_watcher.sh
```

Useful environment variables:
- `WATCH_DIR`
- `LOG_FILE`
- `PROCESSED_FILE`
- `TRANSCRIBE_SCRIPT`

The watcher logs metadata only and avoids writing full transcript text into its log file.

### How the bridge works

#### Voice to text
When a supported audio message arrives:
1. download audio
2. transcribe via Groq Whisper
3. reply to the original message with transcript text

#### Text to voice
When a text message starts with a supported prefix, the bridge sends the remaining text to Groq TTS and replies with generated audio.

#### Cleanup
Temporary audio files are written to temporary directories and deleted after each job.

### Audio compatibility

Telegram voice notes are usually OGG or Opus and work directly.

If conversion is needed:

```bash
ffmpeg -i input.ogg -ar 16000 -ac 1 output.wav
```

### Operational notes

- State is written atomically to reduce corruption risk on crashes.
- The bridge keeps a bounded recent-message cache to reduce duplicate processing on restart or retry.
- `scripts/run_voice_bridge_once.sh` is the recommended unattended entrypoint for cron or launchd.
- `scripts/audio_watcher.py` supports fast local inbound-folder watching.

### Validation

```bash
python3 -m py_compile scripts/transcribe.py scripts/groq_voice_bridge.py scripts/audio_watcher.py
bash -n scripts/*.sh
```

---

## 中文

### 这个仓库做什么

- 用 Groq Whisper 转写本地音频文件
- 把 Telegram / Discord 里的语音消息回复为文字转写结果
- 把带前缀的文字消息转成 TTS 语音回复
- 用 cron 或 macOS LaunchAgent 无人值守运行

适合场景：
- Telegram 语音消息
- 中英文语音转写
- 需要稳定 CLI 行为的小型自动化流程

### 功能

#### 1. 本地转写
支持的音频格式包括：
- `.ogg`
- `.opus`
- `.mp3`
- `.wav`
- `.m4a`
- `.flac`

默认模型：
- `whisper-large-v3-turbo`

典型用途：
- Telegram 语音消息
- 会议录音
- 快速中英文转写
- 先转纯文本，再做后续总结

#### 2. 语音桥接
桥接脚本可以：
- 下载 Telegram / Discord 的音频消息
- 用 Groq Whisper 转写
- 直接回帖文字结果
- 把带前缀的文本消息转成 TTS 音频回复

支持的 TTS 前缀：
- `语音回复：`
- `語音回覆：`
- `voice reply:`
- `tts:`

### 依赖

必需：
- `python3`

可选但推荐：
- `ffmpeg`
- `openclaw`
- `crontab`
- `watchdog`，供 `scripts/audio_watcher.py` 使用

### 配置

#### 保存 Groq API Key

```bash
mkdir -p ~/.config/groq
printf %s YOUR_GROQ_API_KEY > ~/.config/groq/api_key
chmod 600 ~/.config/groq/api_key
```

也可以交互式保存：

```bash
python3 scripts/transcribe.py --set-api-key
```

临时执行也可以用环境变量：

```bash
export GROQ_API_KEY=YOUR_GROQ_API_KEY
```

不要把 API Key 提交到仓库。

### 用法

#### 转写本地音频

```bash
python3 scripts/transcribe.py --file /path/to/audio.ogg
```

示例：

```bash
python3 scripts/transcribe.py \
  --file /path/to/interview.m4a \
  --language zh \
  --prompt "请输出纯文本，不要加时间戳。"
```

#### 常用参数

```bash
--model <name>
--language auto|zh|en
--prompt <text>
--response-format text|json|verbose_json|srt|vtt
--api-key-file <path>
--set-api-key
```

#### 友好包装脚本

```bash
bash scripts/openclaw_audio_cli.sh /path/to/audio.ogg
```

这个包装脚本会输出更友好的中文错误信息，而不是原始 Python stack trace。

### 语音桥接配置

#### 1. 复制配置模板

```bash
cp config/groq_voice_bridge.example.json config/groq_voice_bridge.json
```

#### 2. 编辑配置

示例配置默认关闭所有平台，只开启你真正需要的平台即可。

常见字段：
- `telegram.bot_token`
- `telegram.chat_ids`
- `discord.bot_user_id`
- `discord.channel_ids`

#### 3. 先手动跑一次

```bash
python3 scripts/groq_voice_bridge.py --config config/groq_voice_bridge.json
```

更推荐用于无人值守的单次运行包装脚本：

```bash
bash scripts/run_voice_bridge_once.sh
```

它会自动准备日志目录、在缺少配置时从示例生成，并尽量避免重叠运行。

#### 4. 安装 cron

```bash
bash scripts/install_voice_bridge_cron.sh
```

日志位置：

```bash
~/.openclaw/workspace/logs/groq_voice_bridge.log
```

#### 5. 安装 macOS LaunchAgent

```bash
bash scripts/install_voice_bridge_launchd.sh
```

它会每 60 秒运行一次同样的单次包装脚本。

### 本地 watcher

如果你希望监听本地目录并自动转写，可以运行：

```bash
bash scripts/run_audio_watcher.sh
```

可配置环境变量：
- `WATCH_DIR`
- `LOG_FILE`
- `PROCESSED_FILE`
- `TRANSCRIBE_SCRIPT`

watcher 只记录元信息，不把完整转写内容写进日志，减少隐私泄露风险。

### 桥接流程

#### 语音转文字
收到支持的音频消息后：
1. 下载音频
2. 调用 Groq Whisper 转写
3. 回复文字结果

#### 文字转语音
当文本以前缀开头时，桥接脚本会把剩余内容发送给 Groq TTS，再回复生成的音频。

#### 清理
临时音频文件统一写入临时目录，并在任务结束后删除。

### 音频兼容性

Telegram 语音消息通常是 OGG / Opus，可直接处理。

如需手动转换：

```bash
ffmpeg -i input.ogg -ar 16000 -ac 1 output.wav
```

### 运维说明

- 状态文件使用原子写入，降低异常中断时的损坏风险。
- Bridge 使用有界 recent-message 缓存，减少重启或重试时重复处理。
- `scripts/run_voice_bridge_once.sh` 是更推荐的 cron / launchd 入口。
- `scripts/audio_watcher.py` 支持本地入站目录快速监听。

### 验证

```bash
python3 -m py_compile scripts/transcribe.py scripts/groq_voice_bridge.py scripts/audio_watcher.py
bash -n scripts/*.sh
```

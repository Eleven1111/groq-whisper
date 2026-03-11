#!/usr/bin/env bash
set -u

MEDIA_PATH="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSCRIBE_PY="$SCRIPT_DIR/transcribe.py"

if [[ -z "$MEDIA_PATH" ]]; then
  echo "【语音转写失败】未收到音频文件路径。"
  exit 0
fi

if [[ ! -f "$MEDIA_PATH" ]]; then
  echo "【语音转写失败】音频文件不存在或不可读。"
  exit 0
fi

# Run Groq Whisper script; capture stderr for friendly fallback.
OUT=""
ERR_FILE="$(mktemp)"
trap 'rm -f "$ERR_FILE"' EXIT

if OUT="$(python3 "$TRANSCRIBE_PY" --file "$MEDIA_PATH" 2>"$ERR_FILE")"; then
  OUT="$(printf '%s' "$OUT" | sed 's/^\s\+//;s/\s\+$//')"
  if [[ -n "$OUT" ]]; then
    printf '%s\n' "$OUT"
  else
    echo "【语音转写失败】模型返回了空文本，请重试一次。"
  fi
  exit 0
fi

ERR_MSG="$(tail -n 1 "$ERR_FILE" | sed 's/^\s*//;s/\s*$//')"
if [[ -z "$ERR_MSG" ]]; then
  ERR_MSG="调用转写服务失败（网络/API/格式可能异常）"
fi

echo "【语音转写失败】$ERR_MSG"
exit 0

#!/usr/bin/env bash
set -euo pipefail

ROOT="${HOME}/.openclaw/workspace"
SCRIPT="${ROOT}/skills/groq-whisper/scripts/groq_voice_bridge.py"
CFG="${ROOT}/skills/groq-whisper/config/groq_voice_bridge.json"
LOG="${ROOT}/logs/groq_voice_bridge.log"

mkdir -p "${ROOT}/logs"

if [[ ! -f "${CFG}" ]]; then
  cp "${ROOT}/skills/groq-whisper/config/groq_voice_bridge.example.json" "${CFG}"
  echo "Created ${CFG}; please fill telegram.bot_token/chat_ids before enabling Telegram."
fi

CRON="* * * * * /usr/bin/python3 ${SCRIPT} --config ${CFG} >> ${LOG} 2>&1"
( crontab -l 2>/dev/null | grep -v 'groq_voice_bridge.py' ; echo "$CRON" ) | crontab -

echo "Installed cron job:"
crontab -l | grep 'groq_voice_bridge.py' || true

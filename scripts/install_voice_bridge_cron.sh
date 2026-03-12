#!/usr/bin/env bash
set -euo pipefail

ROOT="${HOME}/.openclaw/workspace"
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="${SKILL_ROOT}/scripts/run_voice_bridge_once.sh"
CFG="${GROQ_VOICE_BRIDGE_CONFIG:-${SKILL_ROOT}/config/groq_voice_bridge.json}"
LOG="${ROOT}/logs/groq_voice_bridge.log"

mkdir -p "${ROOT}/logs"

if [[ ! -f "${CFG}" ]]; then
  cp "${SKILL_ROOT}/config/groq_voice_bridge.example.json" "${CFG}"
  echo "Created ${CFG}; please fill credentials and enable the platforms you use."
fi

CRON="* * * * * GROQ_VOICE_BRIDGE_CONFIG=${CFG} ${RUNNER} >> ${LOG} 2>&1"
( crontab -l 2>/dev/null | grep -v "run_voice_bridge_once.sh" | grep -v "groq_voice_bridge.py" ; echo "$CRON" ) | crontab -

echo "Installed cron job:"
crontab -l | grep "run_voice_bridge_once.sh" || true

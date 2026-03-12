#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BRIDGE_PY="${ROOT}/scripts/groq_voice_bridge.py"
CFG="${GROQ_VOICE_BRIDGE_CONFIG:-${ROOT}/config/groq_voice_bridge.json}"
STATE="${GROQ_VOICE_BRIDGE_STATE:-${HOME}/.openclaw/groq_voice_bridge_state.json}"
LOG_DIR="${HOME}/.openclaw/workspace/logs"
LOCK_DIR="${TMPDIR:-/tmp}/groq_voice_bridge.lock"

mkdir -p "${LOG_DIR}" "$(dirname "${STATE}")"

if [[ ! -f "${CFG}" ]]; then
  cp "${ROOT}/config/groq_voice_bridge.example.json" "${CFG}"
  echo "Created ${CFG}; fill credentials and enable the platforms you use." >&2
fi

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  echo "groq_voice_bridge: another run appears active; skipping overlap." >&2
  exit 0
fi
trap "rmdir \"${LOCK_DIR}\" >/dev/null 2>&1 || true" EXIT

exec "${PYTHON_BIN}" "${BRIDGE_PY}" --config "${CFG}" --state "${STATE}" "$@"

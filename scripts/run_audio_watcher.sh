#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
WATCH_DIR="${WATCH_DIR:-${HOME}/.openclaw/media/inbound}"
LOG_FILE="${LOG_FILE:-${HOME}/.openclaw/workspace/logs/audio_watcher.log}"
PROCESSED_FILE="${PROCESSED_FILE:-${HOME}/.openclaw/workspace/logs/processed_audio.txt}"
TRANSCRIBE_SCRIPT="${TRANSCRIBE_SCRIPT:-${ROOT}/scripts/transcribe.py}"

mkdir -p "${WATCH_DIR}" "$(dirname "${LOG_FILE}")" "$(dirname "${PROCESSED_FILE}")"

export WATCH_DIR LOG_FILE PROCESSED_FILE TRANSCRIBE_SCRIPT
exec "${PYTHON_BIN}" "${ROOT}/scripts/audio_watcher.py" "$@"

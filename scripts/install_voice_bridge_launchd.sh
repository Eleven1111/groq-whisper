#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUNNER="${ROOT}/scripts/run_voice_bridge_once.sh"
CFG="${GROQ_VOICE_BRIDGE_CONFIG:-${ROOT}/config/groq_voice_bridge.json}"
PLIST_DIR="${HOME}/Library/LaunchAgents"
PLIST_PATH="${PLIST_DIR}/com.openclaw.groq-voice-bridge.plist"
LOG_DIR="${HOME}/.openclaw/workspace/logs"
STDOUT_LOG="${LOG_DIR}/groq_voice_bridge.launchd.log"
STDERR_LOG="${LOG_DIR}/groq_voice_bridge.launchd.err.log"
LABEL="com.openclaw.groq-voice-bridge"

mkdir -p "${PLIST_DIR}" "${LOG_DIR}"

if [[ ! -f "${CFG}" ]]; then
  cp "${ROOT}/config/groq_voice_bridge.example.json" "${CFG}"
  echo "Created ${CFG}; fill credentials and enable the platforms you use." >&2
fi

cat > "${PLIST_PATH}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${RUNNER}</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>GROQ_VOICE_BRIDGE_CONFIG</key>
    <string>${CFG}</string>
  </dict>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>StartInterval</key>
  <integer>60</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${STDOUT_LOG}</string>
  <key>StandardErrorPath</key>
  <string>${STDERR_LOG}</string>
</dict>
</plist>
EOF

launchctl unload "${PLIST_PATH}" >/dev/null 2>&1 || true
launchctl load "${PLIST_PATH}"

echo "Installed LaunchAgent: ${PLIST_PATH}"
echo "Control commands:"
echo "  launchctl unload ${PLIST_PATH}"
echo "  launchctl load ${PLIST_PATH}"

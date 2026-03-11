# Changelog

## v0.1.0

Initial public release of `groq-whisper`.

### Added
- Local audio transcription script using Groq OpenAI-compatible audio API
- Secure API key storage flow via `--set-api-key`
- Telegram / Discord voice bridge
- Text-to-speech reply flow with configurable prefixes
- Cron installer for unattended bridge execution
- Example JSON config for bridge setup

### Improved
- Clearer skill metadata for discovery and publication
- Better public-facing documentation for setup and usage
- Consistent explanation of dependencies and optional tools

### Fixed
- Documentation/default-value mismatch between skill docs and actual transcription script behavior
- Clarified actual default language and prompt behavior used by `transcribe.py`

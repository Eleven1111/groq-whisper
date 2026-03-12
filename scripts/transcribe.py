#!/usr/bin/env python3
"""Groq Whisper transcription CLI (OpenAI-compatible audio API)."""

from __future__ import annotations

import argparse
import getpass
import json
import mimetypes
import os
import stat
import sys
import uuid
from pathlib import Path
from urllib import error, request

DEFAULT_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"
DEFAULT_MODEL = "whisper-large-v3-turbo"
DEFAULT_LANGUAGE = "auto"
DEFAULT_PROMPT = "請用簡體中文輸出，不要包含任何繁體字。"
DEFAULT_RESPONSE_FORMAT = "text"
DEFAULT_KEY_FILE = os.path.expanduser("~/.config/groq/api_key")
ENV_API_KEY = "GROQ_API_KEY"


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def read_api_key(path: str) -> str:
    env_key = os.getenv(ENV_API_KEY, "").strip()
    if env_key:
        return env_key

    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(
            f"API key file not found: {p}. Create it first, set {ENV_API_KEY}, or use --set-api-key."
        )

    try:
        mode = stat.S_IMODE(p.stat().st_mode)
        if mode & 0o077:
            eprint(f"Warning: API key file permissions are too broad ({oct(mode)}); expected 0o600.")
    except OSError:
        pass

    key = p.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError(f"API key file is empty: {p}")
    return key


def write_api_key(path: str) -> None:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    key = getpass.getpass("Enter Groq API key (input hidden): ").strip()
    if not key:
        raise ValueError("Empty key; aborting.")
    p.write_text(key, encoding="utf-8")
    os.chmod(p, 0o600)
    print(f"Saved API key to {p} with mode 600")


def build_multipart(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----OpenClawGroq{uuid.uuid4().hex}"
    crlf = "\r\n"
    parts: list[bytes] = []

    for name, value in fields.items():
        parts.append(f"--{boundary}{crlf}".encode())
        parts.append(
            (
                f'Content-Disposition: form-data; name="{name}"{crlf}{crlf}{value}{crlf}'
            ).encode()
        )

    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    filename = file_path.name
    file_bytes = file_path.read_bytes()

    parts.append(f"--{boundary}{crlf}".encode())
    parts.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"{crlf}'
            f"Content-Type: {mime}{crlf}{crlf}"
        ).encode()
    )
    parts.append(file_bytes)
    parts.append(crlf.encode())
    parts.append(f"--{boundary}--{crlf}".encode())

    return b"".join(parts), boundary


def transcribe(
    api_key: str,
    file_path: Path,
    endpoint: str,
    model: str,
    language: str,
    prompt: str,
    response_format: str,
) -> str:
    fields = {
        "model": model,
        "response_format": response_format,
    }
    if language and language.lower() != "auto":
        fields["language"] = language
    if prompt:
        fields["prompt"] = prompt

    body, boundary = build_multipart(fields, "file", file_path)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "OpenClaw/1.0",
    }

    req = request.Request(endpoint, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        err_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {err_text}") from None
    except error.URLError as exc:
        raise RuntimeError(f"Request failed: {exc.reason}") from None

    if response_format == "json":
        try:
            data = json.loads(raw)
            return str(data.get("text", "")).strip() or raw
        except json.JSONDecodeError:
            return raw

    return raw.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe local audio via Groq Whisper (OpenAI-compatible API)."
    )
    parser.add_argument("--file", help="Path to local audio file (.ogg/.opus/.mp3/.wav/...)" )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Transcription endpoint URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name (default: whisper-large-v3-turbo)")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Language code: auto|zh|en (default: auto)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt hint for transcription style")
    parser.add_argument(
        "--response-format",
        default=DEFAULT_RESPONSE_FORMAT,
        choices=["text", "json", "verbose_json", "srt", "vtt"],
        help="API response format (default: text)",
    )
    parser.add_argument("--api-key-file", default=DEFAULT_KEY_FILE, help=f"Path to Groq API key file (ignored if {ENV_API_KEY} is set)")
    parser.add_argument(
        "--set-api-key",
        action="store_true",
        help="Securely input and save API key to --api-key-file (chmod 600)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.set_api_key:
            write_api_key(args.api_key_file)
            if not args.file:
                return 0

        if not args.file:
            eprint("Error: --file is required unless only using --set-api-key")
            return 2

        path = Path(args.file).expanduser()
        if not path.exists() or not path.is_file():
            eprint(f"Error: file not found: {path}")
            return 2

        api_key = read_api_key(args.api_key_file)

        text = transcribe(
            api_key=api_key,
            file_path=path,
            endpoint=args.endpoint,
            model=args.model,
            language=args.language,
            prompt=args.prompt,
            response_format=args.response_format,
        )
        print(text)
        return 0
    except KeyboardInterrupt:
        eprint("Interrupted.")
        return 130
    except Exception as exc:
        eprint(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

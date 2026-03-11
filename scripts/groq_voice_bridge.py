#!/usr/bin/env python3
"""Groq voice bridge for Telegram/Discord.

Features:
- Voice message -> STT (whisper-large-v3-turbo) -> text reply
- Text message with prefix "语音回复：" / "voice reply:" -> TTS audio reply
- Telegram polling (Bot API) and Discord polling (openclaw message read)
- Temp audio files are always cleaned up
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib import parse, request

ROOT = Path(__file__).resolve().parents[3]
TRANSCRIBE_PY = ROOT / "skills/groq-whisper/scripts/transcribe.py"
DEFAULT_CFG = ROOT / "skills/groq-whisper/config/groq_voice_bridge.json"
DEFAULT_STATE = ROOT / ".openclaw/groq_voice_bridge_state.json"
KEY_FILE = Path("~/.config/groq/api_key").expanduser()

STT_MODEL = "whisper-large-v3-turbo"
STT_PROMPT = "Only transcribe Chinese or English speech; output plain text only."
TTS_ENDPOINT = "https://api.groq.com/openai/v1/audio/speech"
TTS_MODEL = "playai-tts"
TTS_VOICE = "Fritz-PlayAI"

TTS_PREFIXES = ("语音回复：", "語音回覆：", "voice reply:", "tts:")


def eprint(*a: object) -> None:
    print(*a, file=sys.stderr)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def read_key() -> str:
    if not KEY_FILE.exists():
        raise FileNotFoundError(f"Groq key file missing: {KEY_FILE}")
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError("Groq key file is empty")
    return key


def openclaw_send(channel: str, target: str, message: str | None = None, reply_to: str | None = None, media: str | None = None) -> None:
    cmd = ["openclaw", "message", "send", "--channel", channel, "--target", target]
    if message:
        cmd += ["--message", message]
    if reply_to:
        cmd += ["--reply-to", reply_to]
    if media:
        cmd += ["--media", media]
    rc, out, err = run(cmd)
    if rc != 0:
        raise RuntimeError(err or out or "openclaw message send failed")


def stt_transcribe(audio_path: Path) -> str:
    cmd = [
        "python3",
        str(TRANSCRIBE_PY),
        "--file",
        str(audio_path),
        "--model",
        STT_MODEL,
        "--language",
        "auto",
        "--prompt",
        STT_PROMPT,
        "--response-format",
        "text",
    ]
    rc, out, err = run(cmd)
    if rc != 0:
        raise RuntimeError(err or "transcribe failed")
    txt = out.strip()
    if not txt:
        raise RuntimeError("empty transcription")
    return txt


def tts_groq_to_file(text: str, out_path: Path, voice: str = TTS_VOICE, model: str = TTS_MODEL) -> None:
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": "wav",
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {read_key()}",
        "Content-Type": "application/json",
    }
    req = request.Request(TTS_ENDPOINT, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=180) as resp:
            audio = resp.read()
    except Exception as exc:
        raise RuntimeError(f"TTS request failed: {exc}")
    out_path.write_bytes(audio)


def extract_tts_text(content: str) -> str | None:
    low = content.lower().strip()
    for p in TTS_PREFIXES:
        if low.startswith(p.lower()):
            return content[len(p):].strip()
    return None


def tg_api(token: str, method: str, params: dict[str, Any] | None = None) -> Any:
    q = parse.urlencode(params or {})
    url = f"https://api.telegram.org/bot{token}/{method}"
    if q:
        url += f"?{q}"
    with request.urlopen(url, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API {method} failed")
    return data["result"]


def tg_download(token: str, file_id: str, out_path: Path) -> None:
    info = tg_api(token, "getFile", {"file_id": file_id})
    p = info.get("file_path")
    if not p:
        raise RuntimeError("Telegram getFile returned no file_path")
    url = f"https://api.telegram.org/file/bot{token}/{p}"
    with request.urlopen(url, timeout=180) as resp:
        out_path.write_bytes(resp.read())


def handle_voice(channel: str, target: str, reply_to: str, download_fn) -> None:
    with tempfile.TemporaryDirectory(prefix="groq-voice-") as td:
        td_path = Path(td)
        src = td_path / "input.audio"
        download_fn(src)
        text = stt_transcribe(src)
        openclaw_send(channel, target, message=f"📝 转写结果：\n{text}", reply_to=reply_to)


def handle_tts(channel: str, target: str, reply_to: str, text: str, cfg: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="groq-tts-") as td:
        out = Path(td) / "tts.wav"
        tts_groq_to_file(text=text, out_path=out, voice=cfg.get("tts_voice", TTS_VOICE), model=cfg.get("tts_model", TTS_MODEL))
        openclaw_send(channel, target, media=str(out), reply_to=reply_to)


def process_telegram(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    tg = cfg.get("telegram") or {}
    if not tg.get("enabled"):
        return
    token = tg.get("bot_token") or os.getenv("OPENCLAW_TELEGRAM_BOT_TOKEN", "")
    chat_ids = set(str(x) for x in (tg.get("chat_ids") or []))
    if not token or not chat_ids:
        return

    offset = int(state.get("telegram_offset", 0))
    updates = tg_api(token, "getUpdates", {"offset": offset, "timeout": 45, "allowed_updates": json.dumps(["message"])})
    for up in updates:
        state["telegram_offset"] = max(int(state.get("telegram_offset", 0)), int(up.get("update_id", 0)) + 1)
        msg = up.get("message") or {}
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        if chat_id not in chat_ids:
            continue
        mid = str(msg.get("message_id", ""))
        text = (msg.get("text") or "").strip()

        # voice -> stt
        file_id = None
        if isinstance(msg.get("voice"), dict):
            file_id = msg["voice"].get("file_id")
        elif isinstance(msg.get("audio"), dict):
            file_id = msg["audio"].get("file_id")
        elif isinstance(msg.get("document"), dict) and str(msg["document"].get("mime_type", "")).startswith("audio/"):
            file_id = msg["document"].get("file_id")
        if file_id:
            try:
                handle_voice("telegram", chat_id, mid, lambda p: tg_download(token, file_id, p))
            except Exception as exc:
                openclaw_send("telegram", chat_id, message=f"❌ 转写失败（Telegram 语音下载/识别）：{exc}", reply_to=mid)
            continue

        # text -> tts
        tts_text = extract_tts_text(text)
        if tts_text:
            try:
                handle_tts("telegram", chat_id, mid, tts_text, cfg)
            except Exception as exc:
                openclaw_send("telegram", chat_id, message=f"❌ 语音合成失败（TTS）：{exc}", reply_to=mid)


def process_discord(cfg: dict[str, Any], state: dict[str, Any]) -> None:
    ds = cfg.get("discord") or {}
    if not ds.get("enabled"):
        return
    channels = [str(x) for x in (ds.get("channel_ids") or [])]
    bot_id = str(ds.get("bot_user_id") or "")

    for ch in channels:
        after = state.get("discord_after", {}).get(ch)
        cmd = ["openclaw", "message", "read", "--channel", "discord", "--target", ch, "--limit", "20", "--json"]
        if after:
            cmd += ["--after", str(after)]
        rc, out, err = run(cmd)
        if rc != 0:
            eprint(f"discord read failed for {ch}: {err or out}")
            continue
        try:
            payload = json.loads(out)
            messages = (((payload or {}).get("payload") or {}).get("messages") or [])
        except Exception:
            messages = []
        messages = sorted(messages, key=lambda x: int(x.get("id", 0)))

        for m in messages:
            mid = str(m.get("id", ""))
            state.setdefault("discord_after", {})[ch] = mid
            author = m.get("author") or {}
            if author.get("bot") or (bot_id and str(author.get("id", "")) == bot_id):
                continue
            content = (m.get("content") or "").strip()
            atts = m.get("attachments") or []

            audio_url = None
            for a in atts:
                ctype = str(a.get("content_type") or "")
                name = str(a.get("filename") or "")
                if ctype.startswith("audio/") or re.search(r"\.(ogg|opus|mp3|wav|m4a|flac)$", name, re.I):
                    audio_url = a.get("url")
                    break
            if audio_url:
                try:
                    handle_voice("discord", ch, mid, lambda p, u=audio_url: p.write_bytes(request.urlopen(u, timeout=180).read()))
                except Exception as exc:
                    openclaw_send("discord", ch, message=f"❌ 转写失败（Discord 音频下载/识别）：{exc}", reply_to=mid)
                continue

            tts_text = extract_tts_text(content)
            if tts_text:
                try:
                    handle_tts("discord", ch, mid, tts_text, cfg)
                except Exception as exc:
                    openclaw_send("discord", ch, message=f"❌ 语音合成失败（TTS）：{exc}", reply_to=mid)


def main() -> int:
    ap = argparse.ArgumentParser(description="Groq voice bridge (Telegram + Discord)")
    ap.add_argument("--config", default=str(DEFAULT_CFG), help="Path to config JSON")
    ap.add_argument("--state", default=str(DEFAULT_STATE), help="Path to state JSON")
    args = ap.parse_args()

    cfg = load_json(Path(args.config), {})
    state = load_json(Path(args.state), {})

    try:
        process_telegram(cfg, state)
        process_discord(cfg, state)
    finally:
        save_json(Path(args.state), state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

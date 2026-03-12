#!/usr/bin/env python3
"""Audio watcher - 实时监听 inbound 目录，新音频自动转录"""

import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = "/Users/eleven/.openclaw/media/inbound"
LOG_FILE = "/Users/eleven/.openclaw/workspace/logs/audio_watcher.log"
PROCESSED_FILE = "/Users/eleven/.openclaw/workspace/logs/processed_audio.txt"
TRANSCRIBE_SCRIPT = "/Users/eleven/.openclaw/workspace/skills/groq-whisper/scripts/transcribe.py"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def is_processed(filepath):
    try:
        with open(PROCESSED_FILE, "r") as f:
            return filepath in f.read()
    except:
        return False

def mark_processed(filepath):
    with open(PROCESSED_FILE, "a") as f:
        f.write(f"{filepath}\n")

def transcribe(filepath):
    log(f"Transcribing: {filepath}")
    env = os.environ.copy()
    env["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"
    try:
        result = subprocess.run(
            ["python3", TRANSCRIBE_SCRIPT, "--file", filepath],
            capture_output=True, text=True, timeout=60, env=env
        )
        if result.returncode == 0:
            log(f"Success: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            log(f"Error: {result.stderr}")
            return None
    except Exception as e:
        log(f"Exception: {e}")
        return None

class AudioHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".ogg"):
            time.sleep(0.5)  # 等待文件写完
            if not is_processed(event.src_path):
                transcribe(event.src_path)
                mark_processed(event.src_path)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(PROCESSED_FILE), exist_ok=True)
    
    log("Audio watcher (watchdog) started")
    
    event_handler = AudioHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
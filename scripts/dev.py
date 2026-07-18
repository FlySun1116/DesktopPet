#!/usr/bin/env python3
"""Development runner: restart the desktop pet when watched files change.

Usage (from project root, with venv activated):

    python scripts/dev.py

Stop with Ctrl+C.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("缺少 watchdog。请先安装：pip install watchdog", file=sys.stderr)
    raise SystemExit(1) from None


WATCH_SUFFIXES = {".py", ".json"}
IGNORE_DIR_NAMES = {".git", ".venv", "__pycache__", "dist", "build", ".pytest_cache", "artwork", "images", "reports"}


class RestartHandler(FileSystemEventHandler):
    def __init__(self, on_change, debounce_s: float = 0.6) -> None:
        super().__init__()
        self._on_change = on_change
        self._debounce_s = debounce_s
        self._last_fire = 0.0

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(getattr(event, "dest_path", None) or event.src_path)
        if path.suffix.lower() not in WATCH_SUFFIXES:
            return
        if any(part in IGNORE_DIR_NAMES for part in path.parts):
            return
        now = time.monotonic()
        if now - self._last_fire < self._debounce_s:
            return
        self._last_fire = now
        print(f"\n[dev] 检测到变更: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
        self._on_change()


class DevRunner:
    def __init__(self, python: str, args: list[str]) -> None:
        self.python = python
        self.args = args
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        self.stop()
        env = os.environ.copy()
        env.setdefault("PYTHONUNBUFFERED", "1")
        print(f"[dev] 启动: {self.python} {' '.join(self.args)}")
        self.process = subprocess.Popen(
            [self.python, *self.args],
            cwd=ROOT,
            env=env,
            start_new_session=True,
        )

    def stop(self) -> None:
        if self.process is None:
            return
        proc = self.process
        self.process = None
        if proc.poll() is not None:
            return
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
            proc.wait(timeout=2)

    def restart(self) -> None:
        print("[dev] 正在重启桌宠…")
        self.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch project files and restart the desktop pet.")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter used to launch main.py (default: current interpreter)",
    )
    parser.add_argument(
        "--debounce",
        type=float,
        default=0.6,
        help="Seconds to coalesce rapid file events (default: 0.6)",
    )
    return parser.parse_args()


def main() -> int:
    options = parse_args()
    runner = DevRunner(options.python, ["main.py"])
    handler = RestartHandler(runner.restart, debounce_s=options.debounce)
    observer = Observer()

    watch_roots = [ROOT / "app", ROOT / "config", ROOT / "main.py"]
    for target in watch_roots:
        if target.is_file():
            observer.schedule(handler, str(target.parent), recursive=False)
        elif target.is_dir():
            observer.schedule(handler, str(target), recursive=True)

    def _shutdown(*_args) -> None:
        print("\n[dev] 退出")
        observer.stop()
        runner.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    observer.start()
    runner.start()
    print("[dev] 监听 app/、config/、main.py — 保存后自动重启。Ctrl+C 退出。")

    try:
        while observer.is_alive():
            if runner.process is not None and runner.process.poll() is not None:
                code = runner.process.returncode
                print(f"[dev] 桌宠进程已退出 (code={code})，等待文件变更后重启…")
                runner.process = None
            time.sleep(0.4)
    finally:
        observer.stop()
        observer.join(timeout=2)
        runner.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

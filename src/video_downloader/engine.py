"""Run bounded download jobs and send plain events to the interface."""

import json
import os
import signal
import subprocess
import threading
import urllib.parse
import urllib.request
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .core import DownloadOptions, build_command, is_retryable, source_type
from .tools import ToolPaths, no_window_flag


@dataclass(frozen=True)
class DownloadEvent:
    job: int
    kind: str
    value: object


def process_kwargs() -> dict:
    if os.name == "nt":
        return {"creationflags": no_window_flag() | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def terminate_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=no_window_flag(),
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            proc.kill()
        proc.wait(timeout=5)


def resolve_yandex_public_url(url: str) -> str:
    endpoint = "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key="
    request = urllib.request.Request(
        endpoint + urllib.parse.quote(url, safe=""), headers={"User-Agent": "VideoDownloader/0.1"}
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.loads(response.read(1024 * 1024).decode("utf-8"))
    direct = data.get("href", "")
    parsed = urllib.parse.urlparse(direct)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(
            "Yandex Disk did not return a public file link. Folder links are not supported."
        )
    return direct


class DownloadEngine:
    def __init__(
        self, options: DownloadOptions, tools: ToolPaths, emit: Callable[[DownloadEvent], None]
    ):
        self.options = options
        self.tools = tools
        self.emit = emit
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.processes = {}

    @property
    def active_count(self) -> int:
        with self.lock:
            return len(self.processes)

    def send(self, index: int, kind: str, value: object) -> None:
        self.emit(DownloadEvent(index, kind, value))

    def cancel(self) -> None:
        self.stop.set()
        with self.lock:
            processes = list(self.processes.values())
        for process in processes:
            terminate_tree(process)

    def command(self, url: str, folder: Path, fragments: int) -> list[str]:
        cmd = build_command(url, folder, self.options, self.tools, fragments)
        if source_type(url) == "Yandex Disk":
            cmd[-1] = resolve_yandex_public_url(url)
        return cmd

    def attempt(self, index: int, url: str, folder: Path, fragments: int) -> tuple[int, str]:
        process = None
        lines = deque(maxlen=8)
        try:
            cmd = self.command(url, folder, fragments)
            if self.stop.is_set():
                return -1, "Cancelled"
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                **process_kwargs(),
            )
            with self.lock:
                self.processes[index] = process
            if self.stop.is_set():
                terminate_tree(process)
            for raw in process.stdout:
                line = raw.strip()
                if not line:
                    continue
                if line.startswith("__PROGRESS__"):
                    parts = line[len("__PROGRESS__") :].split("|")
                    try:
                        progress = max(0.0, min(99.0, float(parts[0].replace("%", ""))))
                        self.send(index, "progress", progress)
                    except ValueError:
                        pass
                    if len(parts) > 1 and parts[1].strip() not in ("", "NA"):
                        self.send(index, "speed", parts[1].strip())
                elif line.startswith("__PROCESSING__") or line.startswith(
                    ("[Merger]", "[ExtractAudio]", "[VideoConvertor]")
                ):
                    self.send(index, "state", "processing")
                else:
                    lines.append(line)
                if self.stop.is_set():
                    terminate_tree(process)
                    break
            return process.wait(), "\n".join(lines)[-1200:]
        except Exception as error:
            return 999, str(error)
        finally:
            if process is not None:
                terminate_tree(process)
                if process.stdout is not None:
                    process.stdout.close()
            with self.lock:
                self.processes.pop(index, None)

    def download_one(self, index: int, url: str, folder: Path, fragments: int) -> tuple[bool, str]:
        if self.stop.is_set():
            self.send(index, "state", "cancelled")
            return False, "Cancelled"
        self.send(index, "state", "running")
        self.send(index, "log", f"Starting {source_type(url)}: {url}")
        code, error = self.attempt(index, url, folder, fragments)
        if code and not self.stop.is_set() and is_retryable(error):
            self.send(index, "log", "Retrying a temporary network error with one fragment.")
            if not self.stop.wait(2):
                code, error = self.attempt(index, url, folder, 1)
        if self.stop.is_set():
            self.send(index, "state", "cancelled")
            return False, "Cancelled"
        if code == 0:
            self.send(index, "progress", 100.0)
            self.send(index, "state", "completed")
            self.send(index, "log", f"Saved: {url}")
            return True, ""
        error = error or "The download failed. Check the Activity log and update yt-dlp."
        self.send(index, "state", "failed")
        self.send(index, "log", f"Failed: {url}\n{error}")
        return False, error

    def run(self, urls: list[str], folder: Path) -> None:
        completed = 0
        failed = []
        try:
            folder.mkdir(parents=True, exist_ok=True)
            workers = min(self.options.workers, max(1, len(urls)))
            fragments = max(1, 16 // workers)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                pending = {
                    pool.submit(self.download_one, index, url, folder, fragments): url
                    for index, url in enumerate(urls)
                }
                for future in as_completed(pending):
                    try:
                        ok, error = future.result()
                    except Exception as exc:
                        ok, error = False, str(exc)
                    if ok:
                        completed += 1
                    elif error != "Cancelled":
                        failed.append((pending[future], error))
                    self.send(-1, "counts", {"completed": completed, "failed": len(failed)})
            if failed:
                report = "\n\n".join(url + "\n" + error for url, error in failed)
                (folder / "failed_downloads.txt").write_text(report + "\n", encoding="utf-8")
        except Exception as error:
            failed.append(("Batch", str(error)))
            self.send(-1, "log", str(error))
        finally:
            self.send(
                -1,
                "batch_done",
                {
                    "completed": completed,
                    "failed": failed,
                    "cancelled": self.stop.is_set(),
                    "folder": str(folder),
                },
            )

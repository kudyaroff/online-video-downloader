"""Find separately installed tools without changing the system PATH."""

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolPaths:
    ytdlp: str | None
    ffmpeg: str | None
    ffprobe: str | None
    deno: str | None


def no_window_flag() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def find_tool(name: str, extra_dirs=()) -> str | None:
    executable = name + ".exe" if os.name == "nt" else name
    home = Path.home()
    local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    app_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
    directories = [
        *map(Path, extra_dirs),
        app_dir / "tools",
        app_dir,
        local / "Microsoft/WinGet/Links",
        home / ".deno/bin",
        home / "scoop/shims",
    ]
    for directory in directories:
        candidate = directory / executable
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        packages = local / "Microsoft/WinGet/Packages"
        patterns = {
            "yt-dlp": "yt-dlp.yt-dlp_*",
            "ffmpeg": "Gyan.FFmpeg_*",
            "ffprobe": "Gyan.FFmpeg_*",
            "deno": "DenoLand.Deno_*",
        }
        for package in packages.glob(patterns.get(name, "__unknown__")):
            try:
                for candidate in package.rglob(executable):
                    if candidate.is_file():
                        return str(candidate)
            except OSError:
                continue
    return None


def find_tools() -> ToolPaths:
    ffmpeg = find_tool("ffmpeg")
    siblings = [Path(ffmpeg).parent] if ffmpeg else []
    return ToolPaths(find_tool("yt-dlp"), ffmpeg, find_tool("ffprobe", siblings), find_tool("deno"))


def diagnostics() -> dict:
    paths = find_tools()
    result = {"python": sys.version.split()[0]}
    for name, path in vars(paths).items():
        version = None
        if path:
            try:
                flag = "-version" if name in ("ffmpeg", "ffprobe") else "--version"
                completed = subprocess.run(
                    [path, flag],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                    creationflags=no_window_flag(),
                )
                version = (completed.stdout or completed.stderr).splitlines()[0]
            except (OSError, subprocess.TimeoutExpired, IndexError) as error:
                version = str(error)
        result[name] = {"path": path, "version": version}
    return result

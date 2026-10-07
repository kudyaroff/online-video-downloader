"""Download choices and command arguments, independent of the interface."""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .tools import ToolPaths

QUALITY_OPTIONS = [
    "1080p · Windows compatible",
    "Best · Windows compatible",
    "2160p / 4K · source codec",
    "1440p · source codec",
    "720p · Windows compatible",
    "480p · Windows compatible",
    "360p · Windows compatible",
    "Best source · may need codecs",
    "Audio only · M4A",
]


@dataclass(frozen=True)
class DownloadOptions:
    quality: str = QUALITY_OPTIONS[0]
    workers: int = 4
    cookies: str = "None"

    def __post_init__(self):
        if self.quality not in QUALITY_OPTIONS:
            raise ValueError("Choose a listed quality option.")
        if self.cookies not in ("None", "Chrome", "Edge", "Firefox"):
            raise ValueError("Choose a supported browser or None.")
        object.__setattr__(self, "workers", max(1, min(4, int(self.workers))))


def parse_urls(text: str) -> list[str]:
    result = []
    for value in re.findall(r'https?://[^\s<>"\']+', text):
        value = value.rstrip(".,);]")
        try:
            valid = urlparse(value).hostname is not None
        except ValueError:
            valid = False
        if valid and value not in result:
            result.append(value)
    return result


def source_type(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return "Other"
    groups = {
        "YouTube": ("youtube.com", "youtu.be"),
        "Instagram": ("instagram.com",),
        "Yandex Disk": ("disk.yandex.ru", "disk.yandex.com", "disk.yandex.kz", "yadi.sk"),
        "Google Drive": ("drive.google.com", "docs.google.com", "drive.usercontent.google.com"),
    }
    for name, domains in groups.items():
        if any(host == domain or host.endswith("." + domain) for domain in domains):
            return name
    return "Other"


def select_format(source: str, quality: str) -> str:
    if quality not in QUALITY_OPTIONS:
        raise ValueError("Unknown quality option.")
    if quality == "Audio only · M4A":
        return "ba/b"
    if source in ("Google Drive", "Yandex Disk"):
        return "source/best"
    if quality == "Best source · may need codecs":
        return "bv+ba/b"
    match = re.match(r"(\d+)p", quality)
    limit = f"[height<={match.group(1)}]" if match else ""
    if "Windows compatible" in quality:
        return (
            f"bv*{limit}[vcodec^=avc1]+ba[acodec^=mp4a]"
            f"/b{limit}[vcodec^=avc1][acodec^=mp4a]/b{limit}/bv{limit}+ba"
        )
    return f"bv{limit}+ba/b{limit}"


def build_command(
    url: str, folder: Path, options: DownloadOptions, tools: ToolPaths, fragments: int
) -> list[str]:
    if not tools.ytdlp:
        raise ValueError("yt-dlp is missing. See the Windows installation guide.")
    source = source_type(url)
    cmd = [
        tools.ytdlp,
        "--ignore-config",
        "--no-plugin-dirs",
        "--newline",
        "--no-playlist",
        "--windows-filenames",
        "--continue",
        "--retries",
        "3",
        "--fragment-retries",
        "3",
        "--retry-sleep",
        "fragment:2",
        "--socket-timeout",
        "30",
        "-N",
        str(fragments),
        "--progress-template",
        "download:__PROGRESS__%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s",
        "--progress-template",
        "postprocess:__PROCESSING__%(progress.status)s",
        "-P",
        str(folder),
        "-o",
        "%(title).180B [%(id)s].%(ext)s",
        "-f",
        select_format(source, options.quality),
    ]
    if tools.ffmpeg:
        cmd += ["--ffmpeg-location", tools.ffmpeg]
    if tools.deno and source == "YouTube":
        cmd += ["--js-runtimes", f"deno:{tools.deno}"]
    if options.quality == "Audio only · M4A":
        cmd += ["-x", "--audio-format", "m4a", "--audio-quality", "0"]
    elif source not in ("Google Drive", "Yandex Disk"):
        cmd += ["--merge-output-format", "mp4"]
        if "Windows compatible" in options.quality:
            cmd += ["--recode-video", "mp4"]
    if options.cookies != "None":
        cmd += ["--cookies-from-browser", options.cookies.lower()]
    return cmd + ["--", url]


def is_retryable(error: str) -> bool:
    error = error.lower()
    if any(
        word in error
        for word in (
            "403",
            "401",
            "404",
            "unsupported url",
            "format is not available",
            "private video",
            "login",
            "sign in",
            "permission denied",
        )
    ):
        return False
    return bool(re.search(r"http (?:error )?(?:429|50[0234])", error)) or any(
        word in error
        for word in (
            "timed out",
            "timeout",
            "connection reset",
            "connection aborted",
            "temporarily unavailable",
            "network is unreachable",
        )
    )

"""Keep preferences in the user's application data folder."""

import json
import os
from pathlib import Path

from .core import QUALITY_OPTIONS, DownloadOptions


def settings_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "VideoDownloader/settings.json"


def load_settings(path: Path | None = None) -> dict:
    defaults = {
        "folder": str(Path.home() / "Videos"),
        "quality": QUALITY_OPTIONS[0],
        "workers": 4,
        "cookies": "None",
    }
    try:
        saved = json.loads((path or settings_path()).read_text(encoding="utf-8"))
        if not isinstance(saved, dict):
            return defaults
        for key in defaults:
            if isinstance(saved.get(key), type(defaults[key])):
                defaults[key] = saved[key]
        opts = DownloadOptions(defaults["quality"], defaults["workers"], defaults["cookies"])
        defaults.update(quality=opts.quality, workers=opts.workers, cookies=opts.cookies)
    except (OSError, ValueError, TypeError):
        defaults.update(quality=QUALITY_OPTIONS[0], workers=4, cookies="None")
    return defaults


def save_settings(values: dict, path: Path | None = None) -> None:
    path = path or settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)

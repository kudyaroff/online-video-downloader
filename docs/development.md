# Development

Python 3.11+ with Tcl/Tk is required. Windows is the supported desktop target. The portable core is also tested on Linux; a Linux desktop build is not provided.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,build]"
.\.venv\Scripts\python.exe -m video_downloader
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests run.py packaging
```

Diagnostics: `python -m video_downloader --diagnose`. It reports **local** paths and tool versions. Redact private paths before sharing it. The root launcher also works with `python run.py` without installing the package.

## Layout

- `core.py`: choices, URLs and command arguments.
- `tools.py`: tool paths and diagnostics.
- `settings.py`: local preferences.
- `engine.py`: subprocesses, bounded jobs, cancellation and progress events.
- `desktop.py`: Tkinter widgets and UI event handling.

UI widgets belong to the main thread. Workers receive a frozen settings object and send events through a queue. External commands use an argument list, not a shell. yt-dlp's user config and plugin directories are ignored so hidden local options do not change this app's behavior.

## Build on Windows

Use 64-bit Python 3.13.15 for the audited release build. Source use supports Python 3.11+. Build dependencies are pinned in `pyproject.toml`. The build checks tests and lint before packaging:

```powershell
.\scripts\build-windows.ps1
```

Output: `dist/Video-Downloader-Windows-x64.zip` and its `.sha256` file. The ZIP includes our app, installation instructions and full runtime license texts. The build is not bit-for-bit reproducible or digitally signed. It does not include external yt-dlp/FFmpeg/Deno binaries.

The build writes an inventory in `licenses/bundled-files.txt` and runtime versions in `licenses/runtime.json`. Check these and the notices when changing Python, PyInstaller or dependencies. License collection uses pinned upstream texts and the actual Python distribution's license, and fails if expected local license files are missing.

## Tests

Core and engine tests use temporary files and small real subprocesses. No third-party video downloads are required. GUI tests run when a display is available. pytest uses Python stream capture because Windows Tcl file loading can conflict with file-descriptor capture when repeatedly creating interpreters.

## Preparing a release

1. Update the version in `pyproject.toml` and `src/video_downloader/__init__.py`; add the changelog entry.
2. Build, check the extracted ZIP, verify the checksum and review licenses.
3. After the repository is published, a matching `vX.Y.Z` tag triggers the release workflow. It validates the version, reruns checks, builds the Windows ZIP and attaches it to a GitHub Release.

No release or remote CI run is claimed until it actually exists. Do not include local logs, media, cookies, internal planning notes or credentials in a release.

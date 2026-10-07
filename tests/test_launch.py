import subprocess
import sys
import tomllib
from pathlib import Path


def test_package_import_from_project_folder():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c", "from video_downloader import __version__; print(__version__)"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    expected = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    assert result.stdout.strip() == expected

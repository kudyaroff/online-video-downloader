"""Run from an extracted source folder, or use python -m video_downloader."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from video_downloader.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()

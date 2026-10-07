"""Source launch, version information and local diagnostics."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def main():
    parser = argparse.ArgumentParser(description="Video Downloader")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--diagnose", action="store_true", help="Print local tool paths and versions"
    )
    parser.add_argument("--diagnostics-file", type=Path, help="Write local diagnostics as JSON")
    parser.add_argument("--smoke-test", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.diagnose or args.diagnostics_file:
        from .tools import diagnostics

        report = json.dumps(diagnostics(), ensure_ascii=False, indent=2)
        if args.diagnostics_file:
            args.diagnostics_file.write_text(report + "\n", encoding="utf-8")
        if args.diagnose and sys.stdout is not None:
            print(report)
        return
    from .desktop import VideoDownloader

    app = VideoDownloader()
    if args.smoke_test:
        app.update()
        report = {
            "version": __version__,
            "title": app.title(),
            "width": app.winfo_width(),
            "tools": vars(app.tools),
            "ui_ready": app.download_btn.winfo_exists() == 1,
        }
        args.smoke_test.write_text(json.dumps(report, indent=2), encoding="utf-8")
        app.destroy()
        return
    app.mainloop()


if __name__ == "__main__":
    main()

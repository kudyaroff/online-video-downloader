# Third-party notices

The MIT license in this repository covers our original code and documentation. It does not replace the licenses of the software listed here. No external downloader binaries are included in our Windows ZIP.

## Included in the Windows build

- **Python** and its incorporated software. The build copies the complete `LICENSE.txt` from the actual Python distribution into `licenses/Python.txt`. Python itself is not modified.
- **Tcl/Tk**. Tkinter uses these libraries for the interface. Their license texts are included in the `licenses` folder.
- **OpenSSL**, **zlib**, **Expat**, and other components used by the bundled Python runtime. Their notices are included in the build. See `licenses/runtime.json` for the actual versions and `licenses/bundled-files.txt` for the file inventory.
- **PyInstaller bootloader and runtime hooks**. PyInstaller's [license exception](https://pyinstaller.org/en/stable/license.html) permits distribution of generated applications under a chosen license while preserving dependency obligations. The build includes PyInstaller's COPYING text and any separately collected package license texts.

The build keeps full license texts in `licenses/`. Build tools such as pytest and Ruff are development dependencies and are not intentionally bundled. If you change the build, review its new contents and licenses before distributing it.

## Installed separately

| Tool | License information | Source |
| --- | --- | --- |
| yt-dlp | Source package: Unlicense. Some bundled executables include GPLv3+ components. Use the license information for the exact release you install. | [Licensing](https://github.com/yt-dlp/yt-dlp#licensing) |
| FFmpeg / ffprobe | LGPL 2.1+ or GPL, depending on build configuration and included components. | [Legal information](https://ffmpeg.org/legal.html) |
| Deno | MIT for Deno itself; bundled dependencies have their own notices. | [Source and license](https://github.com/denoland/deno) |
| Microsoft Visual C++ runtime (x64) | Installed from Microsoft under its own terms. Microsoft runtime DLLs and Windows API-set DLLs are excluded from our ZIP. | [Microsoft downloads](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist/) |

These tools are independent programs invoked as subprocesses. Follow their installation and distribution terms. If you redistribute their binaries, this notice alone is not a substitute for all requirements, such as corresponding source obligations.

## Design

The interface is inspired by [Emil Kowalski's design principles](https://github.com/emilkowalski/skills). No code or visual assets from that repository are bundled. This credit does not imply endorsement.

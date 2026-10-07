# Build with: python -m PyInstaller packaging/windows.spec
from pathlib import Path

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / "run.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[],
    hiddenimports=[],
    excludes=["pytest", "ruff", "PIL", "setuptools", "pip", "yt_dlp"],
    noarchive=False,
)
# Windows 10/11 supplies its API sets and UCRT. The VC runtime is installed
# separately from Microsoft, instead of copying Windows/runtime DLLs into our ZIP.
analysis.binaries = [
    entry for entry in analysis.binaries
    if not Path(entry[0]).name.lower().startswith(
        ("api-ms-win-", "vcruntime", "msvcp", "ucrtbase")
    )
]
archive = PYZ(analysis.pure)
executable = EXE(
    archive, analysis.scripts, [],
    exclude_binaries=True,
    name="Video Downloader",
    console=False,
    debug=False,
    strip=False,
    upx=False,
)
bundle = COLLECT(
    executable, analysis.binaries, analysis.datas,
    strip=False, upx=False, name="Video Downloader",
)

"""Copy the actual runtime's notices into the Windows release folder."""

import decimal
import hashlib
import importlib.metadata
import json
import pyexpat
import shutil
import ssl
import sys
import tkinter
import zlib
from pathlib import Path


def collect(bundle: Path, project: Path) -> None:
    if sys.version_info[:3] != (3, 13, 15):
        raise RuntimeError(
            "The audited Windows build uses Python 3.13.15. Review runtime licenses before changing it."
        )
    source_licenses = project / "licenses"
    destination = bundle / "licenses"
    shutil.copytree(source_licenses, destination, dirs_exist_ok=True)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if not python_license.is_file():
        raise RuntimeError("Python's complete LICENSE.txt was not found.")
    shutil.copy2(python_license, destination / "Python.txt")
    root = tkinter.Tk()
    root.withdraw()
    try:
        tcl_version = root.tk.call("info", "patchlevel")
        tk_version = root.tk.call("package", "provide", "Tk")
        tk_license = Path(str(root.tk.call("set", "tk_library"))) / "license.terms"
    finally:
        root.destroy()
    if tcl_version != "8.6.15" or tk_version != "8.6.15" or not tk_license.is_file():
        raise RuntimeError(
            "Unexpected Tcl/Tk runtime. Review and update its license texts before building."
        )
    shutil.copy2(tk_license, destination / "Tk.txt")
    copied = []
    distribution = importlib.metadata.distribution("pyinstaller")
    for file in distribution.files or []:
        if "license" in str(file).lower() or file.name.lower() == "copying.txt":
            if file.name.lower().endswith((".txt", ".md")) or file.name.lower() in (
                "license",
                "copying",
            ):
                actual = distribution.locate_file(file)
                if actual.is_file():
                    shutil.copy2(actual, destination / ("PyInstaller-" + file.name))
                    copied.append(file.name)
    if not copied:
        raise RuntimeError("PyInstaller's license text was not found.")
    versions = {
        "python": sys.version.split()[0],
        "tcl": tcl_version,
        "tk": tk_version,
        "openssl": ssl.OPENSSL_VERSION,
        "zlib": zlib.ZLIB_RUNTIME_VERSION,
        "expat": pyexpat.EXPAT_VERSION,
        "mpdecimal": decimal.__libmpdec_version__,
        "pyinstaller": distribution.version,
        "python_changes": "No changes to Python, Tcl/Tk or the third-party runtime libraries.",
    }
    versions["license_sha256"] = {
        file.name: hashlib.sha256(file.read_bytes()).hexdigest()
        for file in destination.iterdir()
        if file.is_file()
    }
    (destination / "runtime.json").write_text(
        json.dumps(versions, indent=2) + "\n", encoding="utf-8"
    )
    files = sorted(
        path.relative_to(bundle).as_posix() for path in bundle.rglob("*") if path.is_file()
    )
    (destination / "bundled-files.txt").write_text("\n".join(files) + "\n", encoding="utf-8")
    print("Runtime notices collected:", len(files), "files in bundle")


if __name__ == "__main__":
    collect(Path(sys.argv[1]), Path(__file__).resolve().parents[1])

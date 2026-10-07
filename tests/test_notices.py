import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(
    sys.platform != "win32" or sys.version_info[:3] != (3, 13, 15),
    reason="Audited Windows build environment required",
)
def test_runtime_notices_are_collected_from_actual_runtime(tmp_path):
    project = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "collect_notices", project / "packaging/collect_notices.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.collect(tmp_path, project)
    assert (tmp_path / "licenses/Python.txt").stat().st_size > 1000
    assert (tmp_path / "licenses/Tk.txt").stat().st_size > 1000
    assert (tmp_path / "licenses/runtime.json").exists()

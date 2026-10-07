import importlib
import subprocess
import sys
import threading
import time

import pytest


def engine_module():
    try:
        return importlib.import_module("video_downloader.engine")
    except ModuleNotFoundError:
        pytest.fail("Download execution has not been implemented")


class ScriptEngineMixin:
    """Run small real child processes instead of contacting video services."""

    def command(self, url, folder, fragments):
        return [sys.executable, "-u", "-c", self.scripts[url]]


def make_engine(core, tools, scripts, events, workers=4):
    module = engine_module()

    class Engine(ScriptEngineMixin, module.DownloadEngine):
        pass

    engine = Engine(
        core.DownloadOptions(workers=workers),
        tools.ToolPaths("fixture", None, None, None),
        events.append,
    )
    engine.scripts = scripts
    return engine


def test_processing_is_distinct_from_completed(core, tools, tmp_path):
    events = []
    engine = make_engine(
        core,
        tools,
        {"x": "print('__PROGRESS__100%|1 MiB/s|0'); print('__PROCESSING__started')"},
        events,
    )
    engine.run(["x"], tmp_path)
    states = [event.value for event in events if event.kind == "state"]
    assert states == ["running", "processing", "completed"]
    assert events[-1].value["completed"] == 1
    progress = [event.value for event in events if event.kind == "progress"]
    assert progress[0] < 100 and progress[-1] == 100


def test_access_failure_is_not_retried(core, tools, tmp_path):
    events = []
    engine = make_engine(
        core, tools, {"x": "import sys; print('HTTP Error 403: Forbidden'); sys.exit(1)"}, events
    )
    engine.run(["x"], tmp_path)
    assert not any(event.kind == "log" and "Retrying" in event.value for event in events)
    assert len(events[-1].value["failed"]) == 1
    assert "403" in events[-1].value["failed"][0][1]


def test_transient_failure_retries_once_then_succeeds(core, tools, tmp_path):
    marker = tmp_path / "attempt"
    script = f"from pathlib import Path; import sys; p=Path({str(marker)!r}); old=p.exists(); p.touch(); print('ok' if old else 'HTTP Error 503'); sys.exit(0 if old else 1)"
    events = []
    engine = make_engine(core, tools, {"x": script}, events)
    engine.run(["x"], tmp_path)
    assert events[-1].value["completed"] == 1
    assert sum(event.kind == "log" and "Retrying" in event.value for event in events) == 1


def test_cancel_stops_silent_process_and_waiting_jobs(core, tools, tmp_path):
    marker = tmp_path / "unexpected"
    events = []
    scripts = {
        "slow": "import time; time.sleep(60)",
        "queued": f"from pathlib import Path; Path({str(marker)!r}).touch()",
    }
    engine = make_engine(core, tools, scripts, events, workers=1)
    runner = threading.Thread(target=engine.run, args=(["slow", "queued"], tmp_path))
    runner.start()
    deadline = time.monotonic() + 5
    while not engine.active_count and time.monotonic() < deadline:
        time.sleep(0.01)
    assert engine.active_count == 1
    engine.cancel()
    runner.join(8)
    assert not runner.is_alive()
    assert engine.active_count == 0
    assert not marker.exists()
    assert events[-1].value["cancelled"] is True


def test_spawn_failure_returns_diagnostic_and_cleans_up(core, tools, tmp_path):
    module = engine_module()
    events = []
    engine = module.DownloadEngine(
        core.DownloadOptions(),
        tools.ToolPaths(str(tmp_path / "missing.exe"), None, None, None),
        events.append,
    )
    engine.run(["https://example.org/video"], tmp_path)
    assert engine.active_count == 0
    assert events[-1].value["failed"]


def test_process_tree_cancellation_stops_child(tmp_path):
    module = engine_module()
    pid_file = tmp_path / "child.pid"
    script = f"import subprocess,sys,time; from pathlib import Path; child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); Path({str(pid_file)!r}).write_text(str(child.pid)); time.sleep(60)"
    kwargs = module.process_kwargs()
    proc = subprocess.Popen([sys.executable, "-c", script], **kwargs)
    try:
        deadline = time.monotonic() + 5
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert pid_file.exists()
        child_pid = int(pid_file.read_text())
        module.terminate_tree(proc)
        assert proc.poll() is not None
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {child_pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
            )
            assert f'"{child_pid}"' not in result.stdout
    finally:
        module.terminate_tree(proc)

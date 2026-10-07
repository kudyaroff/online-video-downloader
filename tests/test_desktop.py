import importlib
import os
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="A desktop display is required",
)


@pytest.fixture
def app(tmp_path):
    try:
        module = importlib.import_module("video_downloader.desktop")
    except ModuleNotFoundError:
        pytest.fail("The packaged desktop interface has not been implemented")
    window = module.VideoDownloader(preferences_path=tmp_path / "settings.json")
    window.withdraw()
    window.update()
    yield window
    if window.tk.call("info", "commands", "winfo"):
        window.destroy()


def test_empty_input_does_not_start_download(app, monkeypatch):
    messages = []
    monkeypatch.setattr(
        "tkinter.messagebox.showinfo", lambda *args, **kwargs: messages.append(args)
    )
    app.start_downloads()
    assert app.engine is None
    assert messages


def test_activity_clear_works_when_log_is_read_only(app):
    app.log("Some activity")
    app.clear_log()
    assert app.log_text.get("1.0", "end").strip() == ""
    assert str(app.log_text["state"]) == "disabled"


def test_folder_preferences_are_saved_on_close(app, tmp_path):
    app.folder_var.set(str(tmp_path / "My videos \u00fc"))
    app.save_preferences()
    import json

    saved = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert saved["folder"] == str(tmp_path / "My videos \u00fc")


def test_pasted_text_extracts_urls_without_duplicates(app):
    app.urls_text.insert(
        "1.0", "Links: https://youtu.be/a https://youtu.be/a https://example.org/b"
    )
    assert app.parse_urls() == ["https://youtu.be/a", "https://example.org/b"]


def test_destroy_cancels_pending_poll(app):
    app.destroy()
    assert not app.tk.call("after", "info")

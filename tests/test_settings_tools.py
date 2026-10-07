def test_bad_settings_fall_back_without_overwriting_file(settings, tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("not json", encoding="utf-8")
    values = settings.load_settings(path)
    assert "folder" in values and values["workers"] == 4
    assert path.read_text(encoding="utf-8") == "not json"


def test_saved_settings_preserve_unicode_folder(settings, tmp_path):
    path = tmp_path / "preferences" / "settings.json"
    settings.save_settings({"folder": "C:/My videos \u00fc", "workers": 2}, path)
    assert settings.load_settings(path)["folder"] == "C:/My videos \u00fc"
    assert settings.load_settings(path)["workers"] == 2


def test_settings_ignore_invalid_values(settings, tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"workers": "unlimited", "folder": null}', encoding="utf-8")
    values = settings.load_settings(path)
    assert values["workers"] == 4 and isinstance(values["folder"], str)


def test_discovers_tools_in_portable_directory(tools, tmp_path):
    import os

    suffix = ".exe" if os.name == "nt" else ""
    binary = tmp_path / ("ffmpeg" + suffix)
    binary.write_bytes(b"test fixture")
    assert tools.find_tool("ffmpeg", extra_dirs=[tmp_path]) == str(binary)

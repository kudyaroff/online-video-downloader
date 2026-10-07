from dataclasses import FrozenInstanceError

import pytest


def test_extracts_links_and_keeps_first_occurrence(core):
    text = "Watch https://youtu.be/abc, then https://example.org/video.mp4. https://youtu.be/abc"
    assert core.parse_urls(text) == ["https://youtu.be/abc", "https://example.org/video.mp4"]


@pytest.mark.parametrize(
    "url",
    [
        "https://youtube.com.example.org/a",
        "https://notyoutube.com/a",
        "https://youtube.com@evil.org/a",
    ],
)
def test_misleading_hosts_are_not_youtube(core, url):
    assert core.source_type(url) == "Other"


def test_recognizes_real_subdomains_and_yandex(core):
    assert core.source_type("https://m.youtube.com/watch?v=x") == "YouTube"
    assert core.source_type("https://disk.yandex.ru/d/test") == "Yandex Disk"
    assert core.source_type("https://drive.google.com/file/d/x") == "Google Drive"


@pytest.mark.parametrize(
    "quality,height",
    [
        ("720p · Windows compatible", 720),
        ("1080p · Windows compatible", 1080),
        ("2160p / 4K · source codec", 2160),
    ],
)
def test_every_video_fallback_respects_height(core, quality, height):
    fmt = core.select_format("YouTube", quality)
    for alternative in fmt.split("/"):
        video = alternative.split("+")[0]
        assert f"height<={height}" in video


def test_command_preserves_paths_and_uses_found_ffmpeg(core, tools, tmp_path):
    paths = tools.ToolPaths("C:/some tools/yt-dlp.exe", "C:/some tools/ffmpeg.exe", None, None)
    folder = tmp_path / "My videos \u00fc"
    cmd = core.build_command("https://youtu.be/abc", folder, core.DownloadOptions(), paths, 4)
    assert cmd[0] == paths.ytdlp
    assert cmd[cmd.index("--ffmpeg-location") + 1] == paths.ffmpeg
    assert cmd[cmd.index("-P") + 1] == str(folder)
    assert "--ignore-config" in cmd
    assert cmd[-2:] == ["--", "https://youtu.be/abc"]


def test_settings_snapshot_is_immutable(core):
    options = core.DownloadOptions()
    with pytest.raises(FrozenInstanceError):
        options.workers = 100


def test_workers_cannot_be_unbounded(core):
    assert core.DownloadOptions(workers=100).workers == 4
    assert core.DownloadOptions(workers=0).workers == 1


@pytest.mark.parametrize(
    "error,expected",
    [
        ("HTTP Error 503: unavailable", True),
        ("Connection reset by peer", True),
        ("Unsupported URL", False),
        ("HTTP Error 403: Forbidden", False),
        ("Requested format is not available", False),
    ],
)
def test_retries_only_transient_errors(core, error, expected):
    assert core.is_retryable(error) is expected


def test_audio_uses_extraction_and_does_not_recode_video(core, tools, tmp_path):
    paths = tools.ToolPaths("yt-dlp", "ffmpeg", "ffprobe", None)
    cmd = core.build_command(
        "https://example.org/a",
        tmp_path,
        core.DownloadOptions(quality="Audio only · M4A"),
        paths,
        1,
    )
    assert "-x" in cmd and "--audio-format" in cmd
    assert "--recode-video" not in cmd

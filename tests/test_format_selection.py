import pytest
from yt_dlp import YoutubeDL
from yt_dlp.utils import ExtractorError

from video_downloader.core import select_format


def choose(quality, heights):
    formats = []
    for index, height in enumerate(heights):
        item = {
            "format_id": str(index),
            "url": f"https://example.org/{index}.mp4",
            "ext": "mp4",
            "vcodec": "h264",
            "acodec": "aac",
        }
        if height is not None:
            item["height"] = height
        formats.append(item)
    info = {"id": "fixture", "title": "Fixture", "extractor": "generic", "formats": formats}
    with YoutubeDL(
        {
            "format": select_format("Other", quality),
            "quiet": True,
            "no_warnings": True,
            "simulate": True,
        }
    ) as downloader:
        return downloader.process_ie_result(info, download=False)


@pytest.mark.parametrize(
    "quality",
    ["1080p · Windows compatible", "720p · Windows compatible", "2160p / 4K · source codec"],
)
def test_direct_file_without_height_can_be_selected(quality):
    selected = choose(quality, [None])
    assert selected["format_id"] == "0"


@pytest.mark.parametrize(
    "quality,limit",
    [
        ("1080p · Windows compatible", 1080),
        ("720p · Windows compatible", 720),
        ("2160p / 4K · source codec", 2160),
    ],
)
def test_known_height_above_limit_is_rejected(quality, limit):
    with pytest.raises(ExtractorError, match="Requested format is not available"):
        choose(quality, [limit + 1])


def test_best_known_format_under_limit_is_selected():
    selected = choose("1080p · Windows compatible", [360, 720, 1080, 2160])
    assert selected["height"] == 1080

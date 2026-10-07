import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def core():
    try:
        return importlib.import_module("video_downloader.core")
    except ModuleNotFoundError:
        pytest.fail("The shared download core has not been implemented")


@pytest.fixture
def settings():
    try:
        return importlib.import_module("video_downloader.settings")
    except ModuleNotFoundError:
        pytest.fail("Saved settings have not been implemented")


@pytest.fixture
def tools():
    try:
        return importlib.import_module("video_downloader.tools")
    except ModuleNotFoundError:
        pytest.fail("Tool discovery has not been implemented")

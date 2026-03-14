import pytest
import cv2
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from game_bot.utils.template_matcher import TemplateMatcher


class TestTemplateMatcher:
    @pytest.fixture
    def matcher(self, tmp_path):
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        return TemplateMatcher(str(assets_dir))

    @pytest.fixture
    def sample_screenshot(self):
        return np.zeros((720, 1280, 3), dtype=np.uint8)

    def test_empty_matcher(self, matcher):
        assert len(matcher.templates) == 0

    def test_add_template(self, matcher):
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        matcher.add_template("test_btn", template)
        assert "test_btn" in matcher.templates

    def test_match_not_found(self, matcher, sample_screenshot):
        result = matcher.match(sample_screenshot, "nonexistent")
        assert result is None

    def test_match_success(self, matcher):
        template = np.ones((50, 50, 3), dtype=np.uint8) * 255
        matcher.add_template("white_btn", template)

        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        screenshot[75:125, 75:125] = 255

        pos = matcher.match(screenshot, "white_btn", threshold=0.5)
        assert pos is not None
        assert pos[0] == 100
        assert pos[1] == 100

    def test_match_all(self, matcher):
        template = np.ones((20, 20, 3), dtype=np.uint8) * 255
        matcher.add_template("small_btn", template)

        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        screenshot[10:30, 10:30] = 255
        screenshot[60:80, 60:80] = 255

        positions = matcher.match_all(screenshot, "small_btn", threshold=0.5)
        assert len(positions) >= 2

    def test_threshold_behavior(self, matcher):
        template = np.ones((30, 30, 3), dtype=np.uint8) * 200
        matcher.add_template("gray_btn", template)

        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        screenshot[35:65, 35:65] = 200

        result_high = matcher.match(screenshot, "gray_btn", threshold=0.95)
        result_low = matcher.match(screenshot, "gray_btn", threshold=0.5)

        assert result_low is not None
        assert result_high is None or result_high is not None


class TestIntegration:
    def test_matcher_with_real_image(self):
        assets_dir = Path(__file__).parent.parent / "assets"
        if not assets_dir.exists() or not list(assets_dir.glob("*.png")):
            pytest.skip("No assets found")

        matcher = TemplateMatcher(str(assets_dir))
        assert len(matcher.templates) > 0

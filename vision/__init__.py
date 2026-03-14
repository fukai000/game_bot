import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    x: int
    y: int
    confidence: float
    template_name: str


class Vision:
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = Path(assets_dir)
        self.templates: dict[str, np.ndarray] = {}
        self.default_threshold = 0.8
        self._load_templates()

    def _load_templates(self):
        if not self.assets_dir.exists():
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"Created assets directory: {self.assets_dir}")
            return

        for img_path in self.assets_dir.glob("*.png"):
            self.templates[img_path.stem] = cv2.imread(str(img_path))
            logger.info(f"Loaded template: {img_path.stem}")

    def add_template(self, name: str, image: np.ndarray):
        self.templates[name] = image

    def save_template(self, name: str, image: np.ndarray):
        self.templates[name] = image
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(self.assets_dir / f"{name}.png"), image)
        logger.info(f"Saved template: {name}")

    def capture_area(
        self, screenshot: np.ndarray, x: int, y: int, width: int = 50, height: int = 50
    ) -> np.ndarray:
        h, w = screenshot.shape[:2]
        x1 = max(0, x - width // 2)
        y1 = max(0, y - height // 2)
        x2 = min(w, x + width // 2)
        y2 = min(h, y + height // 2)
        return screenshot[y1:y2, x1:x2]

    def locate(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: Optional[float] = None,
    ) -> Optional[MatchResult]:
        if template_name not in self.templates:
            logger.warning(f"Template not found: {template_name}")
            return None

        template = self.templates[template_name]
        if template is None:
            return None

        threshold = threshold or self.default_threshold
        h, w = template.shape[:2]

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        logger.debug(f"Template '{template_name}' match confidence: {max_val:.3f}")

        if max_val >= threshold:
            return MatchResult(
                x=max_loc[0] + w // 2,
                y=max_loc[1] + h // 2,
                confidence=max_val,
                template_name=template_name,
            )

        return None

    def locate_best(
        self,
        screenshot: np.ndarray,
        template_names: List[str],
        threshold: Optional[float] = None,
    ) -> Optional[MatchResult]:
        best_match = None
        best_confidence = 0.0

        for name in template_names:
            result = self.locate(screenshot, name, threshold)
            if result and result.confidence > best_confidence:
                best_match = result
                best_confidence = result.confidence

        return best_match

    def locate_all(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: Optional[float] = None,
    ) -> List[MatchResult]:
        if template_name not in self.templates:
            return []

        template = self.templates[template_name]
        if template is None:
            return []

        threshold = threshold or self.default_threshold
        h, w = template.shape[:2]

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        matches = []
        for pt in zip(*locations[::-1]):
            confidence = result[pt[1], pt[0]]
            matches.append(
                MatchResult(
                    x=pt[0] + w // 2,
                    y=pt[1] + h // 2,
                    confidence=confidence,
                    template_name=template_name,
                )
            )

        return matches

    async def wait_for(
        self,
        get_screenshot,
        template_name: str,
        timeout: float = 10.0,
        interval: float = 0.5,
        threshold: Optional[float] = None,
    ) -> Optional[MatchResult]:
        import asyncio

        async def _wait():
            start = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start < timeout:
                screenshot = await get_screenshot()
                result = self.locate(screenshot, template_name, threshold)
                if result:
                    return result
                await asyncio.sleep(interval)
            return None

        return await _wait()

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List


class TemplateMatcher:
    def __init__(self, assets_dir: str = "assets"):
        self.assets_dir = Path(assets_dir)
        self.templates: dict[str, np.ndarray] = {}
        self._load_templates()

    def _load_templates(self):
        if not self.assets_dir.exists():
            return
        for img_path in self.assets_dir.glob("*.png"):
            self.templates[img_path.stem] = cv2.imread(str(img_path))
            print(f"Loaded template: {img_path.stem}")

    def add_template(self, name: str, image: np.ndarray):
        self.templates[name] = image

    def save_template(self, name: str, image: np.ndarray):
        self.templates[name] = image
        cv2.imwrite(str(self.assets_dir / f"{name}.png"), image)

    def match(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: float = 0.8,
    ) -> Optional[Tuple[int, int]]:
        if template_name not in self.templates:
            return None

        template = self.templates[template_name]
        if template is None:
            return None

        h, w = template.shape[:2]
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y)

        return None

    def match_all(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: float = 0.8,
    ) -> List[Tuple[int, int]]:
        if template_name not in self.templates:
            return []

        template = self.templates[template_name]
        if template is None:
            return []

        h, w = template.shape[:2]
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)

        centers = []
        for pt in zip(*locations[::-1]):
            centers.append((pt[0] + w // 2, pt[1] + h // 2))

        return centers

    def wait_for_match(
        self,
        screenshot_fn,
        template_name: str,
        timeout: float = 10.0,
        interval: float = 0.5,
        threshold: float = 0.8,
    ) -> Optional[Tuple[int, int]]:
        import asyncio

        async def _wait():
            start = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start < timeout:
                screenshot = await screenshot_fn()
                pos = self.match(screenshot, template_name, threshold)
                if pos:
                    return pos
                await asyncio.sleep(interval)
            return None

        return asyncio.run(_wait())

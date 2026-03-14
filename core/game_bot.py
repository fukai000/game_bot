import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import cv2
import numpy as np

from vision import Vision, MatchResult
from action import Action, Direction


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GameState(Enum):
    UNKNOWN = "unknown"
    HOME = "home"
    SCENE = "scene"
    MENU = "menu"
    DIALOG = "dialog"


@dataclass
class Task:
    name: str
    template_name: str
    is_static: bool = False
    static_x: int = 0
    static_y: int = 0
    threshold: float = 0.8
    max_retries: int = 3
    on_found: Optional[Callable] = None


class GameBot:
    def __init__(
        self,
        game_url: str = "",
        user_data_dir: Optional[str] = None,
        assets_dir: str = "assets",
        headless: bool = False,
        executable_path: Optional[str] = None,
        connect_existing: bool = False,
        existing_ws_url: str = "",
    ):
        self.game_url = game_url
        self.user_data_dir = user_data_dir
        self.assets_dir = assets_dir
        self.headless = headless
        self.executable_path = (
            executable_path or "/Applications/ChromiteX.app/Contents/MacOS/ChromiteX"
        )
        self.connect_existing = connect_existing
        self.existing_ws_url = existing_ws_url

        self.vision = Vision(assets_dir)
        self.action: Optional[Action] = None

        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

        self.tasks: list[Task] = []
        self.current_state = GameState.UNKNOWN

        self.swipe_directions = [
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ]
        self.swipe_attempts = 3
        self.home_button = "home"

    async def start(self):
        playwright = await async_playwright().start()

        if self.connect_existing and self.existing_ws_url:
            self.browser = await playwright.chromium.connect_over_cdp(
                self.existing_ws_url
            )
            self.context = (
                self.browser.contexts[0]
                if self.browser.contexts
                else await self.browser.new_context()
            )
            pages = self.context.pages
            if pages:
                self.page = pages[0]
                logger.info(f"Using existing page: {self.page.url}")
            else:
                self.page = await self.context.new_page()
            self.page.on("console", lambda msg: logger.debug(f"Console: {msg.text}"))
            self.action = Action(self.page)
            logger.info(f"Connected to existing browser")
        else:
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                executable_path=self.executable_path,
            )
            if self.user_data_dir:
                self.context = await self.browser.launch_persistent_context(
                    self.user_data_dir,
                    viewport={"width": 1280, "height": 720},
                )
            else:
                self.context = await self.browser.new_context(
                    viewport={"width": 1280, "height": 720},
                )
            self.page = await self.context.new_page()
            self.page.on("console", lambda msg: logger.debug(f"Console: {msg.text}"))
            self.action = Action(self.page)

            if self.game_url:
                await self.page.goto(self.game_url)
                logger.info(f"Game loaded: {self.game_url}")

    async def stop(self):
        if self.browser:
            await self.browser.close()

    async def get_screenshot(self) -> bytes:
        return await self.page.screenshot()

    async def get_image(self) -> np.ndarray:
        screenshot_bytes = await self.get_screenshot()
        return cv2.imdecode(np.frombuffer(screenshot_bytes, np.uint8), cv2.IMREAD_COLOR)

    def add_task(self, task: Task):
        self.tasks.append(task)
        logger.info(f"Added task: {task.name}")

    async def locate_and_click(
        self,
        template_name: str,
        threshold: float = 0.8,
        use_scroll: bool = True,
    ) -> bool:
        screenshot = await self.get_image()
        result = self.vision.locate(screenshot, template_name, threshold)

        if result:
            logger.info(
                f"Found '{template_name}' at ({result.x}, {result.y}), confidence: {result.confidence:.2f}"
            )
            if use_scroll:
                await self.action.click_with_scroll(result.x, result.y)
            else:
                await self.action._native_click(result.x, result.y)
            return True

        logger.warning(f"Template '{template_name}' not found")
        return False

    async def locate_and_click_with_search(
        self,
        template_name: str,
        threshold: float = 0.8,
        max_swipes: int = 3,
    ) -> bool:
        for attempt in range(max_swipes):
            if await self.locate_and_click(template_name, threshold):
                return True

            logger.info(f"Swipe search attempt {attempt + 1}/{max_swipes}")
            await self.action.swipe_search(self.swipe_directions)
            await asyncio.sleep(0.5)

        return False

    async def click_static(self, x: int, y: int):
        await self.action.click_fixed(x, y)

    async def go_home(self):
        logger.info("Returning to home...")
        await self.locate_and_click(self.home_button, threshold=0.7)

    async def execute_task(self, task: Task) -> bool:
        if task.is_static:
            logger.info(
                f"Executing static task: {task.name} at ({task.static_x}, {task.static_y})"
            )
            await self.click_static(task.static_x, task.static_y)
            await asyncio.sleep(1)
            return True

        for attempt in range(task.max_retries):
            logger.info(
                f"Executing task: {task.name} (attempt {attempt + 1}/{task.max_retries})"
            )

            screenshot = await self.get_image()
            result = self.vision.locate(screenshot, task.template_name, task.threshold)

            if result:
                logger.info(f"Found target at ({result.x}, {result.y})")
                await self.action.smart_click(result.x, result.y)
                await asyncio.sleep(1)

                if task.on_found:
                    await task.on_found(self)
                return True

            logger.warning(f"Target not found, trying swipe search...")
            await self.action.swipe_search(self.swipe_directions)
            await asyncio.sleep(0.5)

        logger.error(f"Task '{task.name}' failed after {task.max_retries} attempts")
        return False

    async def run_task(self, task_name: str) -> bool:
        task = next((t for t in self.tasks if t.name == task_name), None)
        if not task:
            logger.warning(f"Task not found: {task_name}")
            return False

        return await self.execute_task(task)

    async def run_daily_tasks(self):
        logger.info("Starting daily tasks...")
        for task in self.tasks:
            await self.execute_task(task)
            await asyncio.sleep(1)
        logger.info("All tasks completed")

    async def refresh_page(self):
        logger.info("Refreshing page...")
        await self.page.reload()
        await asyncio.sleep(2)

    async def capture_template(
        self,
        name: str,
        x: int,
        y: int,
        width: int = 50,
        height: int = 50,
    ):
        screenshot = await self.get_image()
        template = self.vision.capture_area(screenshot, x, y, width, height)
        self.vision.save_template(name, template)
        logger.info(f"Captured template '{name}' at ({x}, {y})")

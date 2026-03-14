import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from game_bot.core.game_bot import GameBot, Task, GameState


class TestGameBot:
    @pytest.fixture
    def bot(self):
        return GameBot(
            game_url="https://example.com",
            assets_dir="assets",
            headless=True,
        )

    def test_bot_initialization(self, bot):
        assert bot.game_url == "https://example.com"
        assert bot.current_state == GameState.UNKNOWN
        assert len(bot.tasks) == 0

    def test_add_task(self, bot):
        task = Task(name="test", template_name="btn")
        bot.add_task(task)
        assert len(bot.tasks) == 1
        assert bot.tasks[0].name == "test"

    def test_task_with_threshold(self, bot):
        task = Task(name="test", template_name="btn", threshold=0.85)
        bot.add_task(task)
        assert bot.tasks[0].threshold == 0.85

    def test_multiple_tasks(self, bot):
        tasks = [
            Task(name="task1", template_name="btn1"),
            Task(name="task2", template_name="btn2"),
            Task(name="task3", template_name="btn3"),
        ]
        for t in tasks:
            bot.add_task(t)
        assert len(bot.tasks) == 3


@pytest.mark.asyncio
class TestGameBotAsync:
    async def test_browser_start_stop(self):
        bot = GameBot(
            game_url="https://www.baidu.com",
            headless=True,
        )
        await bot.start()
        assert bot.browser is not None
        assert bot.page is not None
        await bot.stop()

    async def test_screenshot_capture(self):
        bot = GameBot(
            game_url="https://www.baidu.com",
            headless=True,
        )
        await bot.start()
        screenshot = await bot.get_canvas_screenshot()
        assert len(screenshot) > 0
        await bot.stop()

    async def test_get_canvas_image(self):
        bot = GameBot(
            game_url="https://www.baidu.com",
            headless=True,
        )
        await bot.start()
        img = await bot.get_canvas_image()
        assert img is not None
        assert img.shape[2] == 3
        await bot.stop()


class TestTask:
    def test_task_creation(self):
        task = Task(
            name="签到",
            template_name="sign_in",
            target_state=GameState.HOME,
        )
        assert task.name == "签到"
        assert task.template_name == "sign_in"
        assert task.target_state == GameState.HOME
        assert task.threshold == 0.8

    def test_task_default_threshold(self):
        task = Task(name="test", template_name="btn")
        assert task.threshold == 0.8

    def test_task_custom_threshold(self):
        task = Task(name="test", template_name="btn", threshold=0.95)
        assert task.threshold == 0.95

import asyncio
import random
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class SwipeConfig:
    duration: float = 0.3
    start_offset: int = 50
    end_offset: int = 100


class Action:
    def __init__(self, page):
        self.page = page
        self.viewport_width = 1280
        self.viewport_height = 720
        self.scale = 2

    async def _native_click(self, x: int, y: int):
        await self.page.mouse.move(x, y)
        await self.page.mouse.down()
        await self.page.mouse.up()
        logger.debug(f"Native clicked at ({x}, {y})")

    async def click_with_scroll(self, x: int, y: int):
        viewport_x = x / self.scale
        viewport_y = y / self.scale
        await self.page.mouse.click(viewport_x, viewport_y)
        logger.debug(f"Clicked at ({x}, {y}) -> ({viewport_x}, {viewport_y})")

    async def _native_click(self, x: int, y: int):
        await self.page.mouse.move(x, y)
        await self.page.mouse.down()
        await self.page.mouse.up()
        logger.debug(f"Native clicked at ({x}, {y})")

    async def click_with_scroll(self, x: int, y: int):
        viewport_x = x / self.scale
        viewport_y = y / self.scale
        await self.page.mouse.click(viewport_x, viewport_y)
        logger.debug(f"Clicked at ({x}, {y}) -> ({viewport_x}, {viewport_y})")

    async def _simple_click(self, x: int, y: int):
        await self.page.evaluate(
            """([x, y]) => {
                const el = document.elementFromPoint(x, y);
                if (!el) return;
                const events = [
                    new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y, isTrusted: true }),
                    new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y, isTrusted: true }),
                    new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, isTrusted: true })
                ];
                events.forEach(e => el.dispatchEvent(e));
            }""",
            [x, y],
        )
        logger.debug(f"Clicked at ({x}, {y})")

    async def _click_with_drag(self, x: int, y: int):
        await self.page.evaluate(
            """([x, y]) => {
                const el = document.elementFromPoint(x, y);
                if (!el) return;

                const events = [
                    new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y, isTrusted: true }),
                    new MouseEvent('mousemove', { bubbles: true, clientX: x + 2, clientY: y + 2, isTrusted: true }),
                    new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y, isTrusted: true }),
                    new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, isTrusted: true })
                ];
                events.forEach(e => el.dispatchEvent(e));
            }""",
            [x, y],
        )
        logger.debug(f"Click with drag at ({x}, {y})")

    async def swipe(
        self,
        direction: Direction,
        distance: Optional[int] = None,
        duration: float = 0.3,
    ):
        cx, cy = self.viewport_width // 2, self.viewport_height // 2
        distance = distance or SwipeConfig.end_offset

        if direction == Direction.UP:
            start_x, start_y = cx, cy + distance // 2
            end_x, end_y = cx, cy - distance // 2
        elif direction == Direction.DOWN:
            start_x, start_y = cx, cy - distance // 2
            end_x, end_y = cx, cy + distance // 2
        elif direction == Direction.LEFT:
            start_x, start_y = cx + distance // 2, cy
            end_x, end_y = cx - distance // 2, cy
        else:
            start_x, start_y = cx - distance // 2, cy
            end_x, end_y = cx + distance // 2, cy

        await self.page.evaluate(
            """([sx, sy, ex, ey, duration]) => {
                const el = document.elementFromPoint(sx, sy);
                if (!el) return;

                const startEvent = new MouseEvent('mousedown', {
                    bubbles: true, clientX: sx, clientY: sy, isTrusted: true
                });
                el.dispatchEvent(startEvent);

                setTimeout(() => {
                    const moveEvent = new MouseEvent('mousemove', {
                        bubbles: true, clientX: ex, clientY: ey, isTrusted: true
                    });
                    el.dispatchEvent(moveEvent);

                    setTimeout(() => {
                        const upEvent = new MouseEvent('mouseup', {
                            bubbles: true, clientX: ex, clientY: ey, isTrusted: true
                        });
                        el.dispatchEvent(upEvent);
                    }, duration * 500);
                }, duration * 500);
            }""",
            [start_x, start_y, end_x, end_y, duration],
        )
        logger.debug(f"Swiped {direction.value}")

    async def swipe_search(
        self,
        directions: list[Direction],
        each_duration: float = 0.5,
    ):
        for direction in directions:
            await self.swipe(direction, duration=each_duration)
            await asyncio.sleep(0.3)

    async def click_fixed(self, x: int, y: int):
        await self.smart_click(x, y, simulate_drag=False)

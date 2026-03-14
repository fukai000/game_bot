import asyncio
import random
from typing import Tuple


async def smart_click(
    page,
    x: int,
    y: int,
    random_offset: int = 3,
    min_delay: float = 0.05,
    max_delay: float = 0.15,
):
    offset_x = random.randint(-random_offset, random_offset)
    offset_y = random.randint(-random_offset, random_offset)
    final_x = x + offset_x
    final_y = y + offset_y

    await asyncio.sleep(random.uniform(min_delay, max_delay))

    await page.evaluate(
        """([x, y]) => {
            const event = new MouseEvent('mousedown', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: x,
                clientY: y,
                isTrusted: true
            });
            document.elementFromPoint(x, y)?.dispatchEvent(event);
        }""",
        [final_x, final_y],
    )

    await asyncio.sleep(random.uniform(0.02, 0.08))

    await page.evaluate(
        """([x, y]) => {
            const event = new MouseEvent('mouseup', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: x,
                clientY: y,
                isTrusted: true
            });
            document.elementFromPoint(x, y)?.dispatchEvent(event);

            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: x,
                clientY: y,
                isTrusted: true
            });
            document.elementFromPoint(x, y)?.dispatchEvent(clickEvent);
        }""",
        [final_x, final_y],
    )


async def click_if_matched(
    page,
    matcher,
    template_name: str,
    threshold: float = 0.8,
    screenshot_callback=None,
) -> bool:
    if screenshot_callback is None:
        screenshot_callback = lambda: page.screenshot()

    screenshot_bytes = await screenshot_callback()
    import numpy as np
    import cv2

    screenshot = cv2.imdecode(
        np.frombuffer(screenshot_bytes, np.uint8), cv2.IMREAD_COLOR
    )

    pos = matcher.match(screenshot, template_name, threshold)
    if pos:
        await smart_click(page, pos[0], pos[1])
        return True
    return False

import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_bot import GameBot


WS_URL = "ws://127.0.0.1:9222/devtools/browser/87559b21-52a4-44f6-ac63-a955d538ed8b"

TEMPLATE_SEQUENCE = [
    "guke",
    "zhizuo",
    "zhizuo2",
    "queding",
    "jiaofu",
    "gongxi",
]

MIN_DELAY = 1.0
MAX_DELAY = 2.0

COORD_DEVIATION = 5


async def run_workflow():
    ASSETS_DIR = str(Path(__file__).parent / "assets")

    bot = GameBot(
        game_url="",
        assets_dir=ASSETS_DIR,
        connect_existing=True,
        existing_ws_url=WS_URL,
    )

    await bot.start()
    await asyncio.sleep(1)

    print("\n=== 开始工作流 ===")
    print(f"序列: {' -> '.join(TEMPLATE_SEQUENCE)}")
    print(f"间隔: {MIN_DELAY}-{MAX_DELAY}秒\n")

    for i, template_name in enumerate(TEMPLATE_SEQUENCE):
        print(f"[{i + 1}/{len(TEMPLATE_SEQUENCE)}] 查找 {template_name}...")

        screenshot = await bot.get_image()
        result = bot.vision.locate(screenshot, template_name, threshold=0.3)

        if result:
            x = result.x + random.randint(-COORD_DEVIATION, COORD_DEVIATION)
            y = result.y + random.randint(-COORD_DEVIATION, COORD_DEVIATION)

            print(f"  找到: ({result.x}, {result.y}), 置信度: {result.confidence:.2f}")
            print(f"  点击: ({x}, {y})")

            await bot.action.click_with_scroll(x, y)
            print(f"  已点击\n")

            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"  等待 {delay:.1f}秒...\n")
            await asyncio.sleep(delay)
        else:
            print(f"  未找到 {template_name}，停止工作流\n")
            break

    print("=== 工作流完成 ===")
    await bot.stop()


if __name__ == "__main__":
    asyncio.run(run_workflow())

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_bot import GameBot


async def capture_templates():
    GAME_URL = "https://www.wanyiwan.top/game/xjskp"
    bot = GameBot(
        game_url=GAME_URL,
        assets_dir="assets",
        headless=False,
    )

    await bot.start()
    await asyncio.sleep(2)

    print("\n=== 模板采集工具 ===")
    print("1. 输入 'screenshot' 保存当前截图")
    print("2. 用图片查看器打开截图，手动查看坐标")
    print("3. 输入 'capture <名称> <x> <y>' 保存模板")
    print("输入 quit 退出\n")

    while True:
        cmd = input("> ").strip()

        if cmd == "quit":
            break
        elif cmd == "screenshot":
            ss = await bot.get_screenshot()
            Path("debug.png").write_bytes(ss)
            print("截图已保存到 debug.png")
            print("用预览或其他图片查看器打开，手动查看坐标")
        elif cmd.startswith("capture "):
            parts = cmd.split()
            if len(parts) >= 4:
                name, x, y = parts[1], int(parts[2]), int(parts[3])
                await bot.capture_template(name, x, y)
                print(f"已采集: {name}")
            else:
                print("用法: capture <名称> <x> <y>")
        elif cmd:
            print("未知命令")

    await bot.stop()


if __name__ == "__main__":
    asyncio.run(capture_templates())

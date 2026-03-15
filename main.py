import asyncio
import logging
import sys
import random
import readline
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.game_bot import GameBot
from config import (
    SEARCH_RANGE,
    THRESHOLDS,
    WORKFLOW_DELAY,
    RETRY_COUNT,
    RETRY_DELAY,
    RUN_LOOP_SLEEP_MIN,
    RUN_LOOP_SLEEP_MAX,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


WORKFLOWS = {
    "guke": ["guke", "zhizuo", "zhizuo2", "queding", "jiaofu", "gongxi"],
}


last_command = ""


def input_with_history(prompt):
    global last_command
    try:
        line = input(prompt)
        if line.strip():
            last_command = line
        return line
    except EOFError:
        return ""


async def click_single(bot, template_name, threshold=0.3, retry_count=RETRY_COUNT):
    sr = SEARCH_RANGE
    for attempt in range(retry_count + 1):
        screenshot = await bot.get_image()
        results = bot.vision.locate_all(screenshot, template_name, threshold)
        results = filter_results_in_range(
            results, sr["x_min"], sr["x_max"], sr["y_min"], sr["y_max"]
        )

        if results:
            result = results[0]
            x, y = clamp_click(
                result.x + random.randint(-2, 2), result.y + random.randint(-2, 2)
            )
            print(
                f"找到 {template_name}: ({result.x}, {result.y}), 置信度: {result.confidence:.2f}"
            )
            await bot.action.click_with_scroll(x, y)
            print(f"已点击: ({x}, {y})")
            return True

        if attempt < retry_count:
            print(
                f"未找到 {template_name}，{RETRY_DELAY}秒后重试 ({attempt + 1}/{retry_count})..."
            )
            await asyncio.sleep(RETRY_DELAY)

    print(f"未找到: {template_name}")
    return False


async def recover_to_huayi(bot):
    print("\n=== 进入恢复模式 ===")

    for attempt in range(10):
        screenshot = await bot.get_image()

        huayi_result = bot.vision.locate(screenshot, "huayi", threshold=0.6)
        if huayi_result:
            print(f"找到 huayi ({huayi_result.x}, {huayi_result.y})，等待恢复...")
            await asyncio.sleep(1)
            print("恢复完成")
            return True

        print(f"未找到 huayi ({attempt + 1}/10)，点击 (600, 280) 附近...")
        x = clamp(random.randint(595, 605), 200, 930)
        y = clamp(random.randint(275, 285), 180, 1450)
        await bot.action.click_with_scroll(x, y)
        await asyncio.sleep(1)

    print("恢复超时")
    return False


def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))


def filter_results_in_range(results, x_min, x_max, y_min, y_max):
    return [r for r in results if x_min <= r.x <= x_max and y_min <= r.y <= y_max]


def clamp_click(x, y):
    return clamp(x, SEARCH_RANGE["x_min"], SEARCH_RANGE["x_max"]), clamp(
        y, SEARCH_RANGE["y_min"], SEARCH_RANGE["y_max"]
    )


async def click_single(bot, template_name, threshold=0.3, retry_count=RETRY_COUNT):
    sr = SEARCH_RANGE
    for attempt in range(retry_count + 1):
        screenshot = await bot.get_image()
        results = bot.vision.locate_all(screenshot, template_name, threshold)
        results = filter_results_in_range(
            results, sr["x_min"], sr["x_max"], sr["y_min"], sr["y_max"]
        )

        if results:
            result = results[0]
            x, y = clamp_click(
                result.x + random.randint(-2, 2), result.y + random.randint(-2, 2)
            )
            print(
                f"找到 {template_name}: ({result.x}, {result.y}), 置信度: {result.confidence:.2f}"
            )
            await bot.action.click_with_scroll(x, y)
            print(f"已点击: ({x}, {y})")
            return True

        if attempt < retry_count:
            print(
                f"未找到 {template_name}，{RETRY_DELAY}秒后重试 ({attempt + 1}/{retry_count})..."
            )
            await asyncio.sleep(RETRY_DELAY)

    print(f"未找到: {template_name}")
    return False


async def recover_to_huayi(bot):
    print("\n=== 进入恢复模式 ===")

    for attempt in range(10):
        screenshot = await bot.get_image()

        huayi_result = bot.vision.locate(screenshot, "huayi", threshold=0.6)
        if huayi_result:
            print(f"找到 huayi ({huayi_result.x}, {huayi_result.y})，等待恢复...")
            await asyncio.sleep(1)
            print("恢复完成")
            return True

        print(f"未找到 huayi ({attempt + 1}/10)，点击 (600, 280) 附近...")
        x = clamp(
            random.randint(595, 605), SEARCH_RANGE["x_min"], SEARCH_RANGE["x_max"]
        )
        y = clamp(
            random.randint(275, 285), SEARCH_RANGE["y_min"], SEARCH_RANGE["y_max"]
        )
        await bot.action.click_with_scroll(x, y)
        await asyncio.sleep(1)

    print("恢复超时")
    return False


async def run_workflow_single(bot, templates, start_index=0):
    for i in range(start_index, len(templates)):
        name = templates[i]
        threshold = THRESHOLDS.get(name, 0.6)
        print(f"[{i + 1}/{len(templates)}] 查找 {name} (阈值: {threshold})...")

        if await click_single(bot, name, threshold=threshold):
            await asyncio.sleep(WORKFLOW_DELAY)
        else:
            return False, i

    return True, len(templates)


async def run_workflow(bot, workflow_name):
    if workflow_name not in WORKFLOWS:
        print(f"未知工作流: {workflow_name}")
        print(f"可用工作流: {list(WORKFLOWS.keys())}")
        return

    templates = WORKFLOWS[workflow_name]
    threshold = THRESHOLDS.get(templates[0], 0.6)
    sr = SEARCH_RANGE

    total_executed = 0
    round_num = 0

    while True:
        round_num += 1
        screenshot = await bot.get_image()
        results = bot.vision.locate_all(screenshot, templates[0], threshold=threshold)
        results = filter_results_in_range(
            results, sr["x_min"], sr["x_max"], sr["y_min"], sr["y_max"]
        )

        if not results:
            if total_executed == 0:
                print(f"未找到: {templates[0]} (阈值: {threshold})")
            else:
                print(f"已完成 {total_executed} 个工作流，没有更多 {templates[0]}")
            break

        result = results[0]
        if result.confidence < threshold:
            print(f"置信度 {result.confidence:.2f} < {threshold}，停止")
            break

        print(f"\n=== 工作流: {workflow_name} 第 {round_num} 轮 ===")
        print(
            f"点击 {templates[0]}: ({result.x}, {result.y}), 置信度: {result.confidence:.2f}"
        )

        x, y = clamp_click(
            result.x + random.randint(-5, 5), result.y + random.randint(-5, 5)
        )
        await bot.action.click_with_scroll(x, y)
        await asyncio.sleep(0.5)

        success, fail_index = await run_workflow_single(bot, templates, 1)

        if not success:
            print(f"步骤 {fail_index + 1} 失败，进入恢复模式...")
            await recover_to_huayi(bot)
            await asyncio.sleep(1)
            continue

        total_executed += 1
        print(f"\n工作流完成，等待 1.5s 后继续...")
        await asyncio.sleep(1.5)

    print(f"\n=== 总计完成 {total_executed} 个工作流 ===")


async def drag(bot, direction, distance):
    print(f"\n向{direction}拖动 {distance} 像素...")

    start_x, start_y = 400, 400

    if direction == "left":
        end_x, end_y = start_x - distance, start_y
    elif direction == "right":
        end_x, end_y = start_x + distance, start_y
    elif direction == "up":
        end_x, end_y = start_x, start_y - distance
    elif direction == "down":
        end_x, end_y = start_x, start_y + distance
    else:
        print(f"未知方向: {direction}")
        return

    steps = max(distance // 10, 1)

    await bot.action.page.mouse.move(start_x, start_y)
    await bot.action.page.mouse.down()

    for i in range(steps):
        x = start_x + (end_x - start_x) * (i + 1) // steps
        y = start_y + (end_y - start_y) * (i + 1) // steps
        await bot.action.page.mouse.move(x, y)
        await asyncio.sleep(0.02)

    await bot.action.page.mouse.up()
    print("完成\n")


async def main():
    global last_command

    ASSETS_DIR = str(Path(__file__).parent / "assets")

    bot = GameBot(
        game_url="",
        assets_dir=ASSETS_DIR,
        connect_existing=True,
        existing_ws_url=WS_URL,
        headless=False,
    )

    await bot.start()
    await asyncio.sleep(1)

    print("\n=== 游戏自动化工具 ===")
    print("点击范围: x=200-930, y=180-1450")
    print("输入 'help' 查看所有命令\n")

    while True:
        try:
            cmd = input_with_history("> ").strip()

            if not cmd:
                continue

            parts = cmd.split()
            action = parts[0].lower()
            arg = " ".join(parts[1:]) if len(parts) > 1 else ""

            if action == "quit" or action == "q":
                break

            elif action == "screenshot" or action == "ss":
                ss = await bot.get_screenshot()
                Path("screenshot.png").write_bytes(ss)
                print("截图已保存到 screenshot.png\n")

            elif action == "click":
                if arg:
                    await click_single(bot, arg)
                else:
                    print("用法: click <图标名称>\n")

            elif action == "find":
                if arg:
                    screenshot = await bot.get_image()
                    results = bot.vision.locate_all(screenshot, arg, threshold=0.6)
                    if results:
                        print(f"找到 {arg} 共 {len(results)} 个:")
                        for i, r in enumerate(results):
                            print(
                                f"  [{i + 1}] ({r.x}, {r.y}), 置信度: {r.confidence:.2f}"
                            )
                        result = await bot.page.evaluate(
                            """
                            (data) => {
                                try {
                                    const results = data[0];
                                    const doc = document.querySelector('iframe') ? document.querySelector('iframe').contentDocument : document;
                                    const existing = doc.getElementById('debug-marker');
                                    if (existing) existing.remove();
                                    const container = doc.createElement('div');
                                    container.id = 'debug-marker';
                                    container.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:99999;';
                                    results.forEach((r, i) => {
                                        const circle = doc.createElement('div');
                                        circle.style.cssText = `
                                            position: absolute;
                                            left: ${r[0]}px;
                                            top: ${r[1]}px;
                                            width: 20px;
                                            height: 20px;
                                            border-radius: 50%;
                                            background: ${['red', 'blue', 'green', 'yellow'][i % 4]};
                                            border: 2px solid white;
                                        `;
                                        container.appendChild(circle);
                                    });
                                    doc.body.appendChild(container);
                                    return 'OK';
                                } catch(e) {
                                    return 'Error: ' + e.message;
                                }
                            }
                            """,
                            ([(r.x, r.y, r.confidence) for r in results], 2),
                        )
                        print(f"已在页面标记 {len(results)} 个位置")
                    else:
                        print(f"未找到: {arg}")
                else:
                    print("用法: find <图标名称>\n")

            elif action == "clean":
                await bot.page.evaluate("""
                    () => {
                        const existing = document.getElementById('debug-marker');
                        if (existing) existing.remove();
                    }
                """)
                print("已清除标记点\n")

            elif action == "scale":
                print(f"当前比例: {bot.action.scale}\n")

            elif action == "marker":
                parts = arg.split()
                if len(parts) == 2:
                    x, y = int(parts[0]), int(parts[1])
                    await bot.page.evaluate(f"""
                        () => {{
                            const existing = document.getElementById('debug-marker');
                            if (existing) existing.remove();
                            const container = document.createElement('div');
                            container.id = 'debug-marker';
                            container.style.cssText = 'position:fixed;top:0;left:0;pointer-events:none;z-index:99999;';
                            const circle = document.createElement('div');
                            circle.style.cssText = `
                                position: absolute;
                                left: {x}px;
                                top: {y}px;
                                width: 20px;
                                height: 20px;
                                border-radius: 50%;
                                background: red;
                                border: 2px solid white;
                            `;
                            container.appendChild(circle);
                            document.body.appendChild(container);
                        }}
                    """)
                    print(f"已标记: viewport ({x}, {y})\n")
                else:
                    print("用法: marker <x> <y>\n")

            elif action == "ck":
                parts = arg.split()
                if len(parts) == 2:
                    x, y = clamp_click(int(parts[0]), int(parts[1]))
                    await bot.action.click_with_scroll(x, y)
                    print(f"已点击: ({x}, {y})\n")
                else:
                    print("用法: ck <x> <y>\n")

            elif action == "point":
                parts = arg.split()
                if len(parts) == 2:
                    x, y = int(parts[0]), int(parts[1])
                    vx, vy = x // 2, y // 2
                    await bot.page.evaluate(
                        f"""
                        () => {{
                            const existing = document.getElementById('point-marker');
                            if (existing) existing.remove();
                            const container = document.createElement('div');
                            container.id = 'point-marker';
                            container.style.cssText = 'position:fixed;top:0;left:0;pointer-events:none;z-index:99999;';
                            const circle = document.createElement('div');
                            circle.style.cssText = `
                                position: absolute;
                                left: {vx}px;
                                top: {vy}px;
                                width: 20px;
                                height: 20px;
                                border-radius: 50%;
                                background: red;
                                border: 2px solid white;
                            `;
                            container.appendChild(circle);
                            document.body.appendChild(container);
                        }}
                    """
                    )
                    print(f"已标记: ({x}, {y})\n")
                else:
                    print("用法: point <x> <y>\n")

            elif action == "go":
                if arg:
                    await run_workflow(bot, arg)
                else:
                    print("用法: go <工作流名称>\n")

            elif action == "run":
                if arg:
                    print(
                        f"开始循环执行 {arg}，间隔 {RUN_LOOP_SLEEP_MIN}-{RUN_LOOP_SLEEP_MAX} 分钟 (Ctrl+C 停止)\n"
                    )
                    while True:
                        await run_workflow(bot, arg)
                        interval = random.randint(
                            RUN_LOOP_SLEEP_MIN * 60, RUN_LOOP_SLEEP_MAX * 60
                        )
                        print(
                            f"等待 {interval} 秒 ({interval / 60:.1f} 分钟) 后继续... (Ctrl+C 停止)"
                        )
                        await asyncio.sleep(interval)
                else:
                    print("用法: run <工作流名称>\n")

            elif action == "stop":
                print("使用 Ctrl+C 停止\n")

            elif action == "left":
                if arg.isdigit():
                    await drag(bot, "left", int(arg))
                else:
                    print("用法: left <像素>\n")

            elif action == "right":
                if arg.isdigit():
                    await drag(bot, "right", int(arg))
                else:
                    print("用法: right <像素>\n")

            elif action == "up":
                if arg.isdigit():
                    await drag(bot, "up", int(arg))
                else:
                    print("用法: up <像素>\n")

            elif action == "down":
                if arg.isdigit():
                    await drag(bot, "down", int(arg))
                else:
                    print("用法: down <像素>\n")

            elif action == "help" or action == "h":
                print("命令:")
                print("  click <名称>   - 点击单个图标")
                print("  find <名称>   - 查找图标并显示位置")
                print("  clean         - 清除标记点")
                print("  scale         - 刷新截图比例")
                print("  point <x> <y> - 在坐标处显示红点")
                print("  marker <x> <y>- 在坐标处显示标记点")
                print("  ck <x> <y>    - 点击指定坐标")
                print("  go <工作流>   - 执行一次工作流")
                print("  run <工作流>  - 循环执行工作流 (3-5分钟间隔)")
                print("  left <像素>   - 向左拖动")
                print("  right <像素>  - 向右拖动")
                print("  up <像素>     - 向上拖动")
                print("  down <像素>   - 向下拖动")
                print("  screenshot    - 保存截图")
                print("  quit          - 退出")
                print("  ↑ 上箭头      - 载入上次命令\n")

            else:
                print(f"未知命令: {cmd}")
                print("输入 'help' 查看帮助\n")

        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"错误: {e}\n")

    await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())

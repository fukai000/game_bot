import subprocess
import sys

print("""
=== 连接已打开的浏览器 ===

方法1: 使用 Chrome 启动参数
在启动 Chrome 时添加:
--remote-debugging-port=9222

然后用以下地址连接:
ws://localhost:9222/devtools/browser/xxx

方法2: 使用脚本启动浏览器并获取地址

""")

cmd = input("是否启动带调试的浏览器? (y/n): ").strip().lower()

if cmd == "y":
    import asyncio
    import sys

    sys.path.insert(0, ".")
    from core.game_bot import GameBot

    async def start_with_debug():
        bot = GameBot(
            game_url="",
            connect_existing=False,
        )
        await bot.start()

        cdp_info = await bot.page.evaluate("""() => {
            return {
                wsEndpoint: window.navigator.webdriver ? 'connected' : 'no'
            };
        }""")

        print(f"\n浏览器已启动")
        print(f"WebSocket地址: {bot.browser.ws_endpoint}")
        print(f"\n使用以下代码连接:")
        print(
            f'bot = GameBot(connect_existing=True, existing_ws_url="{bot.browser.ws_endpoint}")'
        )

        input("\n按回车关闭浏览器...")
        await bot.stop()

    asyncio.run(start_with_debug())

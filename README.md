# 游戏自动化脚本 - 使用指南 (新版本)

> 支持可拖动游戏画面

## 1. 架构说明

```
game_bot/
├── vision/          # 视觉识别模块
│   └── __init__.py  # Vision 类 - OpenCV 模板匹配
├── action/          # 动作执行模块
│   └── __init__.py  # Action 类 - 点击、拖动
├── core/            # 核心逻辑
│   └── game_bot.py  # GameBot 主类
├── main.py          # 入口
└── capture.py       # 模板采集
```

## 2. 核心类说明

### Vision (视觉识别)
```python
from game_bot.vision import Vision

vision = Vision("assets")

# 模板匹配
result = vision.locate(screenshot, "sign_in", threshold=0.8)
if result:
    print(f"找到目标: ({result.x}, {result.y}), 置信度: {result.confidence}")

# 多模板匹配
result = vision.locate_best(screenshot, ["btn1", "btn2", "btn3"])

# 等待目标出现
result = await vision.wait_for(get_screenshot_fn, "target", timeout=10)
```

### Action (动作执行)
```python
from game_bot.action import Action, Direction

action = Action(page)

# 智能点击 (含随机偏移)
await action.smart_click(x, y)

# 模拟拖动点击
await action.smart_click(x, y, simulate_drag=True)

# 滑动屏幕
await action.swipe(Direction.UP)
await action.swipe(Direction.LEFT)

# 滑动搜索
await action.swipe_search([Direction.UP, Direction.DOWN])
```

### GameBot (主控)
```python
from game_bot.core.game_bot import GameBot, Task

bot = GameBot(game_url="...", assets_dir="assets")

# 添加任务
bot.add_task(Task(
    name="签到",
    template_name="sign_in",  # 动态目标 (模板匹配)
    max_retries=3,
))

bot.add_task(Task(
    name="主城",
    template_name="home_btn",  # 动态目标
    is_static=False,
))

# 执行任务 (自动滑动搜索)
await bot.run_task("签到")

# 手动定位 + 点击
await bot.locate_and_click("target")

# 滑动搜索定位
await bot.locate_and_click_with_search("target", max_swipes=3)

# 回到主城
await bot.go_home()
```

## 3. 阈值调优

### 置信度阈值说明
| 阈值范围 | 适用场景 |
|---------|---------|
| 0.9-1.0 | 高精度匹配，UI 元素固定 |
| 0.8-0.9 | 默认值，大部分场景 |
| 0.7-0.8 | 低对比度、模糊 UI |
| 0.5-0.7 | 宽松匹配，可能误触 |

### 调优建议
```python
# 如果找不到目标
1. 降低阈值: threshold=0.7
2. 增加滑动搜索: max_swipes=5

# 如果误触
1. 提高阈值: threshold=0.9
2. 截图确认模板清晰度
```

## 4. 使用流程

### 4.1 安装依赖
```bash
cd game_bot
pip install opencv-python numpy Pillow playwright
playwright install chromium
```

### 4.2 采集模板
```bash
python capture.py
# 输入: capture sign_in 640 360
```

### 4.3 运行脚本
```bash
python main.py
```

## 5. 任务配置

```python
bot.add_task(Task(
    name="签到",
    template_name="sign_in",
    max_retries=3,
))

bot.add_task(Task(
    name="体力",
    template_name="energy",
    threshold=0.75,  # 可自定义阈值
))
```

## 6. 调试技巧

```python
# 保存截图
screenshot = await bot.get_image()
cv2.imwrite("debug.png", screenshot)

# 打印匹配结果
result = vision.locate(screenshot, "btn")
print(f"置信度: {result.confidence}")

# 手动测试滑动
await action.swipe_search([Direction.UP, Direction.DOWN])
```

## 7. 异常处理

```python
try:
    await bot.run_task("签到")
except Exception as e:
    # 刷新页面重试
    await bot.refresh_page()
    await bot.go_home()
    await bot.run_task("签到")
```

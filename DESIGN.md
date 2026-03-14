# 游戏自动化机器人 - 设计文档

## 1. 项目概述

本项目是一个基于图像识别和 Playwright 浏览器自动化的游戏辅助工具。通过模板匹配定位游戏界面元素，并模拟用户操作实现自动化任务执行。

### 技术栈
- **Python 3.10**: 主要编程语言
- **Playwright 1.58**: 浏览器自动化框架
- **OpenCV (cv2)**: 图像处理与模板匹配
- **NumPy**: 数值计算
- **ChromiteX 138**: 目标浏览器（基于 Chromium 的修改版）

---

## 2. 项目结构

```
game_bot/
├── main.py                 # 主入口，交互式命令行界面
├── workflow.py             # 工作流定义
├── connect_existing.py     # 连接已运行浏览器的脚本
├── capture.py              # 模板采集工具
├── core/
│   ├── __init__.py
│   └── game_bot.py         # 核心机器人类
├── vision/
│   ├── __init__.py         # 视觉识别模块（模板匹配）
│   └── template_matcher.py # 模板匹配工具
├── action/
│   ├── __init__.py         # 动作执行模块
│   └── click_utils.py      # 点击工具
├── utils/
│   ├── __init__.py
│   ├── click_utils.py
│   └── template_matcher.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_game_bot.py
│   └── test_template_matcher.py
└── assets/                 # 模板图片目录
    ├── guke.png
    ├── zhizuo.png
    ├── zhizuo2.png
    ├── queding.png
    ├── jiaofu.png
    ├── gongxi.png
    ├── huayi.png
    └── ...
```

---

## 3. 核心模块设计

### 3.1 Vision 模块 (vision/__init__.py)

负责图像识别和模板匹配。

**主要类：**
- `MatchResult`: 匹配结果数据结构
  - `x, y`: 匹配位置中心坐标
  - `confidence`: 置信度 (0-1)
  - `template_name`: 模板名称

- `Vision`: 视觉识别主类
  - `_load_templates()`: 加载 assets 目录下所有 PNG 文件作为模板
  - `locate()`: 模板匹配，返回单个最佳匹配
  - `locate_all()`: 模板匹配，返回所有匹配结果
  - `locate_best()`: 在多个模板中找最佳匹配
  - `add_template()`: 动态添加模板
  - `save_template()`: 保存模板到文件

**算法：** 使用 OpenCV 的 `cv2.matchTemplate` 进行模板匹配，方法为 `TM_CCOEFF_NORMED`。

---

### 3.2 Action 模块 (action/__init__.py)

负责模拟用户操作。

**主要类：**
- `Direction`: 枚举，定义滑动方向 (UP/DOWN/LEFT/RIGHT)
- `SwipeConfig`: 滑动配置数据类
- `Action`: 动作执行主类
  - `smart_click()`: 智能点击（带随机偏移）
  - `click_with_scroll()`: 先滚动再点击
  - `_native_click()`: 原生鼠标点击
  - `_click_with_drag()`: 模拟拖动点击
  - `swipe()`: 滑动操作
  - `swipe_search()`: 连续滑动搜索

**实现原理：** 使用 Playwright 的 `page.mouse` 和 JavaScript 事件模拟用户操作。

---

### 3.3 GameBot 核心类 (core/game_bot.py)

游戏机器人的核心控制器。

**主要属性：**
```python
game_url: str           # 游戏 URL
user_data_dir: str     # 浏览器用户数据目录（保存登录状态）
assets_dir: str        # 模板图片目录
headless: bool         # 是否无头模式
executable_path: str   # 浏览器可执行文件路径
connect_existing: bool # 是否连接已运行的浏览器
existing_ws_url: str  # 已运行浏览器的 WebSocket URL
```

**主要方法：**
- `start()`: 启动机器人，初始化浏览器
- `stop()`: 停止机器人，关闭浏览器
- `get_screenshot()`: 获取页面截图（字节）
- `get_image()`: 获取截图（NumPy 数组）
- `locate_and_click()`: 查找模板并点击
- `add_task()`: 添加任务

---

## 4. 启动方式

### 4.1 启动 ChromiteX 浏览器

```bash
"/Applications/ChromiteX.app/Contents/MacOS/ChromiteX" --remote-debugging-port=9222
```

### 4.2 运行主程序

```bash
python3 main.py
```

### 4.3 交互命令

| 命令 | 说明 |
|------|------|
| `click <模板名>` | 点击单个图标 |
| `find <模板名>` | 查找图标并显示位置 |
| `go <工作流名>` | 执行一次工作流 |
| `run <工作流名>` | 循环执行工作流 (3-5分钟间隔) |
| `ck <x> <y>` | 点击指定坐标 |
| `point <x> <y>` | 在坐标处显示红点 |
| `marker <x> <y>` | 在坐标处显示标记点 |
| `clean` | 清除所有标记点 |
| `left <像素>` | 向左滑动 |
| `right <像素>` | 向右滑动 |
| `up <像素>` | 向上滑动 |
| `down <像素>` | 向下滑动 |
| `screenshot` | 保存截图 |
| `quit` | 退出 |

---

## 5. 工作流定义

当前工作流定义在 `main.py` 中：

```python
WORKFLOWS = {
    "guke": ["guke", "zhizuo", "zhizuo2", "queding", "jiaofu", "gongxi"],
}
```

工作流执行逻辑：
1. 查找主触发器（如 guke）
2. 在指定范围内查找 (250-800, 550-1000)
3. 依次执行后续步骤
4. 失败时进入恢复模式（点击回到华亿）
5. 每次工作流完成后等待1.5秒

---

## 6. 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `WORKFLOW_DELAY` | 0.5s | 步骤间延迟 |
| `RETRY_COUNT` | 3 | 匹配重试次数 |
| `RETRY_DELAY` | 1.0s | 重试间隔 |
| `DEFAULT_THRESHOLD` | 0.8 | 匹配阈值 |
| `guke阈值` | 0.6 | guke图标匹配阈值 |

---

## 7. 坐标范围限制

- **查找范围**: 仅在 (250-800, 550-1000) 内查找 guke
- **点击范围**: 所有点击事件限制在 (200-930, 180-1450) 范围内
- **截图坐标**: 截图分辨率为视口2倍，点击时会自动转换

---

## 8. 恢复模式

工作流执行失败后进入恢复模式：
1. 查找 huayi 图标（阈值0.6）
2. 找到后等待恢复
3. 未找到时点击 (600, 280) 附近
4. 最多尝试10次

---

## 9. 扩展开发

### 9.1 添加新模板
将模板图片放入 `assets/` 目录，命名为 `<名称>.png`

### 9.2 添加新工作流
在 `main.py` 的 `WORKFLOWS` 字典中添加新条目

### 9.3 添加新动作
在 `action/__init__.py` 的 `Action` 类中添加新方法

---

## 10. 注意事项

1. 浏览器兼容性：项目使用 ChromiteX 138，需要对应的浏览器版本
2. 模板匹配阈值：可根据实际效果调整 0.3-0.9
3. 窗口大小：默认视口 1280x720
4. 截图比例：游戏内截图与视口比例为 2:1
5. 按 Ctrl+C 可停止 run 命令的循环执行

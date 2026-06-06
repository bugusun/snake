# 程序化贴图贪吃蛇

一个使用 `pygame` 编写的中文界面贪吃蛇小游戏。项目包含中文主菜单、地图选择、模式选择、特殊食物、连击奖励、粒子反馈、死亡闪屏和蛇身前进插值动画。游戏贴图由程序自动生成，不依赖外部图片素材。

## 运行方式

建议使用 Python 3.10 或更高版本。

```bash
pip install -r requirements.txt
python main.py
```

无窗口冒烟验证：

```bash
python -m snake_game.validation
```

## 主要内容

- 中文主菜单、侧栏和提示文本。
- 七张内置地图：`青翠草地`、`石阵花园`、`螺旋遗迹`、`十字回廊`、`双环迷宫`、`桥岛水道`、`栅栏长廊`。
- 三种模式：`经典模式`、`疾速模式`、`穿墙模式`。
- 三类食物：`普通苹果`、`金苹果`、`冰莓`。
- 蛇身与蛇尾更宽、更方，便于观察地图方格位置。
- `assets/generated/` 中的 PNG 贴图会在运行时自动生成或刷新。

## 按键操作

| 按键 | 功能 |
| --- | --- |
| `方向键` / `W A S D` | 控制移动方向 |
| `Enter` / `Space` | 菜单确认、暂停继续、结束后重开 |
| `P` | 暂停或继续 |
| `R` | 游戏结束后重新开始 |
| `Esc` | 暂停、返回菜单或退出 |

## 项目结构

```text
.
|-- main.py
|-- requirements.txt
|-- README.md
|-- snake_game/
|   |-- __init__.py
|   |-- assets.py
|   |-- fonts.py
|   |-- game.py
|   |-- maps.py
|   |-- menu.py
|   |-- rules.py
|   |-- settings.py
|   `-- validation.py
`-- assets/
    `-- .gitkeep
```

## 说明

- 中文源码和文档使用 UTF-8 编码。
- `assets/generated/`、`__pycache__/`、虚拟环境和本地历史资料不会提交到仓库。
- 如果系统没有中文字体，程序会回退到 `pygame` 默认字体；建议安装 `Microsoft YaHei`、`SimHei` 或 `Noto Sans CJK SC` 等中文字体。

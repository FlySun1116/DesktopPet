# 架构说明

## 设计目标

采用小型分层结构：配置和角色包提供数据，状态机决定“做什么”，行为控制器决定“何时做”，动画播放器决定“显示哪一帧”，窗口只负责呈现与交互。这样可在不启动桌面的情况下测试大部分规则。

```text
Application
├─ ConfigManager ── %APPDATA% 用户配置
├─ CharacterManager ── character.json + 动作目录
├─ PetStateMachine ← BehaviorController / 鼠标事件
├─ AnimationPlayer ← 状态变化，输出当前 QPixmap
├─ PetWindow ← 帧、拖拽、边界与菜单
├─ TrayManager / SettingsWindow
└─ ResourceManager / ScreenManager / StartupManager
```

## 关键数据流

启动时先合并只读默认配置与用户配置，再解析角色清单。状态机初始为 `IDLE`，窗口根据状态请求动作；播放器预加载并缓存已缩放帧。单次动作结束通过回调通知状态机，而不是播放器自行选择业务状态。自动行为仅在未暂停、非拖拽、非单次高优先级动作时提出转换。

拖拽开始进入 `DRAGGED`；移动位置经当前显示器可用区域钳制；释放后依据离“地面”的距离进入 `FALL` 或 `IDLE`。行走触边由屏幕服务报告，控制器改变方向，播放器仅处理水平镜像。

## 状态优先级与冲突

`DRAGGED` 具有交互优先级。`SURPRISED`、`WAVE`、`HAPPY`、`FALL` 属于单次动作，结束后回到 `IDLE` 或合法上下文状态。`SLEEP` 可被点击唤醒。行为控制器必须使用单一调度计时器并设置最小切换间隔，避免多个计时器同时写状态。

## 路径与持久化

只读资源通过统一函数解析：源码模式以项目根为基准，PyInstaller 模式以 `_MEIPASS`/可执行文件资源目录为基准。用户配置、日志和缓存位于 `%APPDATA%\AnimePersonDesktopPet`，不得写入安装目录。角色动作路径始终相对 `character.json` 解析。

## 可测试性

纯函数负责自然排序、递归配置合并、屏幕边界计算和路径选择。状态机不依赖 QWidget。Qt 集成测试使用 offscreen 平台，但托盘、透明窗口、DPI、多屏和点击透明区域仍列入 Windows 人工验收。


# AGENTS.md

## 项目目标与技术栈

本项目交付 Windows 10/11 上稳定、可替换素材的透明动漫人物桌宠。优先级：可运行 > 稳定 > 人物一致性 > 动画自然 > 代码清晰 > 功能数量。技术栈为 Python 3.11+、PySide6、Pillow、pytest、PyInstaller。

## 模块边界

- `app/animation_player.py`：PNG 序列加载、自然排序、缓存、循环/单次播放和镜像。
- `app/state_machine.py`：纯状态与转换规则，不直接操作窗口。
- `app/behavior_controller.py`：随机行为与节流，不承载渲染。
- `app/pet_window.py`：窗口、鼠标与屏幕位置；不硬编码素材路径。
- `app/config_manager.py`：默认/用户配置合并和持久化。
- `app/character_manager.py`：动态解析角色包。
- `app/resource_manager.py`：源码和 PyInstaller 下的只读资源路径、用户数据路径。
- 托盘、设置、开机启动、日志各自独立，避免重复定时器和隐式全局状态。

## 代码规范

- 使用类型标注、小而明确的函数、`pathlib.Path` 和可读日志；公共行为应有测试。
- 默认配置是只读资源；用户可变数据写入 `%APPDATA%\AnimePersonDesktopPet`。
- GUI 状态变化在 Qt 主线程进行；QObject 生命周期明确，退出时停止所有计时器。
- 资源路径不得依赖当前工作目录，不得硬编码开发机绝对路径。
- 不吞掉异常；对可恢复的配置/素材错误记录原因并采用安全回退。

## 素材规则

- **永远不得覆盖、删除或改写 `images/` 中的真人原始照片。** 不将其放入构建包或提交到不必要的外部服务。
- **不得把占位素材冒充正式角色素材。** 占位素材必须显著标注，仅用于程序验证。
- 正式帧为真实 RGBA 透明 PNG，统一画布、连续编号、底部中心锚点；禁止棋盘格、白/黑底、白边、裁切和明显脚底漂移。
- 跨帧保持发型、五官、服装、配饰、色板和年龄感一致。正式素材必须有人物授权和人工相似度复核。

## 常用命令

```powershell
python main.py
pytest
python scripts/validate_assets.py
python scripts/verify_installation.py
build.bat
```

修改动画播放器、状态机、行为控制器、边界或资源路径后必须运行 `pytest`，并至少手动验证 idle、walk 镜像、单次动作结束、拖拽释放和屏幕边界。修改 `character.json` 或任何角色图片后必须运行 `scripts/validate_assets.py` 并检查生成报告和动作预览。

## Windows 注意事项

- 位置计算使用当前显示器的 `availableGeometry()`，兼顾任务栏、高 DPI、负坐标与多屏。
- 关闭主窗口通常隐藏到托盘；只有明确“退出”才结束进程，退出前清理托盘和计时器。
- 开机启动使用当前用户范围，路径加引号，禁用时只移除本应用条目。
- PyInstaller 首选 `onedir` 和无控制台模式；打包后仍写 `%APPDATA%`，绝不写 `Program Files`。

## 完成任务前检查清单

- [ ] 没有覆盖真人照片，也没有把 `images/` 加入发布包。
- [ ] 所有新增/修改测试实际运行并报告真实结果。
- [ ] 素材变更已运行验证脚本；占位/正式状态说明准确。
- [ ] 透明、锚点、帧序、动作回退和边界已经检查。
- [ ] 默认配置、用户配置和打包资源路径均验证。
- [ ] README、架构和打包说明与实现保持一致。
- [ ] 未验证的 Windows、视觉或安装包行为明确列为限制，不虚构通过。


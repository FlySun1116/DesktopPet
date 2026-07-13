# Windows 打包与发布

## 前置检查

在 Windows 10/11、Python 3.11+ 的干净虚拟环境中安装依赖，依次运行：

```powershell
pytest
python scripts/validate_assets.py
python scripts/verify_installation.py
```

任一失败都不应继续发布。确认 `images/`、`artwork/drafts/`、日志、用户配置和生成缓存不在构建输入中。

## PyInstaller

第一阶段使用 `onedir`，便于检查资源。构建应使用无控制台模式，收集 `assets/`、`config/` 和程序图标。运行时只读资源经 `resource_path()` 定位；用户数据始终写 `%APPDATA%\AnimePersonDesktopPet`。

```powershell
build.bat
```

期望目录：

```text
dist/AnimePersonDesktopPet/
release/AnimePersonDesktopPet-Windows-x64.zip
```

## 干净机验收

在未安装 Python 的 Windows 测试机解压并启动：确认无控制台窗口、桌宠透明、托盘可用、隐藏/恢复和显式退出正常；逐动作播放；拖动到四边与任务栏附近；修改并重启验证设置；在 100%/125%/150% 缩放及可用的多屏环境检查位置。检查 `%APPDATA%` 写入，确认安装目录未产生用户数据。

## 发布内容审计

- 包含：可执行程序、Qt 运行库、`assets/`、`config/`、必要许可证和 README。
- 排除：`images/` 真人照片、测试缓存、日志、报告中的私密路径、原始生成输入、密钥和本机用户配置。
- 压缩包解压后应只有一个顶层产品目录；记录版本、构建时间和测试环境。

未在真实 Windows 环境完成上述检查时，只能表述为“已生成构建配置/产物，尚未完成 Windows 实机验证”，不得宣称 EXE 已验收。


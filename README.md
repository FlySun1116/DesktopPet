# Anime Person Desktop Pet

面向 Windows 10/11 的透明动漫人物桌宠。程序使用 PySide6 播放透明 PNG 序列帧，支持自动行为、拖拽、单击/双击反馈、托盘、设置持久化与 PyInstaller 打包。

> **素材状态（重要）**：`images/ZhangLe/` 中的 16 张真人参考照片已完成可见特征分析，照片属于私密输入且不会进入代码仓库或发行包。`artwork/hatch_run/` 已有审核通过的正式角色基准图、标准动作行 0–8 和完整 v2 方向图集。应用角色包的 9 组动作现已全部替换为 `GENERATED_REVIEWED` 正式素材，角色顶层 `placeholder` 已解除。

## 当前效果

第一版已实现无边框、透明、始终置顶且限制在可用屏幕内的桌宠窗口。角色可待机、行走、坐下、睡觉、挥手、开心、惊讶、被拖拽及下落；全部动作均读取 `assets/characters/main_character/` 中的正式审核素材。

## 真人照片输入与隐私

- 将获授权照片放入 `images/<人物名>/`，优先提供正面、左右 45°、侧面、全身与自然表情照片。
- 不要使用来源不明、未获授权、涉及未成年人或不适合处理的照片。
- 原始照片不得覆盖、裁剪后冒充原件、写入构建包或上传到无关服务。
- 对照片只做可见特征分析，不推断身份、族裔、健康、性格等敏感信息。
- 发布角色或安装包前，应再次获得肖像权人对用途和传播范围的确认。

## 动漫角色制作流程

1. 盘点参考照片并选择清晰主参考；记录仅基于可见内容的一致性锚点。
2. 先制作正面、45°、侧面、背面、表情和色板的角色设定图。
3. 审核发型、五官、服装、配饰、色板与 2.5–3.5 头身比例。
4. 逐动作制作透明 PNG 序列，统一 768×768 画布与底部中心锚点。
5. 运行素材检查；修正白边、透明孔洞、裁切、编号和脚底漂移。
6. 在桌宠中逐动作视觉验收后才可标记为正式素材。

详见 [素材流水线](docs/asset_pipeline.md) 与 [角色风格规范](docs/character_style_guide.md)。

## 项目结构

```text
app/                         桌宠程序模块
assets/characters/           角色配置和 PNG 序列
config/default_config.json   只读默认配置
images/                      真人参考输入（不要打包）
artwork/                     设定图与制作过程文件
scripts/                     素材检查、预览和构建辅助工具
docs/                        架构、素材与打包文档
tests/                       pytest 单元测试
reports/                     生成的检查报告
main.py                      程序入口
```

## 安装与启动

要求 Python 3.11+。建议使用虚拟环境：

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

也可运行 `run.bat`。若 Qt 报平台插件错误，请确认虚拟环境中的 PySide6 安装完整，且不要混用多个 Python。

## 素材生成、检查与替换

素材生成必须以获授权照片为人物参考，先生成角色设定，再生成动作；不能把程序绘制的几何占位图当作正式图。已审核的生成源、标准行和 QA 预览保存在 `artwork/hatch_run/` 与 `artwork/remaining_actions/`。占位素材脚本仅供重新联调，不应覆盖当前正式角色包：

```powershell
python scripts/generate_placeholder_assets.py
python scripts/validate_assets.py
python scripts/build_character_preview.py
```

替换人物时：复制新的角色目录，填写 `character.json`，为每个动作放入连续编号的透明 PNG，然后运行素材检查。不要覆盖 `images/` 中的原照。检查报告位于 `reports/asset_validation_report.md`。

## `character.json`

核心字段：`id`、`name`、`version`、`canvas_size`、`anchor`、`default_scale` 和 `animations`。每个动作声明相对 `character.json` 的 `folder`、`fps` 与 `loop`；程序动态读取，不应硬编码动作绝对路径。`walk` 通常只制作一个方向，另一方向由播放器水平镜像。

## 设置

设置窗口可调整自动移动、角色缩放、移动速度、动画速度、始终置顶、开机启动及角色位置。默认配置保持只读；用户配置保存到 `%APPDATA%\AnimePersonDesktopPet\user_config.json`。损坏或缺字段时回退默认值。

## 测试与素材验证

```powershell
pytest
python scripts/validate_assets.py
python scripts/verify_installation.py
```

GUI 测试可设置 `QT_QPA_PLATFORM=offscreen`，但透明窗口、托盘、缩放、多显示器和拖拽仍需在 Windows 桌面人工验收。

当前实测：`pytest` 为 **15 passed, 1 skipped**；素材验证为 **0 errors, 0 warnings**；offscreen 启动检查退出码为 **0**。

## Windows 打包

```powershell
build.bat
```

已使用 PyInstaller `onedir`、无控制台模式生成 `dist/AnimePersonDesktopPet/`，并生成 `release/AnimePersonDesktopPet-Windows-x64.zip`。源码离屏启动验证通过；本轮最新未签名 EXE 被当前 Windows 应用控制策略阻止启动，因此尚未完成最新发布包的存活验证。构建包包含 `assets/` 和 `config/`，不包含 `images/`、本地日志或用户配置。详见 [打包说明](docs/packaging.md)。

## 常见错误

- **只有空白窗口**：检查动作目录、PNG 透明度、`character.json` 路径和素材报告。
- **白色/黑色方框**：图片没有真实 alpha 通道，或窗口未启用透明背景。
- **动作顺序错误**：使用 `001.png` 起始的连续编号，避免 `1, 10, 2` 字典序问题。
- **角色走出屏幕**：必须使用当前屏幕 `availableGeometry()` 而非完整分辨率。
- **打包后找不到资源**：所有只读资源应通过统一资源路径函数解析 PyInstaller 临时目录。
- **设置无法保存**：不要写安装目录；检查 `%APPDATA%` 权限。
- **退出后仍运行**：从托盘“退出”触发显式退出；关闭主窗默认仅隐藏。

## 当前限制

- 9 组应用动作均为正式审核素材；五组补充动作的联系表位于 `reports/remaining_actions_contact_sheet.png`。
- hatch-pet v2 角色包已通过验证；少数中间方向仍有非阻塞的语义/连续性警告，详见 `artwork/hatch_run/qa/direction-semantics.json` 与 `look-continuity.json`。
- 自动化测试不能替代人物相似度、动作自然度、透明边缘与高 DPI 的人工视觉检查。
- 最新安装包构建成功，但被当前 Windows 应用控制策略阻止启动；仍需在允许执行未签名程序的 Windows 环境中完成存活、开机启动、托盘交互、高 DPI 与多显示器验收。
- 第一版无声音系统，仅预留配置。

## 可扩展方向

- 多角色切换及角色包导入导出。
- 更精细的行为调度、屏幕间移动与交互热区。
- 素材制作端的帧间一致性、光流预览和自动锚点校正。

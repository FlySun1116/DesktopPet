from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CHAR = ROOT / "assets" / "characters" / "main_character"
REPORT = ROOT / "reports" / "asset_validation_report.md"


def validate() -> tuple[list[str], list[str], list[str]]:
    errors, warnings, details = [], [], []
    try: meta = json.loads((CHAR / "character.json").read_text(encoding="utf-8"))
    except Exception as exc: return [f"character.json 无法读取：{exc}"], [], []
    expected = tuple(meta.get("canvas_size", [])); placeholder = bool(meta.get("placeholder"))
    if placeholder: warnings.append("当前角色包被明确标记为 PLACEHOLDER，不可作为正式角色素材发布。")
    for action, spec in meta.get("animations", {}).items():
        folder = CHAR / spec.get("folder", action); frames = sorted(folder.glob("*.png"))
        if not frames: errors.append(f"{action}: 缺少 PNG 帧"); continue
        numeric = [p.name == f"{i:03}.png" for i, p in enumerate(frames, 1)]
        if not all(numeric): errors.append(f"{action}: 帧命名必须从 001.png 连续编号")
        bottoms = []
        for frame in frames:
            try:
                with Image.open(frame) as im:
                    if im.size != expected: errors.append(f"{action}/{frame.name}: 尺寸 {im.size} != {expected}")
                    if im.mode != "RGBA": errors.append(f"{action}/{frame.name}: 缺少 RGBA 透明通道")
                    alpha = im.getchannel("A"); bbox = alpha.getbbox()
                    if bbox is None: errors.append(f"{action}/{frame.name}: 完全透明")
                    else:
                        bottoms.append(bbox[3]);
                        if alpha.crop((0,0,im.width,1)).getbbox() or alpha.crop((0,im.height-1,im.width,im.height)).getbbox(): warnings.append(f"{action}/{frame.name}: 内容接触上下边缘")
            except Exception as exc: errors.append(f"{action}/{frame.name}: {exc}")
        if action not in {"dragged", "fall"} and bottoms and max(bottoms)-min(bottoms) > 12:
            warnings.append(f"{action}: 脚底/边界漂移 {max(bottoms)-min(bottoms)}px")
        details.append(f"- `{action}`: {len(frames)} 帧")
    if not (CHAR / "preview.png").exists(): errors.append("缺少 preview.png")
    return errors, list(dict.fromkeys(warnings)), details


def main() -> int:
    errors, warnings, details = validate(); REPORT.parent.mkdir(parents=True, exist_ok=True)
    meta = json.loads((CHAR / "character.json").read_text(encoding="utf-8"))
    placeholder = bool(meta.get("placeholder"))
    status = ("通过（占位素材）" if placeholder else "通过（正式素材）") if not errors else "失败"
    material = "PLACEHOLDER / 非正式素材" if placeholder else "GENERATED_REVIEWED / 正式审核素材"
    lines = ["# 素材校验报告", "", f"- 状态：**{status}**", f"- 素材类型：**{material}**", "- 画布要求：768×768 RGBA", "", "## 动作", *details, "", "## 错误"]
    lines += [f"- {x}" for x in errors] or ["- 无"]
    lines += ["", "## 警告"] + ([f"- {x}" for x in warnings] or ["- 无"])
    REPORT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(f"Asset validation: {status}; errors={len(errors)}, warnings={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__": raise SystemExit(main())

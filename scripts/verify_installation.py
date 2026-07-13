from pathlib import Path
import importlib.util, json

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors=[]
    for module in ("PySide6","PIL"):
        if importlib.util.find_spec(module) is None: errors.append(f"缺少 Python 模块：{module}")
    for path in (ROOT/"main.py", ROOT/"config/default_config.json", ROOT/"assets/characters/main_character/character.json"):
        if not path.exists(): errors.append(f"缺少文件：{path.relative_to(ROOT)}")
    try: meta = json.loads((ROOT/"assets/characters/main_character/character.json").read_text(encoding="utf-8"))
    except Exception as exc: errors.append(f"角色配置无效：{exc}")
    if errors:
        print("Installation verification failed:\n- " + "\n- ".join(errors)); return 1
    status = "PLACEHOLDER" if meta.get("placeholder") else "GENERATED_REVIEWED"
    print(f"Installation verification passed (asset status: {status}).")
    return 0


if __name__ == "__main__": raise SystemExit(main())

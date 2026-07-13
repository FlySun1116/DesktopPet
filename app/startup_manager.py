import sys
from pathlib import Path


def set_startup(enabled: bool) -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    command = f'"{Path(sys.executable)}"'
    if not getattr(sys, "frozen", False):
        command += f' "{Path(sys.argv[0]).resolve()}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, "AnimePersonDesktopPet", 0, winreg.REG_SZ, command)
            else:
                try: winreg.DeleteValue(key, "AnimePersonDesktopPet")
                except FileNotFoundError: pass
        return True
    except OSError:
        return False

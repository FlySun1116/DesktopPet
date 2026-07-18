import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from .behavior_controller import BehaviorController
from .character_manager import CharacterManager
from .chat_client import ChatClient
from .chat_window import ChatWindow
from .config_manager import ConfigManager
from .env_manager import load_project_env
from .pet_window import PetWindow
from .resource_manager import resource_path
from .settings_window import SettingsWindow
from .startup_manager import set_startup
from .state_machine import PetStateMachine
from .tray_manager import TrayManager


class DesktopPetApplication(QApplication):
    def __init__(self, argv=None):
        super().__init__(argv or sys.argv); self.setQuitOnLastWindowClosed(False); self.setApplicationName("AnimePersonDesktopPet")
        load_project_env()
        self.setWindowIcon(QIcon(str(resource_path("assets", "app_icon", "app_icon.png"))))
        self.config = ConfigManager(); self.character = CharacterManager(); self.pet = PetWindow(self.config, self.character, self)
        self.machine = PetStateMachine(self); self.pet.bind_state_machine(self.machine)
        self.behavior = BehaviorController(self.pet, self.config, self); self.tray = TrayManager(self); self.tray.show()
        self.chat_client = ChatClient(self.config, self); self.chat_window: ChatWindow | None = None
        self.aboutToQuit.connect(self._shutdown)
        self.pet.reset_position(); self.pet.show(); self.machine.transition(self.machine.state, force=True)

    def show_settings(self):
        SettingsWindow(self.config, self._settings_saved, self.pet).exec()

    def _settings_saved(self):
        self.pet.apply_settings(); set_startup(bool(self.config.get("start_on_boot", False)))
        self.behavior.resume() if self.config.get("auto_move", True) else self.behavior.pause()

    def show_about(self): QMessageBox.about(self.pet, "关于", "真人动漫形象桌宠\nPySide6 版")

    def show_chat(self):
        if self.chat_window is None:
            self.chat_window = ChatWindow(self.chat_client, self.pet)
        self.chat_window.refresh_status()
        self.chat_window.show()
        self.chat_window.raise_()
        self.chat_window.activateWindow()
        self.chat_window.focus_input()

    def _shutdown(self):
        self.chat_client.cancel()
        if self.chat_window is not None:
            self.chat_window.hide()


def run() -> int:
    return DesktopPetApplication().exec()

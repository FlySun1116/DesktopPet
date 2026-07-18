from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayManager(QSystemTrayIcon):
    def __init__(self, application):
        super().__init__(application.windowIcon(), application)
        menu = QMenu()
        for text, slot in [("显示桌宠", application.pet.show), ("隐藏桌宠", application.pet.hide), ("AI 聊天", application.show_chat), ("暂停", application.behavior.pause), ("恢复", application.behavior.resume), ("重置位置", application.pet.reset_position), ("设置", application.show_settings), ("关于", application.show_about), ("退出", application.quit)]: menu.addAction(text, slot)
        self.setContextMenu(menu); self.activated.connect(lambda reason: application.pet.show() if reason == self.Trigger else None)

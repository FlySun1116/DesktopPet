from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFormLayout, QPushButton, QVBoxLayout)


class SettingsWindow(QDialog):
    def __init__(self, config, on_saved, parent=None):
        super().__init__(parent)
        self.config, self.on_saved = config, on_saved
        self.setWindowTitle("桌宠设置")
        form = QFormLayout()
        self.auto = QCheckBox(); self.auto.setChecked(config.get("auto_move", True))
        self.top = QCheckBox(); self.top.setChecked(config.get("always_on_top", True))
        self.startup = QCheckBox(); self.startup.setChecked(config.get("start_on_boot", False))
        self.scale = QDoubleSpinBox(); self.scale.setRange(.15, 1.0); self.scale.setSingleStep(.05); self.scale.setValue(config.get("character_scale", .36))
        self.move = QDoubleSpinBox(); self.move.setRange(20, 500); self.move.setValue(config.get("move_speed", 100))
        self.anim = QDoubleSpinBox(); self.anim.setRange(.25, 3); self.anim.setSingleStep(.1); self.anim.setValue(config.get("animation_speed", 1))
        for label, widget in [("自动移动", self.auto), ("始终置顶", self.top), ("开机启动", self.startup), ("角色缩放", self.scale), ("移动速度", self.move), ("动画速度", self.anim)]: form.addRow(label, widget)
        reset = QPushButton("恢复默认设置", clicked=self._reset)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, accepted=self._save, rejected=self.reject)
        layout = QVBoxLayout(self); layout.addLayout(form); layout.addWidget(reset); layout.addWidget(buttons)

    def _save(self):
        for key, val in [("auto_move", self.auto.isChecked()), ("always_on_top", self.top.isChecked()), ("start_on_boot", self.startup.isChecked()), ("character_scale", self.scale.value()), ("move_speed", self.move.value()), ("animation_speed", self.anim.value())]: self.config.set(key, val)
        self.config.save(); self.on_saved(); self.accept()

    def _reset(self):
        self.config.reset(); self.on_saved(); self.accept()

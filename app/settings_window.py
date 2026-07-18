from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from .chat_client import ModelListClient, read_api_key, read_base_url
from .env_manager import API_KEY_ENV, BASE_URL_ENV, save_env_value


class SettingsWindow(QDialog):
    def __init__(self, config, on_saved, parent=None):
        super().__init__(parent)
        self.config, self.on_saved = config, on_saved
        self.setWindowTitle("桌宠设置")
        self.model_client = ModelListClient(self)
        self.model_client.models_received.connect(self._models_received)
        self.model_client.error.connect(self._model_error)
        form = QFormLayout()
        self.auto = QCheckBox(); self.auto.setChecked(config.get("auto_move", True))
        self.top = QCheckBox(); self.top.setChecked(config.get("always_on_top", True))
        self.startup = QCheckBox(); self.startup.setChecked(config.get("start_on_boot", False))
        self.scale = QDoubleSpinBox(); self.scale.setRange(.15, 1.0); self.scale.setSingleStep(.05); self.scale.setValue(config.get("character_scale", .36))
        self.move = QDoubleSpinBox(); self.move.setRange(20, 500); self.move.setValue(config.get("move_speed", 100))
        self.anim = QDoubleSpinBox(); self.anim.setRange(.25, 3); self.anim.setSingleStep(.1); self.anim.setValue(config.get("animation_speed", 1))
        for label, widget in [("自动移动", self.auto), ("始终置顶", self.top), ("开机启动", self.startup), ("角色缩放", self.scale), ("移动速度", self.move), ("动画速度", self.anim)]: form.addRow(label, widget)

        self.api_status = QLabel("API Key 和地址保存在项目根目录 .env（明文，请勿提交）")
        self.chat_api_key = QLineEdit(read_api_key() or "")
        self.chat_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.chat_api_key.setPlaceholderText("填写 OpenAI 兼容 API Key")
        self.chat_base_url = QLineEdit(read_base_url(config.get("chat.base_url", "https://api.openai.com/v1")))
        self.chat_model = QComboBox()
        self.chat_model.setEditable(True)
        self.chat_model.addItem(str(config.get("chat.model", "gpt-4o-mini")))
        self.refresh_models = QPushButton("从 API 获取模型")
        self.refresh_models.clicked.connect(self._fetch_models)
        self.chat_temperature = QDoubleSpinBox(); self.chat_temperature.setRange(0.0, 2.0); self.chat_temperature.setSingleStep(0.1); self.chat_temperature.setValue(float(config.get("chat.temperature", 0.7)))
        self.chat_timeout = QSpinBox(); self.chat_timeout.setRange(5, 300); self.chat_timeout.setValue(int(config.get("chat.timeout_seconds", 60)))
        self.chat_max_rounds = QSpinBox(); self.chat_max_rounds.setRange(1, 30); self.chat_max_rounds.setValue(int(config.get("chat.max_context_rounds", 8)))
        self.chat_system_prompt = QTextEdit(config.get("chat.system_prompt", "你是一个可爱、简洁的桌宠助手。"))
        self.chat_system_prompt.setFixedHeight(72)
        for label, widget in [
            ("密钥存储", self.api_status),
            ("API Key", self.chat_api_key),
            ("聊天 API 地址", self.chat_base_url),
            ("聊天模型", self.chat_model),
            ("模型列表", self.refresh_models),
            ("温度", self.chat_temperature),
            ("超时（秒）", self.chat_timeout),
            ("上下文轮数", self.chat_max_rounds),
            ("系统提示词", self.chat_system_prompt),
        ]: form.addRow(label, widget)

        reset = QPushButton("恢复默认设置", clicked=self._reset)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, accepted=self._save, rejected=self.reject)
        layout = QVBoxLayout(self); layout.addLayout(form); layout.addWidget(reset); layout.addWidget(buttons)

    def _fetch_models(self):
        base_url = self.chat_base_url.text().strip()
        api_key = self.chat_api_key.text().strip()
        if not base_url or not api_key:
            QMessageBox.warning(self, "无法获取模型", "请先填写 API 地址和 API Key。")
            return
        self.refresh_models.setEnabled(False)
        self.refresh_models.setText("正在获取…")
        self.model_client.fetch(base_url, api_key)

    def _models_received(self, models):
        selected = self.chat_model.currentText().strip()
        self.chat_model.clear()
        self.chat_model.addItems(models)
        if selected:
            index = self.chat_model.findText(selected)
            if index < 0:
                self.chat_model.insertItem(0, selected)
                index = 0
            self.chat_model.setCurrentIndex(index)
        self.refresh_models.setEnabled(True)
        self.refresh_models.setText("从 API 获取模型")

    def _model_error(self, message):
        self.refresh_models.setEnabled(True)
        self.refresh_models.setText("从 API 获取模型")
        QMessageBox.warning(self, "获取模型失败", message)

    def _save(self):
        for key, val in [("auto_move", self.auto.isChecked()), ("always_on_top", self.top.isChecked()), ("start_on_boot", self.startup.isChecked()), ("character_scale", self.scale.value()), ("move_speed", self.move.value()), ("animation_speed", self.anim.value())]: self.config.set(key, val)
        base_url = self.chat_base_url.text().strip()
        api_key = self.chat_api_key.text().strip()
        model = self.chat_model.currentText().strip()
        system_prompt = self.chat_system_prompt.toPlainText().strip()
        if not base_url:
            base_url = "https://api.openai.com/v1"
        parsed_url = QUrl(base_url)
        if not parsed_url.isValid() or parsed_url.scheme() not in ("http", "https") or not parsed_url.host():
            QMessageBox.warning(self, "设置无效", "API 地址必须是有效的 HTTP 或 HTTPS 地址。")
            return
        if not model:
            model = "gpt-4o-mini"
        if not system_prompt:
            system_prompt = "你是一个可爱、简洁的桌宠助手。"
        save_env_value(API_KEY_ENV, api_key)
        save_env_value(BASE_URL_ENV, base_url)
        self.config.set("chat.base_url", base_url)
        self.config.set("chat.model", model)
        self.config.set("chat.temperature", self.chat_temperature.value())
        self.config.set("chat.timeout_seconds", self.chat_timeout.value())
        self.config.set("chat.max_context_rounds", self.chat_max_rounds.value())
        self.config.set("chat.system_prompt", system_prompt)
        self.config.save(); self.on_saved(); self.accept()

    def _reset(self):
        self.config.reset(); self.on_saved(); self.accept()

    def closeEvent(self, event):
        self.model_client.cancel()
        super().closeEvent(event)

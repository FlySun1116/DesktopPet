from __future__ import annotations

import json
import logging
from typing import Any

from PySide6.QtCore import QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from .env_manager import API_KEY_ENV, BASE_URL_ENV, read_env_value

logger = logging.getLogger(__name__)


def read_api_key() -> str | None:
    return read_env_value(API_KEY_ENV)


def read_base_url(default: str = "https://api.openai.com/v1") -> str:
    return read_env_value(BASE_URL_ENV) or default


def build_chat_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def build_models_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/models"
    return f"{base}/v1/models"


def parse_model_ids(body: bytes) -> list[str]:
    data = json.loads(body.decode("utf-8"))
    items = data.get("data")
    if not isinstance(items, list):
        raise ValueError("响应中缺少 data 模型列表")
    model_ids = {
        item["id"].strip()
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()
    }
    return sorted(model_ids, key=str.casefold)


def trim_context_messages(
    messages: list[dict[str, str]],
    system_prompt: str,
    max_rounds: int,
) -> list[dict[str, str]]:
    system = {"role": "system", "content": system_prompt}
    history = [message for message in messages if message.get("role") != "system"]
    if max_rounds <= 0:
        return [system]
    max_messages = max_rounds * 2
    if len(history) > max_messages:
        history = history[-max_messages:]
    return [system, *history]


def build_request_payload(
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    stream: bool = True,
) -> dict[str, Any]:
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }


def parse_sse_data_payload(payload: str) -> tuple[str | None, bool]:
    payload = payload.strip()
    if not payload:
        return None, False
    if payload == "[DONE]":
        return None, True
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None, False
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None, False
    choice = choices[0]
    if not isinstance(choice, dict):
        return None, False
    delta = choice.get("delta", {})
    if not isinstance(delta, dict):
        return None, False
    content = delta.get("content")
    if isinstance(content, str) and content:
        return content, False
    return None, False


class SseStreamParser:
    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, text: str) -> tuple[list[str], bool]:
        self._buffer += text
        deltas: list[str] = []
        done = False
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")
            if not line or not line.startswith("data:"):
                continue
            payload = line[5:].lstrip()
            delta, is_done = parse_sse_data_payload(payload)
            if delta:
                deltas.append(delta)
            if is_done:
                done = True
        return deltas, done


def map_http_error(status_code: int, body: str) -> str:
    if status_code == 401:
        return "API 密钥无效或未授权，请检查 DESKTOP_PET_API_KEY。"
    if status_code == 429:
        return "请求过于频繁，请稍后再试。"
    if status_code >= 500:
        return "服务端暂时不可用，请稍后再试。"
    detail = body.strip()
    if detail:
        return f"请求失败（HTTP {status_code}）：{detail[:240]}"
    return f"请求失败（HTTP {status_code}）。"


class ChatClient(QObject):
    delta_received = Signal(str)
    finished = Signal(str)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, config, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._network = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None
        self._parser = SseStreamParser()
        self._assistant_buffer = ""
        self._pending_user_message: dict[str, str] | None = None
        self._messages: list[dict[str, str]] = []
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)

    @property
    def messages(self) -> list[dict[str, str]]:
        return list(self._messages)

    def reset_conversation(self) -> None:
        self.cancel()
        self._messages = []
        self._pending_user_message = None
        self._assistant_buffer = ""

    def send_message(self, user_text: str) -> None:
        text = user_text.strip()
        if not text:
            self.error.emit("请输入消息。")
            return
        if self._reply is not None:
            self.error.emit("上一条消息仍在生成中。")
            return

        api_key = read_api_key()
        if not api_key:
            self.error.emit("未配置 API 密钥。请设置环境变量 DESKTOP_PET_API_KEY 后重启应用。")
            return

        base_url = read_base_url(str(self.config.get("chat.base_url", "https://api.openai.com/v1")))
        model = str(self.config.get("chat.model", "gpt-4o-mini"))
        temperature = float(self.config.get("chat.temperature", 0.7))
        timeout_seconds = int(self.config.get("chat.timeout_seconds", 60))
        system_prompt = str(self.config.get("chat.system_prompt", "你是一个可爱、简洁的桌宠助手。"))
        max_rounds = int(self.config.get("chat.max_context_rounds", 8))

        user_message = {"role": "user", "content": text}
        request_messages = trim_context_messages([*self._messages, user_message], system_prompt, max_rounds)
        payload = build_request_payload(request_messages, model, temperature, stream=True)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        request = QNetworkRequest(QUrl(build_chat_url(base_url)))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Authorization", f"Bearer {api_key}".encode("utf-8"))

        self._pending_user_message = user_message
        self._assistant_buffer = ""
        self._parser = SseStreamParser()
        self._reply = self._network.post(request, body)
        self._reply.readyRead.connect(self._on_ready_read)
        self._reply.finished.connect(self._on_finished)
        self._timeout_timer.start(max(5, timeout_seconds) * 1000)

    def cancel(self) -> None:
        if self._reply is None:
            return
        reply = self._reply
        self._reply = None
        self._timeout_timer.stop()
        reply.abort()
        reply.deleteLater()
        self._pending_user_message = None
        self._assistant_buffer = ""
        self.cancelled.emit()

    @Slot()
    def _on_ready_read(self) -> None:
        if self._reply is None:
            return
        raw = bytes(self._reply.readAll()).decode("utf-8", errors="replace")
        deltas, done = self._parser.feed(raw)
        for delta in deltas:
            self._assistant_buffer += delta
            self.delta_received.emit(delta)
        if done:
            reply = self._reply
            self._reply = None
            self._timeout_timer.stop()
            self._complete_success()
            reply.abort()
            reply.deleteLater()

    @Slot()
    def _on_finished(self) -> None:
        if self._reply is None:
            return
        reply = self._reply
        self._reply = None
        self._timeout_timer.stop()

        if reply.error() == QNetworkReply.NetworkError.OperationCanceledError:
            reply.deleteLater()
            return

        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code and int(status_code) >= 400:
            body = bytes(reply.readAll()).decode("utf-8", errors="replace")
            reply.deleteLater()
            self._rollback_pending_turn()
            self.error.emit(map_http_error(int(status_code), body))
            return
        if reply.error() != QNetworkReply.NetworkError.NoError:
            reply.deleteLater()
            self._rollback_pending_turn()
            self.error.emit("网络连接失败，请检查网络或 API 地址。")
            return

        if self._pending_user_message is not None:
            trailing = bytes(reply.readAll()).decode("utf-8", errors="replace")
            if trailing:
                deltas, done = self._parser.feed(trailing)
                for delta in deltas:
                    self._assistant_buffer += delta
                    self.delta_received.emit(delta)
                if done:
                    reply.deleteLater()
                    self._complete_success()
                    return
            if self._assistant_buffer:
                reply.deleteLater()
                self._complete_success()
                return
            reply.deleteLater()
            self._rollback_pending_turn()
            self.error.emit("服务端返回了空响应。")
            return

        reply.deleteLater()

    @Slot()
    def _on_timeout(self) -> None:
        if self._reply is None:
            return
        reply = self._reply
        self._reply = None
        self._timeout_timer.stop()
        reply.abort()
        reply.deleteLater()
        self._rollback_pending_turn()
        self.error.emit("请求超时，请稍后重试。")

    def _complete_success(self) -> None:
        if self._pending_user_message is None:
            return
        content = self._assistant_buffer.strip()
        if not content:
            self._rollback_pending_turn()
            self.error.emit("服务端返回了空回复。")
            return
        self._messages.append(self._pending_user_message)
        self._messages.append({"role": "assistant", "content": content})
        self._pending_user_message = None
        self._assistant_buffer = ""
        self.finished.emit(content)

    def _rollback_pending_turn(self) -> None:
        self._pending_user_message = None
        self._assistant_buffer = ""


class ModelListClient(QObject):
    models_received = Signal(list)
    error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._reply: QNetworkReply | None = None

    def fetch(self, base_url: str, api_key: str) -> None:
        if self._reply is not None:
            self._reply.abort()
            self._reply.deleteLater()
        request = QNetworkRequest(QUrl(build_models_url(base_url)))
        request.setRawHeader(b"Authorization", f"Bearer {api_key.strip()}".encode("utf-8"))
        self._reply = self._network.get(request)
        self._reply.finished.connect(self._on_finished)

    def cancel(self) -> None:
        if self._reply is None:
            return
        reply = self._reply
        self._reply = None
        reply.abort()
        reply.deleteLater()

    @Slot()
    def _on_finished(self) -> None:
        if self._reply is None:
            return
        reply = self._reply
        self._reply = None
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        body = bytes(reply.readAll())
        network_error = reply.error()
        reply.deleteLater()
        if network_error != QNetworkReply.NetworkError.NoError:
            if status_code:
                self.error.emit(map_http_error(int(status_code), body.decode("utf-8", errors="replace")))
            else:
                self.error.emit("无法连接模型接口，请检查 API 地址和网络。")
            return
        try:
            models = parse_model_ids(body)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.error.emit(f"模型列表响应无效：{exc}")
            return
        if not models:
            self.error.emit("接口未返回可用模型。")
            return
        self.models_received.emit(models)

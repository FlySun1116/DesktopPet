import json

import pytest

from app.chat_client import (
    API_KEY_ENV,
    SseStreamParser,
    build_chat_url,
    build_models_url,
    build_request_payload,
    map_http_error,
    parse_model_ids,
    parse_sse_data_payload,
    read_api_key,
    trim_context_messages,
)
from app.env_manager import BASE_URL_ENV, load_project_env, read_env_value, save_env_value


def test_build_chat_url_with_and_without_v1_suffix():
    assert build_chat_url("https://api.openai.com/v1") == "https://api.openai.com/v1/chat/completions"
    assert build_chat_url("https://api.deepseek.com") == "https://api.deepseek.com/v1/chat/completions"
    assert build_chat_url("https://example.com/v1/") == "https://example.com/v1/chat/completions"
    assert build_models_url("https://api.openai.com/v1") == "https://api.openai.com/v1/models"
    assert build_models_url("https://example.com") == "https://example.com/v1/models"


def test_parse_model_ids_sorts_and_deduplicates():
    body = json.dumps({"data": [{"id": "model-z"}, {"id": "model-a"}, {"id": "model-a"}]}).encode()
    assert parse_model_ids(body) == ["model-a", "model-z"]


def test_build_request_payload_streaming():
    messages = [{"role": "user", "content": "你好"}]
    payload = build_request_payload(messages, "gpt-4o-mini", 0.7, stream=True)
    assert payload["model"] == "gpt-4o-mini"
    assert payload["messages"] == messages
    assert payload["temperature"] == 0.7
    assert payload["stream"] is True


def test_trim_context_messages_keeps_system_and_recent_rounds():
    history = []
    for index in range(10):
        history.append({"role": "user", "content": f"u{index}"})
        history.append({"role": "assistant", "content": f"a{index}"})
    trimmed = trim_context_messages(history, "你是桌宠", max_rounds=2)
    assert trimmed[0] == {"role": "system", "content": "你是桌宠"}
    assert trimmed[-4:] == [
        {"role": "user", "content": "u8"},
        {"role": "assistant", "content": "a8"},
        {"role": "user", "content": "u9"},
        {"role": "assistant", "content": "a9"},
    ]


def test_parse_sse_data_payload_delta_and_done():
    delta_payload = json.dumps({"choices": [{"delta": {"content": "你好"}}]})
    assert parse_sse_data_payload(delta_payload) == ("你好", False)
    assert parse_sse_data_payload("[DONE]") == (None, True)
    assert parse_sse_data_payload("{broken") == (None, False)


def test_sse_stream_parser_handles_split_chunks_and_done():
    parser = SseStreamParser()
    first, done = parser.feed('data: {"choices":[{"delta":{"content":"你"')
    assert first == []
    assert done is False
    second, done = parser.feed('}}]}\n\ndata: [DONE]\n')
    assert second == ["你"]
    assert done is True


def test_map_http_error_messages():
    assert "密钥" in map_http_error(401, "")
    assert "频繁" in map_http_error(429, "")
    assert "服务端" in map_http_error(500, "")


def test_read_api_key_from_environment(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    assert read_api_key() is None
    monkeypatch.setenv(API_KEY_ENV, "  secret-key  ")
    assert read_api_key() == "secret-key"


def test_project_env_can_be_saved_and_loaded(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    monkeypatch.delenv(BASE_URL_ENV, raising=False)
    save_env_value(API_KEY_ENV, "secret-key", path)
    save_env_value(BASE_URL_ENV, "https://example.com/v1", path)
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    monkeypatch.delenv(BASE_URL_ENV, raising=False)
    load_project_env(path)
    assert read_env_value(API_KEY_ENV, path) == "secret-key"
    assert read_env_value(BASE_URL_ENV, path) == "https://example.com/v1"


def test_default_chat_config_merge_does_not_include_api_key(tmp_path):
    from app.config_manager import ConfigManager

    default_path = tmp_path / "default.json"
    user_path = tmp_path / "user.json"
    default_path.write_text(
        json.dumps(
            {
                "chat": {
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4o-mini",
                }
            }
        ),
        encoding="utf-8",
    )
    user_path.write_text(json.dumps({"chat": {"model": "deepseek-chat"}}), encoding="utf-8")
    manager = ConfigManager(default_path=default_path, user_path=user_path)
    manager.set("chat.temperature", 0.5)
    manager.save()
    saved = json.loads(user_path.read_text(encoding="utf-8"))
    assert saved["chat"]["model"] == "deepseek-chat"
    assert saved["chat"]["temperature"] == 0.5
    assert "api_key" not in json.dumps(saved)

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.llm_provider import (
    ProviderConfigError,
    build_chat_model,
    build_embedder,
    get_provider_config,
)


PROVIDER_ENV_VARS = [
    "LLM_PROVIDER",
    "GOOGLE_API_KEY",
    "GEMINI_MODEL_ID",
    "GEMINI_EMBEDDING_MODEL_ID",
    "OLLAMA_HOST",
    "OLLAMA_BASE_URL",
    "OLLAMA_API_KEY",
    "OLLAMA_MODEL_ID",
    "OLLAMA_EMBEDDING_MODEL_ID",
    "HF_TOKEN",
    "HUGGINGFACE_API_KEY",
    "HUGGINGFACE_BASE_URL",
    "HUGGINGFACE_MODEL_ID",
    "HUGGINGFACE_EMBEDDING_MODEL_ID",
    "EMBEDDING_DIMENSIONS",
]


def clear_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in PROVIDER_ENV_VARS:
        monkeypatch.delenv(key, raising=False)


def reload_my_os():
    sys.modules.pop("my_os", None)
    return importlib.import_module("my_os")


def test_get_provider_config_gemini(monkeypatch: pytest.MonkeyPatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    config = get_provider_config()

    assert config.provider == "gemini"
    assert config.model_id == "gemini-2.0-flash-001"
    assert config.embedding_model_id == "gemini-embedding-001"
    assert config.embedding_dimensions == 768


def test_get_provider_config_ollama(monkeypatch: pytest.MonkeyPatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")

    config = get_provider_config()

    assert config.provider == "ollama"
    assert config.ollama_host == "http://localhost:11434"
    assert config.model_id == "llama3.2"


def test_get_provider_config_huggingface(monkeypatch: pytest.MonkeyPatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "huggingface")
    monkeypatch.setenv("HF_TOKEN", "hf_test_token")

    config = get_provider_config()

    assert config.provider == "huggingface"
    assert config.huggingface_token == "hf_test_token"
    assert config.model_id == "meta-llama/Llama-3.1-8B-Instruct"


def test_autodetect_precedence(monkeypatch: pytest.MonkeyPatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    monkeypatch.setenv("HF_TOKEN", "hf-token")

    config = get_provider_config()

    assert config.provider == "gemini"
    assert config.detection_source == "auto-detect"


def test_invalid_provider(monkeypatch: pytest.MonkeyPatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "claude")

    with pytest.raises(ProviderConfigError):
        get_provider_config()


def test_missing_provider_credentials(monkeypatch: pytest.MonkeyPatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "huggingface")

    with pytest.raises(ProviderConfigError):
        get_provider_config()


@pytest.mark.parametrize(
    ("provider", "envs", "expected_model", "expected_embedder"),
    [
        (
            "gemini",
            {"GOOGLE_API_KEY": "google-key"},
            "Gemini",
            "GeminiEmbedder",
        ),
        (
            "ollama",
            {"OLLAMA_HOST": "http://localhost:11434"},
            "Ollama",
            "OllamaEmbedder",
        ),
        (
            "huggingface",
            {"HF_TOKEN": "hf-token"},
            "HuggingFace",
            "HuggingfaceCustomEmbedder",
        ),
    ],
)
def test_builders_for_each_provider(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    envs: dict[str, str],
    expected_model: str,
    expected_embedder: str,
):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", provider)
    for key, value in envs.items():
        monkeypatch.setenv(key, value)

    model = build_chat_model()
    embedder = build_embedder()

    assert model.__class__.__name__ == expected_model
    assert embedder.__class__.__name__ == expected_embedder


@pytest.mark.parametrize(
    ("provider", "envs"),
    [
        ("gemini", {"GOOGLE_API_KEY": "google-key"}),
        ("ollama", {"OLLAMA_HOST": "http://localhost:11434"}),
        ("huggingface", {"HF_TOKEN": "hf-token"}),
    ],
)
def test_my_os_bootstrap_for_each_provider(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    envs: dict[str, str],
):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", provider)
    for key, value in envs.items():
        monkeypatch.setenv(key, value)

    my_os = reload_my_os()

    assert my_os.app is not None
    assert my_os.agent_os is not None


def test_agentos_docs_and_config(monkeypatch: pytest.MonkeyPatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")

    my_os = reload_my_os()
    paths = {route.path for route in my_os.app.routes}

    assert "/docs" in paths
    assert "/config" in paths

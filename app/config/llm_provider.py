"""
Centralized LLM provider resolution for the Fiscal Agent.

This module is the single source of truth for:
- chat model provider selection
- provider-specific environment validation
- embedding provider selection used by the ingest/RAG pipeline
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ("gemini", "ollama", "huggingface")
AUTODETECT_PRECEDENCE = ("gemini", "ollama", "huggingface")
DEFAULT_EMBEDDING_DIMENSIONS = 768


class ProviderConfigError(ValueError):
    """Raised when provider configuration is missing or invalid."""


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    detection_source: str
    model_id: str
    embedding_model_id: str
    embedding_dimensions: int
    ollama_host: str | None = None
    ollama_api_key: str | None = None
    huggingface_token: str | None = None
    huggingface_base_url: str | None = None
    google_api_key: str | None = None


def _normalize_provider(raw: str) -> str:
    value = raw.strip().lower()
    aliases = {
        "google": "gemini",
        "hf": "huggingface",
        "hugging_face": "huggingface",
        "hugging-face": "huggingface",
    }
    return aliases.get(value, value)


def _env_has_gemini() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY"))


def _env_has_ollama() -> bool:
    return bool(
        os.getenv("OLLAMA_HOST")
        or os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_API_KEY")
    )


def _env_has_huggingface() -> bool:
    return bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY"))


def _resolve_provider_name() -> tuple[str, str]:
    explicit = os.getenv("LLM_PROVIDER")
    if explicit:
        provider = _normalize_provider(explicit)
        if provider not in SUPPORTED_PROVIDERS:
            raise ProviderConfigError(
                f"LLM_PROVIDER inválido: '{explicit}'. "
                f"Use um de: {', '.join(SUPPORTED_PROVIDERS)}"
            )
        return provider, "env:LLM_PROVIDER"

    candidates: list[str] = []
    if _env_has_gemini():
        candidates.append("gemini")
    if _env_has_ollama():
        candidates.append("ollama")
    if _env_has_huggingface():
        candidates.append("huggingface")

    if not candidates:
        logger.info(
            "LLM_PROVIDER não definido e nenhum provider detectado automaticamente. "
            "Assumindo 'gemini' por compatibilidade."
        )
        return "gemini", "default:compatibility"

    if len(candidates) > 1:
        logger.warning(
            "Múltiplos providers detectados automaticamente (%s). "
            "Usando precedência %s.",
            ", ".join(candidates),
            " > ".join(AUTODETECT_PRECEDENCE),
        )

    for provider in AUTODETECT_PRECEDENCE:
        if provider in candidates:
            return provider, "auto-detect"

    raise ProviderConfigError("Não foi possível resolver o provider ativo.")


def _get_embedding_dimensions() -> int:
    raw = os.getenv("EMBEDDING_DIMENSIONS", str(DEFAULT_EMBEDDING_DIMENSIONS))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ProviderConfigError(
            f"EMBEDDING_DIMENSIONS inválido: '{raw}'. Use um inteiro."
        ) from exc
    if value <= 0:
        raise ProviderConfigError("EMBEDDING_DIMENSIONS deve ser maior que zero.")
    return value


def get_provider_config() -> ProviderConfig:
    provider, detection_source = _resolve_provider_name()
    dimensions = _get_embedding_dimensions()

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderConfigError(
                "Provider 'gemini' selecionado, mas GOOGLE_API_KEY não está configurada."
            )
        return ProviderConfig(
            provider="gemini",
            detection_source=detection_source,
            model_id=os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-001"),
            embedding_model_id=os.getenv("GEMINI_EMBEDDING_MODEL_ID", "gemini-embedding-001"),
            embedding_dimensions=dimensions,
            google_api_key=api_key,
        )

    if provider == "ollama":
        host = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST")
        api_key = os.getenv("OLLAMA_API_KEY")
        if not host and not api_key:
            raise ProviderConfigError(
                "Provider 'ollama' selecionado, mas nenhum endpoint foi configurado. "
                "Defina OLLAMA_HOST/OLLAMA_BASE_URL para local ou OLLAMA_API_KEY para cloud."
            )
        return ProviderConfig(
            provider="ollama",
            detection_source=detection_source,
            model_id=os.getenv("OLLAMA_MODEL_ID", "llama3.2"),
            embedding_model_id=os.getenv("OLLAMA_EMBEDDING_MODEL_ID", "nomic-embed-text"),
            embedding_dimensions=dimensions,
            ollama_host=host,
            ollama_api_key=api_key,
        )

    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
    if not hf_token:
        raise ProviderConfigError(
            "Provider 'huggingface' selecionado, mas HF_TOKEN não está configurado."
        )
    return ProviderConfig(
        provider="huggingface",
        detection_source=detection_source,
        model_id=os.getenv("HUGGINGFACE_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct"),
        embedding_model_id=os.getenv(
            "HUGGINGFACE_EMBEDDING_MODEL_ID",
            "sentence-transformers/all-mpnet-base-v2",
        ),
        embedding_dimensions=dimensions,
        huggingface_token=hf_token,
        huggingface_base_url=os.getenv("HUGGINGFACE_BASE_URL"),
    )


def build_chat_model(*, model_id: str | None = None, temperature: float | None = None):
    """Build the Agno chat model for the active provider."""
    config = get_provider_config()
    resolved_model_id = model_id or config.model_id

    if config.provider == "gemini":
        try:
            from agno.models.google import Gemini
        except ImportError as exc:
            raise ProviderConfigError(
                "Dependência ausente para provider 'gemini'. "
                "Instale os requisitos do projeto novamente."
            ) from exc

        return Gemini(
            id=resolved_model_id,
            temperature=temperature,
            api_key=config.google_api_key,
        )

    if config.provider == "ollama":
        try:
            from agno.models.ollama import Ollama
        except ImportError as exc:
            raise ProviderConfigError(
                "Dependência ausente para provider 'ollama'. "
                "Instale os pacotes `agno` e `ollama` definidos em requirements.txt."
            ) from exc

        ollama_kwargs: dict[str, Any] = {
            "id": resolved_model_id,
            "host": config.ollama_host,
            "api_key": config.ollama_api_key,
        }
        if temperature is not None:
            ollama_kwargs["options"] = {"temperature": temperature}

        return Ollama(
            **ollama_kwargs,
        )

    try:
        from agno.models.huggingface import HuggingFace
    except ImportError as exc:
        raise ProviderConfigError(
            "Dependência ausente para provider 'huggingface'. "
            "Instale os pacotes `agno` e `huggingface_hub` definidos em requirements.txt."
        ) from exc

    return HuggingFace(
        id=resolved_model_id,
        temperature=temperature,
        api_key=config.huggingface_token,
        base_url=config.huggingface_base_url,
    )


def build_embedder(*, model_id: str | None = None, task_type: str = "RETRIEVAL_QUERY"):
    """
    Build the knowledge embedder for the active provider.

    All default embedding models are chosen to fit the current `vector(768)`
    storage schema.
    """
    config = get_provider_config()
    resolved_model_id = model_id or config.embedding_model_id

    if config.provider == "gemini":
        try:
            from agno.knowledge.embedder.google import GeminiEmbedder
        except ImportError as exc:
            raise ProviderConfigError(
                "Dependência ausente para embeddings do provider 'gemini'."
            ) from exc

        return GeminiEmbedder(
            id=resolved_model_id,
            task_type=task_type,
            dimensions=config.embedding_dimensions,
            api_key=config.google_api_key,
        )

    if config.provider == "ollama":
        try:
            from agno.knowledge.embedder.ollama import OllamaEmbedder
        except ImportError as exc:
            raise ProviderConfigError(
                "Dependência ausente para embeddings do provider 'ollama'. "
                "Instale o pacote `ollama`."
            ) from exc

        client_kwargs: dict[str, Any] | None = None
        host = config.ollama_host
        if config.ollama_api_key:
            if not host:
                host = "https://ollama.com"
            client_kwargs = {
                "headers": {"authorization": f"Bearer {config.ollama_api_key}"}
            }

        return OllamaEmbedder(
            id=resolved_model_id,
            dimensions=config.embedding_dimensions,
            host=host,
            client_kwargs=client_kwargs,
        )

    try:
        from agno.knowledge.embedder.huggingface import HuggingfaceCustomEmbedder
    except ImportError as exc:
        raise ProviderConfigError(
            "Dependência ausente para embeddings do provider 'huggingface'. "
            "Instale o pacote `huggingface_hub`."
        ) from exc

    return HuggingfaceCustomEmbedder(
        id=resolved_model_id,
        api_key=config.huggingface_token,
        client_params=(
            {"base_url": config.huggingface_base_url}
            if config.huggingface_base_url
            else None
        ),
    )


def get_startup_summary() -> str:
    """Human-readable summary for startup logs."""
    config = get_provider_config()
    return (
        f"provider={config.provider} "
        f"(source={config.detection_source}) "
        f"model={config.model_id} "
        f"embedding_model={config.embedding_model_id} "
        f"embedding_dimensions={config.embedding_dimensions}"
    )

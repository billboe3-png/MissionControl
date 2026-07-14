"""
Mission Control AI Provider Abstraction

Abstract base class and factory for AI providers.
Supports: Ollama, OpenAI, Azure OpenAI, Anthropic, Local LLM.

Providers NEVER execute infrastructure changes.
They only generate text analysis and recommendations.

Sprint 2.6.0 - AI Operations Engine.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connectivity to the AI provider."""
        ...

    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = "") -> dict:
        """
        Send a prompt and return a completion.

        Returns:
            {"success": bool, "text": str, "error": str | None}
        """
        ...

    @abstractmethod
    async def get_models(self) -> dict:
        """List available models from this provider."""
        ...

    @abstractmethod
    async def get_provider_info(self) -> dict:
        """Return provider metadata."""
        ...


class OllamaProvider(AIProvider):
    """Ollama local LLM provider."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def test_connection(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    return {"success": True, "message": "Ollama connected"}
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def complete(self, prompt: str, system_prompt: str = "") -> dict:
        try:
            import httpx

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {"model": self._model, "messages": messages, "stream": False}

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data.get("message", {}).get("content", "")
                    return {"success": True, "text": text, "error": None}
                return {
                    "success": False,
                    "text": "",
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "text": "", "error": str(e)}

    async def get_models(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return {"success": True, "models": models}
                return {
                    "success": False,
                    "models": [],
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "models": [], "error": str(e)}

    async def get_provider_info(self) -> dict:
        return {
            "name": "Ollama",
            "type": "ollama",
            "model": self._model,
            "base_url": self._base_url,
            "offline_capable": True,
        }


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._api_key = api_key
        self._model = model

    async def test_connection(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "OpenAI connected"}
                return {
                    "success": False,
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def complete(self, prompt: str, system_prompt: str = "") -> dict:
        try:
            import httpx

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self._model,
                "messages": messages,
            }

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": (f"Bearer {self._api_key}"),
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "text": text,
                        "error": None,
                    }
                err = f"HTTP {resp.status_code}"
                return {
                    "success": False,
                    "text": "",
                    "error": err,
                }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": str(e),
            }

    async def get_models(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={
                        "Authorization": (f"Bearer {self._api_key}"),
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    models = [
                        m["id"]
                        for m in data.get("data", [])
                        if "gpt" in m.get("id", "").lower()
                    ]
                    return {
                        "success": True,
                        "models": models,
                    }
                err = f"HTTP {resp.status_code}"
                return {
                    "success": False,
                    "models": [],
                    "error": err,
                }
        except Exception as e:
            return {"success": False, "models": [], "error": str(e)}

    async def get_provider_info(self) -> dict:
        return {
            "name": "OpenAI",
            "type": "openai",
            "model": self._model,
            "offline_capable": False,
        }


class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI provider."""

    def __init__(self, endpoint: str, api_key: str, deployment: str = "gpt-4o"):
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._deployment = deployment

    async def test_connection(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self._endpoint}/openai/models",
                    headers={"api-key": self._api_key},
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "Azure OpenAI connected"}
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def complete(self, prompt: str, system_prompt: str = "") -> dict:
        try:
            import httpx

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {"messages": messages}
            url = (
                f"{self._endpoint}/openai/deployments/{self._deployment}"
                f"/chat/completions?api-version=2024-02-01"
            )

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    url,
                    headers={
                        "api-key": self._api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    return {"success": True, "text": text, "error": None}
                return {
                    "success": False,
                    "text": "",
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "text": "", "error": str(e)}

    async def get_models(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self._endpoint}/openai/models",
                    headers={"api-key": self._api_key},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", [])]
                    return {"success": True, "models": models}
                return {
                    "success": False,
                    "models": [],
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "models": [], "error": str(e)}

    async def get_provider_info(self) -> dict:
        return {
            "name": "Azure OpenAI",
            "type": "azure_openai",
            "model": self._deployment,
            "endpoint": self._endpoint,
            "offline_capable": False,
        }


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._api_key = api_key
        self._model = model

    async def test_connection(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "Anthropic connected"}
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def complete(self, prompt: str, system_prompt: str = "") -> dict:
        try:
            import httpx

            payload: dict = {
                "model": self._model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["content"][0]["text"]
                    return {"success": True, "text": text, "error": None}
                return {
                    "success": False,
                    "text": "",
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "text": "", "error": str(e)}

    async def get_models(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", [])]
                    return {"success": True, "models": models}
                return {
                    "success": False,
                    "models": [],
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "models": [], "error": str(e)}

    async def get_provider_info(self) -> dict:
        return {
            "name": "Anthropic",
            "type": "anthropic",
            "model": self._model,
            "offline_capable": False,
        }


class LocalLLMProvider(AIProvider):
    """Local LLM provider (Ollama-based offline mode)."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def test_connection(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    return {"success": True, "message": "Local LLM connected"}
                return {"success": False, "error": "Ollama not reachable"}
        except Exception:
            return {"success": False, "error": "Ollama not running locally"}

    async def complete(self, prompt: str, system_prompt: str = "") -> dict:
        try:
            import httpx

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {"model": self._model, "messages": messages, "stream": False}

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data.get("message", {}).get("content", "")
                    return {"success": True, "text": text, "error": None}
                return {
                    "success": False,
                    "text": "",
                    "error": f"HTTP {resp.status_code}",
                }
        except Exception as e:
            return {"success": False, "text": "", "error": str(e)}

    async def get_models(self) -> dict:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return {"success": True, "models": models}
                return {"success": False, "models": [], "error": "Not reachable"}
        except Exception:
            return {"success": False, "models": [], "error": "Ollama not running"}

    async def get_provider_info(self) -> dict:
        return {
            "name": "Local LLM",
            "type": "local",
            "model": self._model,
            "base_url": self._base_url,
            "offline_capable": True,
        }


class RuleBasedProvider(AIProvider):
    """
    Built-in rule-based AI provider.
    No external dependencies. Always available.
    Provides deterministic analysis without LLM calls.
    """

    async def test_connection(self) -> dict:
        return {"success": True, "message": "Rule-based engine always available"}

    async def complete(self, prompt: str, system_prompt: str = "") -> dict:
        return {
            "success": True,
            "text": (
                "Rule-based analysis: No external AI "
                "provider configured. Configure an AI "
                "provider in Settings > Integrations "
                "for enhanced analysis."
            ),
            "error": None,
        }

    async def get_models(self) -> dict:
        return {"success": True, "models": ["rule-based-v1"]}

    async def get_provider_info(self) -> dict:
        return {
            "name": "Rule-Based Engine",
            "type": "rule_based",
            "model": "rule-based-v1",
            "offline_capable": True,
        }


_ai_provider: AIProvider | None = None

AI_PROVIDER_TYPES = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "azure_openai": AzureOpenAIProvider,
    "anthropic": AnthropicProvider,
    "local": LocalLLMProvider,
    "rule_based": RuleBasedProvider,
}


def get_ai_provider() -> AIProvider:
    """
    Return the singleton AI provider.

    Checks IntegrationProfile DB for an enabled ai_provider type.
    Falls back to RuleBasedProvider.
    """
    global _ai_provider

    if _ai_provider is not None:
        return _ai_provider

    try:
        from app.db import SessionLocal
        from app.repositories.integration_profile_repository import (
            IntegrationProfileRepository,
        )

        db = SessionLocal()
        try:
            profile = IntegrationProfileRepository.get_enabled_by_type(
                db, "ai_provider"
            )
            if profile is not None:
                from app.core.config import get_settings
                from app.core.security import CredentialCipher

                settings = get_settings()
                cipher = CredentialCipher(settings.missioncontrol_secret_key)
                api_key = (
                    cipher.decrypt(profile.encrypted_secret)
                    if profile.encrypted_secret
                    else ""
                )

                provider_type = profile.base_url or "rule_based"
                model = profile.username or "default"

                if provider_type == "ollama":
                    _ai_provider = OllamaProvider(model=model)
                elif provider_type == "openai":
                    _ai_provider = OpenAIProvider(api_key=api_key, model=model)
                elif provider_type == "azure_openai":
                    _ai_provider = AzureOpenAIProvider(
                        endpoint=profile.base_url or "",
                        api_key=api_key,
                        deployment=model,
                    )
                elif provider_type == "anthropic":
                    _ai_provider = AnthropicProvider(api_key=api_key, model=model)
                elif provider_type == "local":
                    _ai_provider = LocalLLMProvider(model=model)
                else:
                    _ai_provider = RuleBasedProvider()

                logger.info("Created AI provider: %s", provider_type)
                return _ai_provider
        finally:
            db.close()
    except Exception as e:
        logger.debug("AI provider DB lookup failed: %s", e)

    _ai_provider = RuleBasedProvider()
    logger.info("Using default RuleBasedProvider")
    return _ai_provider


def reset_ai_provider() -> None:
    """Reset singleton provider. Used for testing."""
    global _ai_provider
    _ai_provider = None
    logger.info("AI provider singleton reset")

"""OpenRouter API client for LLM integration."""

import asyncio
from dataclasses import dataclass
from typing import Optional, AsyncIterator
import httpx

from ..config import LLMConfig


@dataclass
class LLMResponse:
    """Response from LLM API."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMClient:
    """Client for OpenRouter API (OpenAI-compatible)."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the LLM client.

        Args:
            config: LLM configuration. If None, uses default config.
        """
        self.config = config or LLMConfig()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "HTTP-Referer": "https://github.com/chess-alive",
                    "X-Title": "ChessAlive",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get a completion from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model: Model to use (overrides config)
            temperature: Temperature setting (overrides config)
            max_tokens: Max tokens (overrides config)

        Returns:
            The completion text
        """
        response = await self.complete_full(
            prompt, system_prompt, model, temperature, max_tokens
        )
        return response.content

    async def complete_full(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Get a full completion response from the LLM.

        Returns:
            LLMResponse with content and metadata
        """
        if not self.config.is_configured:
            raise RuntimeError(
                "OpenRouter API key not configured. "
                "Set OPENROUTER_API_KEY environment variable."
            )

        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            usage = data.get("usage", {})

            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", model or self.config.model),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except Exception:
                error_detail = str(e)
            raise LLMError(f"OpenRouter API error: {error_detail}") from e

        except httpx.RequestError as e:
            raise LLMError(f"Request failed: {e}") from e

    async def complete_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream completion from the LLM.

        Yields:
            Chunks of completion text
        """
        if not self.config.is_configured:
            raise RuntimeError(
                "OpenRouter API key not configured. "
                "Set OPENROUTER_API_KEY environment variable."
            )

        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": True,
        }

        try:
            async with client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

        except httpx.HTTPStatusError as e:
            raise LLMError(f"OpenRouter API error: {e}") from e

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class LLMError(Exception):
    """Exception raised for LLM API errors."""

    pass


# Convenience function for quick completions
async def get_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    config: Optional[LLMConfig] = None,
) -> str:
    """
    Quick helper to get a completion.

    Example:
        response = await get_completion("What is 2+2?")
    """
    async with LLMClient(config) as client:
        return await client.complete(prompt, system_prompt)

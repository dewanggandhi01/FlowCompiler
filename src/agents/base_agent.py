"""
Base Agent — Abstract base class for all pipeline agents.

Provides:
- OpenAI client setup with deterministic configuration (temperature=0)
- Structured output parsing via Pydantic models
- Retry logic with exponential backoff
- Token usage tracking
- Fixed prompt template system
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

from src.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class TokenUsage(BaseModel):
    """Tracks token usage for a single LLM call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentResult(BaseModel, Generic[T]):
    """Wrapper for agent results with metadata."""
    data: Any = None
    token_usage: TokenUsage = TokenUsage()
    duration_ms: float = 0.0
    retries: int = 0
    model: str = ""


class BaseAgent(ABC):
    """
    Abstract base class for all pipeline agents.

    Subclasses must implement:
    - `system_prompt` property: Returns the fixed system prompt
    - `build_user_prompt(input_data)`: Builds the user message from input
    - `output_model` property: Returns the Pydantic model class for structured output
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        # Support AI Pipe or any OpenAI-compatible proxy via custom base_url
        client_kwargs: dict = {"api_key": self.settings.openai_api_key}
        if self.settings.openai_base_url:
            client_kwargs["base_url"] = self.settings.openai_base_url
        self.client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)
        self.model = self.settings.openai_model
        self.temperature = self.settings.openai_temperature
        self.max_retries = self.settings.max_retries

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the fixed system prompt for this agent."""
        ...

    @abstractmethod
    def build_user_prompt(self, input_data: Any) -> str:
        """Build the user message from input data."""
        ...

    @property
    @abstractmethod
    def output_model(self) -> type[BaseModel]:
        """Return the Pydantic model class for structured output."""
        ...

    def run(self, input_data: Any) -> AgentResult:
        """
        Execute the agent synchronously with retry logic.

        Args:
            input_data: Input data for the agent (varies by stage).

        Returns:
            AgentResult wrapping the parsed output and metadata.
        """
        user_prompt = self.build_user_prompt(input_data)
        start_time = time.time()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                parsed, usage = self._call_llm(user_prompt)
                duration_ms = (time.time() - start_time) * 1000
                token_usage = TokenUsage(
                    prompt_tokens=usage.prompt_tokens if usage else 0,
                    completion_tokens=usage.completion_tokens if usage else 0,
                    total_tokens=usage.total_tokens if usage else 0,
                )

                logger.info(
                    f"{self.__class__.__name__} completed in {duration_ms:.0f}ms "
                    f"(tokens: {token_usage.total_tokens}, attempt: {attempt + 1})"
                )

                return AgentResult(
                    data=parsed,
                    token_usage=token_usage,
                    duration_ms=duration_ms,
                    retries=attempt,
                    model=self.model,
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    f"{self.__class__.__name__} attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)

        raise RuntimeError(
            f"{self.__class__.__name__} failed after {self.max_retries} attempts: {last_error}"
        )

    async def arun(self, input_data: Any) -> AgentResult:
        """
        Execute the agent asynchronously with retry logic.

        Args:
            input_data: Input data for the agent.

        Returns:
            AgentResult wrapping the parsed output and metadata.
        """
        user_prompt = self.build_user_prompt(input_data)
        start_time = time.time()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                parsed, usage = await self._acall_llm(user_prompt)
                duration_ms = (time.time() - start_time) * 1000
                token_usage = TokenUsage(
                    prompt_tokens=usage.prompt_tokens if usage else 0,
                    completion_tokens=usage.completion_tokens if usage else 0,
                    total_tokens=usage.total_tokens if usage else 0,
                )

                logger.info(
                    f"{self.__class__.__name__} completed in {duration_ms:.0f}ms "
                    f"(tokens: {token_usage.total_tokens}, attempt: {attempt + 1})"
                )

                return AgentResult(
                    data=parsed,
                    token_usage=token_usage,
                    duration_ms=duration_ms,
                    retries=attempt,
                    model=self.model,
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    f"{self.__class__.__name__} attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)

        raise RuntimeError(
            f"{self.__class__.__name__} failed after {self.max_retries} attempts: {last_error}"
        )

    def _llm_messages(self, user_prompt: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_response(self, content: str) -> BaseModel:
        return self.output_model.model_validate_json(content)

    def _call_llm(self, user_prompt: str):
        messages = self._llm_messages(user_prompt)
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                temperature=self.temperature,
                messages=messages,
                response_format=self.output_model,
            )
            return response.choices[0].message.parsed, response.usage
        except Exception as parse_error:
            if "Invalid schema" not in str(parse_error) and "response_format" not in str(parse_error):
                raise
            logger.warning(f"{self.__class__.__name__} structured parse failed, using JSON mode")
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return self._parse_response(content), response.usage

    async def _acall_llm(self, user_prompt: str):
        messages = self._llm_messages(user_prompt)
        try:
            response = await self.async_client.beta.chat.completions.parse(
                model=self.model,
                temperature=self.temperature,
                messages=messages,
                response_format=self.output_model,
            )
            return response.choices[0].message.parsed, response.usage
        except Exception as parse_error:
            if "Invalid schema" not in str(parse_error) and "response_format" not in str(parse_error):
                raise
            logger.warning(f"{self.__class__.__name__} structured parse failed, using JSON mode")
            response = await self.async_client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return self._parse_response(content), response.usage

    def _serialize_input(self, data: Any) -> str:
        """Serialize input data to JSON string for prompt injection."""
        if isinstance(data, BaseModel):
            return data.model_dump_json(indent=2)
        elif isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)
        elif isinstance(data, str):
            return data
        else:
            return str(data)

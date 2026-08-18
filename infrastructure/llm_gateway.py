"""Centralized model access with contracts, safety controls, and operational metadata."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from core.config import Settings, get_settings
from domain.models import GenerationMetadata
from infrastructure.security import SensitiveDataRedactor
from infrastructure.telemetry import NullTelemetrySink, TelemetryEvent, TelemetrySink

T = TypeVar("T", bound=BaseModel)


class GenerationError(RuntimeError):
    """Raised when a model response cannot safely satisfy a generation contract."""


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    task: str
    system_prompt: str
    user_prompt: str
    prompt_version: str
    output_model: type[T]
    reasoning: bool = False
    model: str | None = None
    max_output_tokens: int = 6_000
    cacheable: bool = True
    image_data_urls: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GenerationResponse:
    value: T
    metadata: GenerationMetadata


class LLMGateway(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResponse: ...


class OpenAIModelGateway:
    """Provider boundary; domain agents never call provider SDKs directly."""

    def __init__(
        self,
        settings: Settings | None = None,
        redactor: SensitiveDataRedactor | None = None,
        telemetry: TelemetrySink | None = None,
    ):
        self.settings = settings or get_settings()
        self.redactor = redactor or SensitiveDataRedactor()
        self.telemetry = telemetry or NullTelemetrySink()
        self._cache: dict[str, GenerationResponse] = {}
        self._client: Any | None = None

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        self.settings.validate("llm")
        prepared = self._prepare_request(request)
        cache_key = self._cache_key(prepared)
        if prepared.cacheable and cache_key in self._cache:
            cached = self._cache[cache_key]
            return GenerationResponse(
                value=cached.value,
                metadata=cached.metadata.model_copy(update={"cached": True}),
            )

        started = time.perf_counter()
        response = self._with_retries(prepared)
        latency_ms = int((time.perf_counter() - started) * 1000)
        content = self._extract_content(response)
        try:
            parsed = prepared.output_model.model_validate_json(content)
        except Exception as error:  # provider output is untrusted until validated
            raise GenerationError(
                f"Model response failed the {prepared.output_model.__name__} contract for task '{prepared.task}': {error}"
            ) from error

        usage = getattr(response, "usage", None)
        metadata = GenerationMetadata(
            task=prepared.task,
            model=self._select_model(prepared),
            prompt_version=prepared.prompt_version,
            input_hash=sha256(f"{prepared.system_prompt}\n{prepared.user_prompt}".encode()).hexdigest(),
            latency_ms=latency_ms,
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
        )
        result = GenerationResponse(value=parsed, metadata=metadata)
        self.telemetry.emit(
            TelemetryEvent(
                event_type="llm.generation",
                attributes={
                    "task": metadata.task,
                    "model": metadata.model,
                    "prompt_version": metadata.prompt_version,
                    "input_hash": metadata.input_hash,
                    "latency_ms": metadata.latency_ms,
                    "prompt_tokens": metadata.prompt_tokens,
                    "completion_tokens": metadata.completion_tokens,
                },
            )
        )
        if prepared.cacheable:
            self._cache[cache_key] = result
        return result

    def _prepare_request(self, request: GenerationRequest) -> GenerationRequest:
        if not self.settings.redact_sensitive_data:
            return request
        system = self.redactor.redact(request.system_prompt).text
        user = self.redactor.redact(request.user_prompt).text
        return GenerationRequest(
            task=request.task,
            system_prompt=system,
            user_prompt=user,
            prompt_version=request.prompt_version,
            output_model=request.output_model,
            reasoning=request.reasoning,
            model=request.model,
            max_output_tokens=request.max_output_tokens,
            cacheable=request.cacheable,
            image_data_urls=request.image_data_urls,
        )

    def _with_retries(self, request: GenerationRequest) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.settings.model_max_retries + 1):
            try:
                return self._invoke(request)
            except Exception as error:  # SDK errors are normalized at one boundary
                last_error = error
                if attempt == self.settings.model_max_retries:
                    break
                time.sleep((2**attempt) + random.uniform(0, 0.25))
        raise GenerationError(f"Model generation failed after retries: {last_error}") from last_error

    def _invoke(self, request: GenerationRequest) -> Any:
        model = self._select_model(request)
        user_content: str | list[dict[str, Any]] = request.user_prompt
        if request.image_data_urls:
            user_content = [{"type": "text", "text": request.user_prompt}]
            user_content.extend(
                {"type": "image_url", "image_url": {"url": image, "detail": "auto"}}
                for image in request.image_data_urls
            )
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": user_content},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.output_model.__name__.lower(),
                    "strict": True,
                    "schema": _strict_schema(request.output_model.model_json_schema()),
                },
            },
        }
        if model.startswith("gpt-"):
            kwargs["max_completion_tokens"] = request.max_output_tokens
            if request.reasoning:
                kwargs["extra_body"] = {"reasoning": {"effort": "medium"}}
        else:
            kwargs["max_tokens"] = request.max_output_tokens
        return self._get_client().chat.completions.create(**kwargs)

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as error:
                raise GenerationError("Install the 'openai' package to use the QUALTAN model gateway.") from error
            kwargs: dict[str, Any] = {"api_key": self.settings.openai_api_key, "timeout": self.settings.model_timeout_seconds}
            if self.settings.openai_base_url:
                kwargs["base_url"] = self.settings.openai_base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _select_model(self, request: GenerationRequest) -> str:
        return request.model or (self.settings.reasoning_model if request.reasoning else self.settings.default_model)

    @staticmethod
    def _extract_content(response: Any) -> str:
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise GenerationError("Model provider returned no completion content.") from error
        if not content:
            raise GenerationError("Model provider returned empty completion content.")
        return content

    @staticmethod
    def _cache_key(request: GenerationRequest) -> str:
        body = json.dumps(
            {
                "task": request.task,
                "system": request.system_prompt,
                "user": request.user_prompt,
                "model": request.model,
                "output": request.output_model.model_json_schema(),
                "reasoning": request.reasoning,
                "images": [sha256(value.encode()).hexdigest() for value in request.image_data_urls],
            },
            sort_keys=True,
            default=str,
        )
        return sha256(body.encode()).hexdigest()


class StaticLLMGateway:
    """Deterministic gateway for tests, demos, and offline workflow development."""

    def __init__(self, responses: dict[str, BaseModel]):
        self.responses = responses
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        self.requests.append(request)
        response = self.responses.get(request.task)
        if response is None:
            raise GenerationError(f"No static response configured for task '{request.task}'.")
        if not isinstance(response, request.output_model):
            raise GenerationError(
                f"Static response for '{request.task}' is {type(response).__name__}, "
                f"expected {request.output_model.__name__}."
            )
        return GenerationResponse(
            value=response,
            metadata=GenerationMetadata(
                task=request.task,
                model="static-test-model",
                prompt_version=request.prompt_version,
                input_hash="static",
            ),
        )


def _strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Constrain every object node so provider schema validation is meaningful."""

    cloned = json.loads(json.dumps(schema))

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" or "properties" in node:
                node["additionalProperties"] = False
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(cloned)
    return cloned
""

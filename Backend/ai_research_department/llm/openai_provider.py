from __future__ import annotations

import json
import os
from typing import Type, TypeVar

from pydantic import BaseModel

from ai_research_department.config import load_backend_env
from ai_research_department.llm.base import LLMProvider
from ai_research_department.repositories.sqlite_repository import validate_model

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMProvider):
    """OpenAI structured output provider.

    This class is intentionally not used by the default MVP workflow, which runs
    without API keys. Instantiate it only when `OPENAI_API_KEY` is configured.
    """

    def __init__(self, model: str | None = None) -> None:
        load_backend_env()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
    ) -> T:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        import asyncio

        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=api_key,
            default_headers={"Accept-Encoding": "identity"},
            max_retries=0,
            timeout=self.timeout_seconds,
        )
        schema = (
            output_schema.model_json_schema()
            if hasattr(output_schema, "model_json_schema")
            else output_schema.schema()
        )
        response = await asyncio.wait_for(
            client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                store=False,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": output_schema.__name__,
                        "schema": schema,
                        "strict": False,
                    }
                },
            ),
            timeout=self.timeout_seconds + 5,
        )
        if not response.output_text:
            raise RuntimeError("OpenAI returned an empty response.")
        return validate_model(output_schema, json.loads(response.output_text))

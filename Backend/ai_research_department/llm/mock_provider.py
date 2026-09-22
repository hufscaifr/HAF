from __future__ import annotations

from typing import Type, TypeVar

from pydantic import BaseModel

from ai_research_department.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Deterministic provider for tests and offline demos."""

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
    ) -> T:
        return output_schema()

from __future__ import annotations

import asyncio

from ai_research_department.models import ResearchRequest
from ai_research_department.orchestration.research_director import ResearchDirector


def run_research_sync(request: ResearchRequest, database_path: str | None = None) -> dict:
    """Synchronous helper for scripts and tests."""
    director = ResearchDirector(database_path=database_path)
    return asyncio.run(director.run_research(request))

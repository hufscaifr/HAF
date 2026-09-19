"""Multi-agent equity research department backend."""

from ai_research_department.models import ResearchRequest
from ai_research_department.orchestration.research_director import ResearchDirector

__all__ = ["ResearchDirector", "ResearchRequest"]

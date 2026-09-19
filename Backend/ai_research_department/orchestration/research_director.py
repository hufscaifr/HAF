from __future__ import annotations

from pathlib import Path
from typing import Optional

from ai_research_department.config import load_backend_env
from ai_research_department.models import ResearchProject, ResearchRequest
from ai_research_department.orchestration.research_manager import ResearchManager, default_workspace_path
from ai_research_department.repositories.sqlite_repository import SQLiteWorkspaceRepository
from ai_research_department.services.company_resolver import resolve_company
from ai_research_department.workspace.research_context import ResearchContext
from cam_pipeline.krx_listings import refresh_krx_listings


class ResearchDirector:
    """Create projects and delegate execution to the Research Manager."""

    def __init__(self, database_path: Optional[str | Path] = None) -> None:
        self.repository = SQLiteWorkspaceRepository(database_path or default_workspace_path())

    async def run_research(self, request: ResearchRequest) -> dict:
        """Create and run a research project."""
        krx_refresh_status = None
        if request.refresh_krx_listings:
            load_backend_env()
            krx_refresh_status = refresh_krx_listings()
        if request.data_mode == "real":
            resolved = resolve_company(
                company=request.company,
                ticker=request.ticker,
                market=request.market,
            )
            request.company = resolved.company
            request.ticker = resolved.ticker
            request.market = resolved.market
        project = ResearchProject(request=request)
        context = ResearchContext(project=project, repository=self.repository)
        manager = ResearchManager(context)
        manager.log("[Research Director] Research project created.")
        if krx_refresh_status:
            manager.log(
                "[Research Director] KRX listings refreshed "
                f"(total={krx_refresh_status.get('total')}, counts={krx_refresh_status.get('counts')})."
            )
        manager.log(
            f"[Research Director] Company={request.company}, ticker={request.ticker}, "
            f"market={request.market or 'N/A'}, type={request.research_type}, data_mode={request.data_mode}."
        )
        return await manager.run()

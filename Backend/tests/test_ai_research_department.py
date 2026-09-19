from __future__ import annotations

import asyncio

import pytest

from ai_research_department.agents.base import AgentResult, JuniorAgent, SeniorAgent
from ai_research_department.financial.calculations import calculate_eps, calculate_revenue, calculate_revision_pct
from ai_research_department.models import ReportClaim, ResearchProject, ResearchRequest, ResearchTask
from ai_research_department.orchestration.research_manager import Department, ResearchManager
from ai_research_department.orchestration.workflow import run_research_sync
from ai_research_department.enums import ResearchStage, ReviewDecision
from ai_research_department.repositories.sqlite_repository import SQLiteWorkspaceRepository
from ai_research_department.utils.number_format import format_korean_number
from ai_research_department.workspace.lineage import validate_claim_lineage
from ai_research_department.workspace.research_context import ResearchContext


class CountingJunior(JuniorAgent):
    def __init__(self) -> None:
        super().__init__("CountingJunior", "test")
        self.count = 0

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        self.count += 1
        return AgentResult(status="completed", summary=f"junior run {self.count}")


class RevisionThenApproveSenior(SeniorAgent):
    def __init__(self) -> None:
        super().__init__("RevisionThenApproveSenior", "test")
        self.count = 0

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        self.count += 1
        if self.count == 1:
            context.save_review(self.build_review(task.task_id, ReviewDecision.REVISION_REQUIRED, "revise"))
            return AgentResult(status="revision_required", summary="revise")
        context.save_review(self.build_review(task.task_id, ReviewDecision.APPROVED, "approved"))
        return AgentResult(status="completed", summary="approved")


class AlwaysRevisionSenior(SeniorAgent):
    def __init__(self) -> None:
        super().__init__("AlwaysRevisionSenior", "test")

    async def execute(self, task: ResearchTask, context: ResearchContext) -> AgentResult:
        return AgentResult(status="revision_required", summary="still bad")


def make_context(tmp_path) -> ResearchContext:
    request = ResearchRequest(company="Example Electronics", ticker="000000", as_of_date="2026-09-19")
    project = ResearchProject(request=request)
    repo = SQLiteWorkspaceRepository(tmp_path / "workspace.db")
    return ResearchContext(project, repo)


def test_senior_revision_reruns_junior(tmp_path):
    context = make_context(tmp_path)
    manager = ResearchManager(context, max_review_iterations=3)
    junior = CountingJunior()
    senior = RevisionThenApproveSenior()
    department = Department("Test Dept", ResearchStage.ISSUE_DISCOVERY, junior, senior)

    asyncio.run(manager.run_department(department))

    assert junior.count == 2
    assert senior.count == 2


def test_max_review_iterations_stops_loop(tmp_path):
    context = make_context(tmp_path)
    manager = ResearchManager(context, max_review_iterations=2)
    department = Department("Loop Dept", ResearchStage.ISSUE_DISCOVERY, CountingJunior(), AlwaysRevisionSenior())

    with pytest.raises(RuntimeError):
        asyncio.run(manager.run_department(department))


def test_evidence_less_claim_is_rejected():
    claim = ReportClaim(sentence="Unsupported claim.")

    errors = validate_claim_lineage(claim, evidence=[], estimates=[], hypotheses=[])

    assert errors


def test_financial_calculation_is_deterministic():
    assert calculate_revenue(110, 112) == 12320
    assert calculate_eps(720, 2) == 360
    assert round(calculate_revision_pct(120, 100) or 0, 2) == 20


def test_workflow_reaches_completed(tmp_path):
    result = run_research_sync(
        ResearchRequest(company="Example Electronics", ticker="000000", as_of_date="2026-09-19"),
        database_path=str(tmp_path / "workflow.db"),
    )

    assert result["project"]["stage"] == ResearchStage.COMPLETED
    assert result["project"]["report_ready"] is True
    assert result["report"]["verification_passed"] is True


def test_report_numbers_match_estimate(tmp_path):
    result = run_research_sync(
        ResearchRequest(company="Example Electronics", ticker="000000", as_of_date="2026-09-19"),
        database_path=str(tmp_path / "numbers.db"),
    )
    report_text = "\n".join(section["body"] for section in result["report"]["sections"])
    estimate = result["report"]["claims"][1]["estimate_ids"][0]

    assert estimate.startswith("EST_")
    assert "1.2만원" in report_text
    assert "2,464원" in report_text


def test_korean_large_number_formatter():
    assert format_korean_number(333_605_938_000_000, "KRW") == "333.6조원"
    assert format_korean_number(43_601_051_000_000, "KRW") == "43.6조원"
    assert format_korean_number(17_489_615, "shares") == "1,749만주"
    assert format_korean_number(6_603, "KRW/share") == "6,603원"


def test_data_department_creates_visualization_artifacts(tmp_path):
    result = run_research_sync(
        ResearchRequest(company="Example Electronics", ticker="000000", as_of_date="2026-09-19"),
        database_path=str(tmp_path / "visualizations.db"),
    )

    assert result["charts"]
    assert result["tables"]
    assert result["tables"][0]["columns"]
    assert result["tables"][0]["rows"]


def test_workflow_creates_risk_assessments(tmp_path):
    result = run_research_sync(
        ResearchRequest(company="Example Electronics", ticker="000000", as_of_date="2026-09-19"),
        database_path=str(tmp_path / "risks.db"),
    )

    assert "Risk Department" in result["project"]["completed_departments"]
    assert result["risk_assessments"]
    assert all(item["approved"] for item in result["risk_assessments"])
    assert result["report"]["json_payload"]["risks"]
    assert "주가 검증" in result["report"]["json_payload"]["risks"][0]["description"]

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_research_department.agents.base import AgentResult, BaseAgent
from ai_research_department.agents.cause.junior import CauseJuniorAgent
from ai_research_department.agents.cause.senior import CauseSeniorAgent
from ai_research_department.agents.data.junior import DataJuniorAgent
from ai_research_department.agents.data.senior import DataSeniorAgent
from ai_research_department.agents.estimate.junior import EstimateJuniorAgent
from ai_research_department.agents.estimate.senior import EstimateSeniorAgent
from ai_research_department.agents.fundamental.junior import FundamentalJuniorAgent
from ai_research_department.agents.fundamental.senior import FundamentalSeniorAgent
from ai_research_department.agents.issue.junior import IssueJuniorAgent
from ai_research_department.agents.issue.senior import IssueSeniorAgent
from ai_research_department.agents.merging.junior import MergingJuniorAgent
from ai_research_department.agents.merging.senior import MergingSeniorAgent
from ai_research_department.agents.report.junior import ReportJuniorAgent
from ai_research_department.agents.report.senior import ReportSeniorAgent
from ai_research_department.agents.risk.junior import RiskJuniorAgent
from ai_research_department.agents.risk.senior import RiskSeniorAgent
from ai_research_department.agents.verification.consistency_checker import ConsistencyCheckerAgent
from ai_research_department.agents.verification.fact_checker import FactCheckerAgent
from ai_research_department.agents.verification.numerical_checker import NumericalCheckerAgent
from ai_research_department.agents.verification.senior import VerificationSeniorReviewer
from ai_research_department.constants import MAX_REVIEW_ITERATIONS
from ai_research_department.enums import ResearchStage
from ai_research_department.models import ResearchTask
from ai_research_department.repositories.sqlite_repository import dump_model
from ai_research_department.workspace.research_context import ResearchContext


@dataclass
class Department:
    """Junior and senior pairing for a research department."""

    name: str
    stage: ResearchStage
    junior: BaseAgent
    senior: BaseAgent


class ResearchManager:
    """Coordinate department execution, reviews, revisions, and final verification."""

    def __init__(self, context: ResearchContext, max_review_iterations: int = MAX_REVIEW_ITERATIONS) -> None:
        self.context = context
        self.max_review_iterations = max_review_iterations
        self.logs: list[str] = []
        data_agent = DataJuniorAgent(self.build_data_connector())
        self.departments = [
            Department("Issue Department", ResearchStage.ISSUE_DISCOVERY, IssueJuniorAgent(), IssueSeniorAgent()),
            Department("Cause Analysis Dept", ResearchStage.CAUSE_ANALYSIS, CauseJuniorAgent(), CauseSeniorAgent()),
            Department("Data Research Dept", ResearchStage.DATA_COLLECTION, data_agent, DataSeniorAgent()),
            Department("Fundamental Research Dept", ResearchStage.FUNDAMENTAL_FORECAST, FundamentalJuniorAgent(), FundamentalSeniorAgent()),
            Department("Estimate Department", ResearchStage.ESTIMATION, EstimateJuniorAgent(), EstimateSeniorAgent()),
            Department("Risk Department", ResearchStage.RISK_ANALYSIS, RiskJuniorAgent(), RiskSeniorAgent()),
            Department("Report Department", ResearchStage.REPORT_WRITING, ReportJuniorAgent(), ReportSeniorAgent()),
            Department("Merging Department", ResearchStage.MERGING, MergingJuniorAgent(), MergingSeniorAgent()),
        ]
        self.verification_agents = [
            FactCheckerAgent(),
            NumericalCheckerAgent(),
            ConsistencyCheckerAgent(),
            VerificationSeniorReviewer(),
        ]

    def build_data_connector(self):
        """Build the configured data connector for the project."""
        request = self.context.project.request
        if request.data_mode == "real":
            from ai_research_department.datasource.real import RealCompanyDataConnector

            return RealCompanyDataConnector(
                company=request.company,
                ticker=request.ticker,
                market=request.market or "KOSPI",
                period=request.price_period,
                interval=request.price_interval,
            )
        return None

    async def run(self) -> dict:
        """Run the full research workflow to completion."""
        self.log("[Research Manager] Workflow started.")
        for department in self.departments:
            await self.run_department(department)
        await self.run_verification()
        self.context.project.stage = ResearchStage.COMPLETED
        self.context.project.report_ready = True
        if self.context.reports():
            self.context.project.final_report_id = self.context.reports()[-1].report_id
        self.context.save_project()
        self.log("FINAL REPORT CREATED.")
        report = self.context.reports()[-1]
        return {
            "project": dump_model(self.context.project),
            "report": dump_model(report),
            "risk_assessments": [dump_model(risk) for risk in self.context.risk_assessments()],
            "charts": [dump_model(chart) for chart in self.context.charts()],
            "tables": [dump_model(table) for table in self.context.tables()],
            "logs": self.logs,
        }

    async def run_department(self, department: Department) -> None:
        """Run one department with junior execution and senior review loop."""
        self.context.project.stage = department.stage
        self.context.save_project()
        task = ResearchTask(
            project_id=self.context.project_id,
            stage=department.stage,
            description=f"Run {department.name}",
        )
        for iteration in range(self.max_review_iterations):
            task.iteration = iteration
            junior_result = await department.junior.execute(task, self.context)
            self.log(f"[{department.junior.name}] {junior_result.summary}")
            if junior_result.status != "completed":
                task.feedback = junior_result.summary
                continue
            senior_result = await department.senior.execute(task, self.context)
            self.log(f"[{department.senior.name}] {senior_result.summary}")
            if senior_result.status == "completed":
                self.context.project.completed_departments.append(department.name)
                self.context.save_project()
                return
            task.feedback = senior_result.summary
        self.context.project.rejected_tasks.append(task.task_id)
        self.context.save_project()
        raise RuntimeError(f"{department.name} exceeded max review iterations.")

    async def run_verification(self) -> None:
        """Run final verification department."""
        self.context.project.stage = ResearchStage.VERIFICATION
        self.context.save_project()
        task = ResearchTask(
            project_id=self.context.project_id,
            stage=ResearchStage.VERIFICATION,
            description="Verify final report",
        )
        for agent in self.verification_agents:
            result: AgentResult = await agent.execute(task, self.context)
            self.log(f"[{agent.name}] {result.summary}")
            if result.status != "completed":
                raise RuntimeError(f"Verification failed: {result.summary}")
        self.context.project.completed_departments.append("Verification Department")
        self.context.save_project()

    def log(self, message: str) -> None:
        """Record a workflow log line."""
        self.logs.append(message)


def default_workspace_path() -> Path:
    """Return the default SQLite path under the package data directory."""
    return Path(__file__).resolve().parents[1] / "data" / "research_workspace.db"

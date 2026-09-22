from __future__ import annotations

from ai_research_department.models import (
    AuditLog,
    DataRequest,
    Evidence,
    FinancialEstimate,
    Forecast,
    FundamentalAssumption,
    Hypothesis,
    Issue,
    Report,
    ReportSectionDraft,
    Review,
    RiskAssessment,
    ResearchProject,
    ChartArtifact,
    TableArtifact,
)
from ai_research_department.repositories.sqlite_repository import SQLiteWorkspaceRepository


class ResearchContext:
    """Shared workspace facade used by all agents."""

    def __init__(self, project: ResearchProject, repository: SQLiteWorkspaceRepository) -> None:
        self.project = project
        self.repository = repository
        self.save_project()

    @property
    def project_id(self) -> str:
        return self.project.project_id

    def save_project(self) -> None:
        self.repository.save("project", self.project.project_id, self.project, self.project_id)

    def add_audit(self, audit: AuditLog) -> None:
        self.repository.save("audit", audit.audit_id, audit, self.project_id)

    def save_evidence(self, evidence: Evidence) -> None:
        self.repository.save("evidence", evidence.evidence_id, evidence, self.project_id)

    def save_issue(self, issue: Issue) -> None:
        self.repository.save("issue", issue.issue_id, issue, self.project_id)

    def save_hypothesis(self, hypothesis: Hypothesis) -> None:
        self.repository.save("hypothesis", hypothesis.hypothesis_id, hypothesis, self.project_id)

    def save_data_request(self, request: DataRequest) -> None:
        self.repository.save("data_request", request.request_id, request, self.project_id)

    def save_assumption(self, assumption: FundamentalAssumption) -> None:
        self.repository.save("assumption", assumption.assumption_id, assumption, self.project_id)

    def save_forecast(self, forecast: Forecast) -> None:
        self.repository.save("forecast", forecast.forecast_id, forecast, self.project_id)

    def save_estimate(self, estimate: FinancialEstimate) -> None:
        self.repository.save("estimate", estimate.estimate_id, estimate, self.project_id)

    def save_review(self, review: Review) -> None:
        self.repository.save("review", review.review_id, review, self.project_id)

    def save_risk_assessment(self, risk: RiskAssessment) -> None:
        self.repository.save("risk_assessment", risk.risk_id, risk, self.project_id)

    def save_report(self, report: Report) -> None:
        self.repository.save("report", report.report_id, report, self.project_id)

    def save_section_draft(self, draft: ReportSectionDraft) -> None:
        self.repository.save("section_draft", draft.draft_id, draft, self.project_id)

    def save_chart(self, chart: ChartArtifact) -> None:
        self.repository.save("chart", chart.chart_id, chart, self.project_id)

    def save_table(self, table: TableArtifact) -> None:
        self.repository.save("table", table.table_id, table, self.project_id)

    def evidence(self) -> list[Evidence]:
        return self.repository.list("evidence", Evidence, self.project_id)

    def issues(self) -> list[Issue]:
        return self.repository.list("issue", Issue, self.project_id)

    def hypotheses(self) -> list[Hypothesis]:
        return self.repository.list("hypothesis", Hypothesis, self.project_id)

    def data_requests(self) -> list[DataRequest]:
        return self.repository.list("data_request", DataRequest, self.project_id)

    def assumptions(self) -> list[FundamentalAssumption]:
        return self.repository.list("assumption", FundamentalAssumption, self.project_id)

    def forecasts(self) -> list[Forecast]:
        return self.repository.list("forecast", Forecast, self.project_id)

    def estimates(self) -> list[FinancialEstimate]:
        return self.repository.list("estimate", FinancialEstimate, self.project_id)

    def risk_assessments(self) -> list[RiskAssessment]:
        return self.repository.list("risk_assessment", RiskAssessment, self.project_id)

    def reports(self) -> list[Report]:
        return self.repository.list("report", Report, self.project_id)

    def section_drafts(self) -> list[ReportSectionDraft]:
        return self.repository.list("section_draft", ReportSectionDraft, self.project_id)

    def charts(self) -> list[ChartArtifact]:
        return self.repository.list("chart", ChartArtifact, self.project_id)

    def tables(self) -> list[TableArtifact]:
        return self.repository.list("table", TableArtifact, self.project_id)

from __future__ import annotations

from ai_research_department.enums import ResearchStage


NEXT_STAGE = {
    ResearchStage.ISSUE_DISCOVERY: ResearchStage.CAUSE_ANALYSIS,
    ResearchStage.CAUSE_ANALYSIS: ResearchStage.DATA_COLLECTION,
    ResearchStage.DATA_COLLECTION: ResearchStage.FUNDAMENTAL_FORECAST,
    ResearchStage.FUNDAMENTAL_FORECAST: ResearchStage.ESTIMATION,
    ResearchStage.ESTIMATION: ResearchStage.RISK_ANALYSIS,
    ResearchStage.RISK_ANALYSIS: ResearchStage.REPORT_WRITING,
    ResearchStage.REPORT_WRITING: ResearchStage.MERGING,
    ResearchStage.MERGING: ResearchStage.VERIFICATION,
    ResearchStage.VERIFICATION: ResearchStage.COMPLETED,
}


def next_stage(stage: ResearchStage) -> ResearchStage:
    """Return the next normal workflow stage."""
    return NEXT_STAGE[stage]

from __future__ import annotations

from ai_research_department.models import Evidence, FinancialEstimate, Hypothesis, ReportClaim


def validate_claim_lineage(
    claim: ReportClaim,
    evidence: list[Evidence],
    estimates: list[FinancialEstimate],
    hypotheses: list[Hypothesis],
) -> list[str]:
    """Return lineage errors for a report claim."""
    errors: list[str] = []
    evidence_ids = {item.evidence_id for item in evidence}
    estimate_ids = {item.estimate_id for item in estimates}
    hypothesis_ids = {item.hypothesis_id for item in hypotheses}

    if not claim.evidence_ids and not claim.estimate_ids and not claim.hypothesis_ids:
        errors.append(f"{claim.claim_id} has no lineage.")
    for evidence_id in claim.evidence_ids:
        if evidence_id not in evidence_ids:
            errors.append(f"{claim.claim_id} references missing evidence {evidence_id}.")
    for estimate_id in claim.estimate_ids:
        if estimate_id not in estimate_ids:
            errors.append(f"{claim.claim_id} references missing estimate {estimate_id}.")
    for hypothesis_id in claim.hypothesis_ids:
        if hypothesis_id not in hypothesis_ids:
            errors.append(f"{claim.claim_id} references missing hypothesis {hypothesis_id}.")
    return errors

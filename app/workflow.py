from __future__ import annotations

from app.models import (
    AuditEvent,
    CopilotResult,
    IntakeRequest,
    WorkflowStatus,
)
from app.policies import PolicyRepository
from app.tools import ToolRegistry


class HealthcareOperationsCopilot:
    """Deterministic, auditable agent workflow with an explicit human-review gate."""

    def __init__(self, policies: PolicyRepository | None = None) -> None:
        self.tools = ToolRegistry(policies or PolicyRepository())

    def process(self, intake: IntakeRequest) -> CopilotResult:
        trace = []
        audit = [AuditEvent(event="intake_received", detail={"request_id": intake.request_id})]

        review_reasons = self.tools.call("validate_intake", trace, intake=intake)
        citations = self.tools.call("retrieve_policy", trace, intake=intake)
        if not citations:
            review_reasons.append("No matching operational policy was found")

        needs_review = bool(review_reasons)
        tasks = self.tools.call(
            "create_tasks", trace, intake=intake, needs_review=needs_review
        )
        status = (
            WorkflowStatus.NEEDS_HUMAN_REVIEW if needs_review else WorkflowStatus.READY
        )
        operational_priority = intake.submitted_urgency.value
        audit.extend(
            [
                AuditEvent(
                    event="policy_retrieved",
                    detail={"policy_ids": [item.policy_id for item in citations]},
                ),
                AuditEvent(
                    event="workflow_routed",
                    detail={"status": status.value, "review_reasons": review_reasons},
                ),
            ]
        )
        return CopilotResult(
            request_id=intake.request_id,
            status=status,
            operational_priority=operational_priority,
            summary=(
                f"Prepared {len(tasks)} operational task(s) for "
                f"{intake.request_type.value.replace('_', ' ')}."
            ),
            human_review_reasons=review_reasons,
            tasks=tasks,
            citations=citations,
            tool_trace=trace,
            audit_trail=audit,
        )


from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any

from app.models import IntakeRequest, OperationsTask, RequestType, ToolCall
from app.policies import PolicyRepository


class ToolRegistry:
    """Small, explicit tool layer so every agent action is inspectable and testable."""

    def __init__(self, policies: PolicyRepository) -> None:
        self.policies = policies
        self._tools: dict[str, Callable[..., Any]] = {
            "validate_intake": self.validate_intake,
            "retrieve_policy": self.retrieve_policy,
            "create_tasks": self.create_tasks,
        }

    def call(self, name: str, trace: list[ToolCall], **kwargs: Any) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        started = perf_counter()
        output = self._tools[name](**kwargs)
        trace.append(
            ToolCall(
                tool=name,
                input_summary=self._summarize(kwargs),
                output_summary=self._summarize(output),
                duration_ms=max(0, int((perf_counter() - started) * 1000)),
            )
        )
        return output

    @staticmethod
    def validate_intake(intake: IntakeRequest) -> list[str]:
        reasons: list[str] = []
        if not intake.consent_confirmed:
            reasons.append("Consent has not been confirmed")
        if intake.request_type == RequestType.PRIOR_AUTHORIZATION and not intake.insurance_plan:
            reasons.append("Insurance plan is required for prior authorization")
        if intake.request_type in {RequestType.PRIOR_AUTHORIZATION, RequestType.REFERRAL}:
            if not intake.attachments:
                reasons.append("Supporting documents are missing")
        if intake.submitted_urgency.value == "urgent":
            reasons.append("Urgent submissions require staff review")
        return reasons

    def retrieve_policy(self, intake: IntakeRequest):
        return self.policies.find(intake.request_type)

    @staticmethod
    def create_tasks(intake: IntakeRequest, needs_review: bool) -> list[OperationsTask]:
        queues = {
            RequestType.PRIOR_AUTHORIZATION: "authorization-team",
            RequestType.REFERRAL: "referral-coordination",
            RequestType.SCHEDULING: "scheduling-desk",
            RequestType.RECORDS_REQUEST: "health-information-management",
        }
        action = {
            RequestType.PRIOR_AUTHORIZATION: "Verify benefits and submit authorization packet",
            RequestType.REFERRAL: "Validate referral packet and route to receiving clinic",
            RequestType.SCHEDULING: "Contact requester and offer eligible appointment slots",
            RequestType.RECORDS_REQUEST: (
                "Validate release requirements and prepare records request"
            ),
        }[intake.request_type]
        tasks = [
            OperationsTask(
                task_id=f"{intake.request_id}-01",
                owner_queue=queues[intake.request_type],
                action=action,
                priority=intake.submitted_urgency.value,
            )
        ]
        if needs_review:
            tasks.insert(
                0,
                OperationsTask(
                    task_id=f"{intake.request_id}-review",
                    owner_queue="human-review",
                    action="Review flagged intake before downstream processing",
                    priority="urgent" if intake.submitted_urgency.value == "urgent" else "soon",
                ),
            )
        return tasks

    @staticmethod
    def _summarize(value: Any) -> str:
        text = str(value)
        return text if len(text) <= 180 else f"{text[:177]}..."


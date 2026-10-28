from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RequestType(StrEnum):
    PRIOR_AUTHORIZATION = "prior_authorization"
    REFERRAL = "referral"
    SCHEDULING = "scheduling"
    RECORDS_REQUEST = "records_request"


class SubmittedUrgency(StrEnum):
    ROUTINE = "routine"
    SOON = "soon"
    URGENT = "urgent"


class WorkflowStatus(StrEnum):
    READY = "ready"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    APPROVED = "approved"


class IntakeRequest(BaseModel):
    request_id: str = Field(min_length=3, max_length=64)
    request_type: RequestType
    submitted_urgency: SubmittedUrgency = SubmittedUrgency.ROUTINE
    requested_service: str = Field(min_length=2, max_length=200)
    referring_department: str = Field(min_length=2, max_length=100)
    insurance_plan: str | None = Field(default=None, max_length=100)
    consent_confirmed: bool = False
    attachments: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=1000)


class Citation(BaseModel):
    policy_id: str
    title: str
    section: str
    excerpt: str


class OperationsTask(BaseModel):
    task_id: str
    owner_queue: str
    action: str
    priority: str


class ToolCall(BaseModel):
    tool: str
    input_summary: str
    output_summary: str
    duration_ms: int


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event: str
    detail: dict[str, Any] = Field(default_factory=dict)


class CopilotResult(BaseModel):
    request_id: str
    status: WorkflowStatus
    operational_priority: str
    summary: str
    human_review_reasons: list[str]
    tasks: list[OperationsTask]
    citations: list[Citation]
    tool_trace: list[ToolCall]
    audit_trail: list[AuditEvent]
    disclaimer: str = (
        "Operational support only. This output is not medical advice and must not be used "
        "for diagnosis, treatment, or emergency decisions."
    )


class ApprovalRequest(BaseModel):
    reviewer: str = Field(min_length=2, max_length=100)
    note: str | None = Field(default=None, max_length=500)


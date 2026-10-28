from app.models import IntakeRequest, WorkflowStatus
from app.workflow import HealthcareOperationsCopilot


def make_intake(**overrides):
    payload = {
        "request_id": "REQ-100",
        "request_type": "scheduling",
        "submitted_urgency": "routine",
        "requested_service": "Annual wellness visit",
        "referring_department": "Primary Care",
        "consent_confirmed": True,
    }
    payload.update(overrides)
    return IntakeRequest(**payload)


def test_complete_intake_is_ready_with_a_policy_citation():
    result = HealthcareOperationsCopilot().process(make_intake())

    assert result.status == WorkflowStatus.READY
    assert result.citations[0].policy_id == "OPS-SCH-003"
    assert result.tasks[0].owner_queue == "scheduling-desk"
    assert [call.tool for call in result.tool_trace] == [
        "validate_intake",
        "retrieve_policy",
        "create_tasks",
    ]


def test_missing_consent_routes_to_human_review():
    result = HealthcareOperationsCopilot().process(make_intake(consent_confirmed=False))

    assert result.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert "Consent has not been confirmed" in result.human_review_reasons
    assert result.tasks[0].owner_queue == "human-review"


def test_urgent_request_always_requires_human_review():
    result = HealthcareOperationsCopilot().process(
        make_intake(submitted_urgency="urgent")
    )

    assert result.status == WorkflowStatus.NEEDS_HUMAN_REVIEW
    assert "Urgent submissions require staff review" in result.human_review_reasons


def test_prior_authorization_requires_plan_and_attachment():
    result = HealthcareOperationsCopilot().process(
        make_intake(request_type="prior_authorization")
    )

    assert "Insurance plan is required for prior authorization" in result.human_review_reasons
    assert "Supporting documents are missing" in result.human_review_reasons


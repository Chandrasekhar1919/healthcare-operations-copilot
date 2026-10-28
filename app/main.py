from fastapi import FastAPI, HTTPException

from app.models import ApprovalRequest, CopilotResult, IntakeRequest
from app.store import ResultStore
from app.workflow import HealthcareOperationsCopilot

app = FastAPI(
    title="Healthcare Operations Copilot",
    version="0.1.0",
    description="Auditable agent workflow for synthetic healthcare operations requests.",
)
copilot = HealthcareOperationsCopilot()
store = ResultStore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/intakes/analyze", response_model=CopilotResult)
def analyze_intake(intake: IntakeRequest) -> CopilotResult:
    return store.save(copilot.process(intake))


@app.get("/v1/intakes/{request_id}", response_model=CopilotResult)
def get_intake(request_id: str) -> CopilotResult:
    result = store.get(request_id)
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")
    return result


@app.post("/v1/intakes/{request_id}/approve", response_model=CopilotResult)
def approve_intake(request_id: str, approval: ApprovalRequest) -> CopilotResult:
    result = store.approve(request_id, approval.reviewer, approval.note)
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")
    return result


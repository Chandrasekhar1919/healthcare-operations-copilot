from __future__ import annotations

from copy import deepcopy
from threading import Lock

from app.models import AuditEvent, CopilotResult, WorkflowStatus


class ResultStore:
    """Thread-safe demo store. Replace with a database adapter in production."""

    def __init__(self) -> None:
        self._items: dict[str, CopilotResult] = {}
        self._lock = Lock()

    def save(self, result: CopilotResult) -> CopilotResult:
        with self._lock:
            self._items[result.request_id] = deepcopy(result)
        return result

    def get(self, request_id: str) -> CopilotResult | None:
        with self._lock:
            item = self._items.get(request_id)
            return deepcopy(item) if item else None

    def approve(self, request_id: str, reviewer: str, note: str | None) -> CopilotResult | None:
        with self._lock:
            item = self._items.get(request_id)
            if not item:
                return None
            item.status = WorkflowStatus.APPROVED
            item.audit_trail.append(
                AuditEvent(event="human_approved", detail={"reviewer": reviewer, "note": note})
            )
            return deepcopy(item)


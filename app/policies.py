from __future__ import annotations

import json
from pathlib import Path

from app.models import Citation, RequestType


class PolicyRepository:
    def __init__(self, policy_path: Path | None = None) -> None:
        default_path = Path(__file__).resolve().parents[1] / "data" / "policies.json"
        self.policy_path = policy_path or default_path
        self._policies = json.loads(self.policy_path.read_text(encoding="utf-8"))

    def find(self, request_type: RequestType) -> list[Citation]:
        matches = []
        for policy in self._policies:
            if request_type.value in policy["request_types"]:
                matches.append(
                    Citation(
                        policy_id=policy["policy_id"],
                        title=policy["title"],
                        section=policy["section"],
                        excerpt=policy["excerpt"],
                    )
                )
        return matches


from __future__ import annotations

import json
from pathlib import Path

from app.models import IntakeRequest
from app.workflow import HealthcareOperationsCopilot


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "data" / "evaluation_cases.json").read_text())
    copilot = HealthcareOperationsCopilot()
    passed = 0
    details = []
    for case in cases:
        result = copilot.process(IntakeRequest(**case["intake"]))
        status_ok = result.status.value == case["expected_status"]
        queue_ok = any(task.owner_queue == case["expected_queue"] for task in result.tasks)
        case_passed = status_ok and queue_ok
        passed += int(case_passed)
        details.append({"case": case["name"], "passed": case_passed})
    report = {
        "cases": len(cases),
        "passed": passed,
        "pass_rate": round(passed / len(cases), 3),
        "details": details,
    }
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()


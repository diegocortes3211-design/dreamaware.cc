from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json
import time
import os

from .executive import Executive
from .evaluator import Evaluator
from .self_modify import SelfModifier


def run_once(objective: str) -> Dict[str, Any]:
    logs = Path("logs") / "agentics"
    logs.mkdir(parents=True, exist_ok=True)

    execu = Executive()
    evalr = Evaluator()
    mod = SelfModifier()

    plan = execu.plan(objective)
    exec_out = execu.run(plan)
    evaluation = evalr.evaluate(exec_out)
    proposals = mod.propose(evaluation)
    proposal_path = mod.persist(proposals, logs)

    report = {
        "objective": objective,
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "executive": exec_out,
        "evaluation": evaluation,
        "proposals_file": str(proposal_path),
    }
    (logs / "last_report.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    obj = os.environ.get("AGENTICS_OBJECTIVE", "harden repository and raise safety score")
    out = run_once(obj)
    print(json.dumps(out, indent=2))
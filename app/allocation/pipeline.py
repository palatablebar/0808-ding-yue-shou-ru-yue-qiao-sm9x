"""合同归属模式的阶段流水线。"""

from app.allocation import contract
from app.business import DomainIssue
from app.modules.grouping import case_groups
from app.spec import CONTRACT_KINDS


def evaluate_case(rows):
    case = {
        "case": rows[0]["case"],
        "records": [r["record"] for r in rows],
        "status": "READY",
    }
    foreign = [r for r in rows if r["kind"] not in CONTRACT_KINDS]
    if foreign:
        case["status"] = "UNKNOWN_KIND"
        case["issues"] = [
            {
                "line": r["line"],
                "record": r["record"],
                "seat": r.get("seat", ""),
                "department": r.get("department", ""),
            }
            for r in foreign
        ]
        return case
    try:
        case["allocation"] = contract.evaluate(rows)
    except DomainIssue as error:
        case["status"] = error.code
        case["issues"] = getattr(error, "details", [])
    return case


def run_allocation(intake, stage=6):
    """stage 仅用于保持与月桥流水线一致的入口形状；归属在一次评估内完成。"""
    cases = [evaluate_case(rows) for _, rows in case_groups(intake["rows"])]
    return cases

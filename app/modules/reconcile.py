from collections import Counter


def _bridge_balance(intake, cases):
    status = Counter(case["status"] for case in cases)
    ready = status.pop("READY", 0)
    observed = sum(len(case["records"]) for case in cases)
    accounted = (
        intake["accepted"] + intake["rejected"] + intake["blank"] + intake["repeated"]
    )
    return dict(
        input=intake["input"],
        accepted=intake["accepted"],
        isolated=intake["rejected"],
        ignored=intake["blank"] + intake["repeated"],
        accounted=accounted,
        balanced=accounted == intake["input"] and observed == intake["accepted"],
        ready=ready,
        pending=len(cases) - ready,
        issues=dict(sorted(status.items())),
        releasable=bool(cases)
        and ready == len(cases)
        and not intake["rejected"]
        and accounted == intake["input"]
        and observed == intake["accepted"],
    )


def _allocation_balance(intake, cases):
    status = Counter(case["status"] for case in cases)
    ready = status.pop("READY", 0)
    observed = sum(len(case["records"]) for case in cases)
    accounted = (
        intake["accepted"] + intake["rejected"] + intake["blank"] + intake["repeated"]
    )
    revenue = sum(
        case["allocation"]["revenue_cents"]
        for case in cases
        if case["status"] == "READY"
    )
    department_total = sum(
        case["allocation"]["department_total_cents"]
        for case in cases
        if case["status"] == "READY"
    )
    # 部门实际使用金额之和必须与合同收入逐分对账一致。
    reconciled = revenue == department_total
    return dict(
        input=intake["input"],
        accepted=intake["accepted"],
        isolated=intake["rejected"],
        ignored=intake["blank"] + intake["repeated"],
        accounted=accounted,
        balanced=accounted == intake["input"] and observed == intake["accepted"],
        ready=ready,
        pending=len(cases) - ready,
        issues=dict(sorted(status.items())),
        contract_revenue_cents=revenue,
        department_usage_cents=department_total,
        reconcile_delta_cents=department_total - revenue,
        reconciled=reconciled,
        releasable=bool(cases)
        and ready == len(cases)
        and reconciled
        and not intake["rejected"]
        and accounted == intake["input"]
        and observed == intake["accepted"],
    )


def balance(intake, cases, allocation=False):
    if allocation:
        return _allocation_balance(intake, cases)
    return _bridge_balance(intake, cases)

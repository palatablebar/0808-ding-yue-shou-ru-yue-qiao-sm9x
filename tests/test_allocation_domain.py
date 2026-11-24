"""集团合同收入与部门归属领域规则测试。"""

import pytest

from alloc_helpers import alloc_csv, assign, contract, cover
from app.allocation.contract import evaluate
from app.business import DomainIssue

W = 43200


def parse(rows):
    """经完整采信管线把 CSV 行转为领域行，确保与真实入口同口径。"""
    from app.intake.service import inspect

    return inspect(alloc_csv(rows))["rows"]


def test_mid_month_transfer_splits_proportionally_and_reconciles():
    rows = parse(
        [
            contract("C1", "G1", 6000),
            assign("A1", "G1", "S1", "销售部", 0, W // 2),
            assign("A2", "G1", "S1", "交付部", W // 2, W),
            cover("G1", "S2", "销售部"),
        ]
    )
    result = evaluate(rows)
    # 席位金额 3000，转移席位按半月各得 1500，原部门与新部门都不能独占整月。
    s1 = next(s for s in result["seat_results"] if s["seat"] == "S1")
    assert [p["amount_cents"] for p in s1["assignments"]] == [1500, 1500]
    by_dept = {d["department"]: d["amount_cents"] for d in result["departments"]}
    assert by_dept == {"销售部": 4500, "交付部": 1500}
    # 部门实际使用金额之和与合同收入逐分对账一致。
    assert result["department_total_cents"] == result["revenue_cents"] == 6000
    assert result["reconcile_delta_cents"] == 0


def test_largest_remainder_allocates_leftover_cents_without_loss():
    rows = parse(
        [
            contract("C1", "G1", 100, end=1000),
            assign("A1", "G1", "S1", "甲", 0, 333),
            assign("A2", "G1", "S1", "乙", 333, 666),
            assign("A3", "G1", "S1", "丙", 666, 1000),
        ]
    )
    result = evaluate(rows)
    amounts = sorted(d["amount_cents"] for d in result["departments"])
    assert amounts == [33, 33, 34]
    assert result["department_total_cents"] == 100


def test_overlap_lists_all_participating_records_and_blocks():
    rows = parse(
        [
            contract("C1", "G1", 3000),
            assign("A1", "G1", "S1", "销售部", 0, 21600),
            assign("A2", "G1", "S1", "交付部", 20000, W),
        ]
    )
    with pytest.raises(DomainIssue) as exc:
        evaluate(rows)
    assert exc.value.code == "ASSIGN_OVERLAP"
    records = {item["record"] for item in exc.value.details}
    assert records == {"A1", "A2"}


def test_gap_lists_adjacent_records_and_blocks():
    rows = parse(
        [
            contract("C1", "G1", 3000),
            assign("A1", "G1", "S1", "销售部", 0, 21600),
            assign("A2", "G1", "S1", "交付部", 25000, W),
        ]
    )
    with pytest.raises(DomainIssue) as exc:
        evaluate(rows)
    assert exc.value.code == "COVERAGE_GAP"
    assert {item["record"] for item in exc.value.details} == {"A1", "A2"}


def test_coverage_must_start_at_window_origin():
    rows = parse(
        [
            contract("C1", "G1", 3000),
            assign("A1", "G1", "S1", "销售部", 100, W),
        ]
    )
    with pytest.raises(DomainIssue, match="COVERAGE_GAP"):
        evaluate(rows)


def test_window_breach_is_rejected():
    rows = parse(
        [
            contract("C1", "G1", 3000),
            assign("A1", "G1", "S1", "销售部", 0, W + 1),
        ]
    )
    with pytest.raises(DomainIssue, match="WINDOW_BREACH"):
        evaluate(rows)


def test_invalid_span_is_rejected():
    rows = parse(
        [
            contract("C1", "G1", 3000),
            assign("A1", "G1", "S1", "销售部", 200, 100),
        ]
    )
    with pytest.raises(DomainIssue, match="ASSIGN_INVALID_SPAN"):
        evaluate(rows)


def test_seat_without_assignment_is_missing():
    rows = parse([contract("C1", "G1", 3000)])
    with pytest.raises(DomainIssue, match="SEAT_MISSING"):
        evaluate(rows)


def test_indivisible_seat_rate_blocks():
    rows = parse(
        [
            contract("C1", "G1", 703),
            cover("G1", "S1", "研发部"),
            cover("G1", "S2", "研发部"),
        ]
    )
    with pytest.raises(DomainIssue, match="SEAT_RATE_INDIVISIBLE"):
        evaluate(rows)


def test_contract_must_be_single():
    rows = parse(
        [
            contract("C1", "G1", 3000),
            contract("C2", "G1", 3000),
            cover("G1", "S1", "财务部"),
        ]
    )
    with pytest.raises(DomainIssue) as exc:
        evaluate(rows)
    assert exc.value.code == "CONTRACT_NOT_SINGLE"
    assert {item["record"] for item in exc.value.details} == {"C1", "C2"}


def test_contract_missing_when_only_assignments():
    rows = parse([cover("G1", "S1", "财务部", record="A1")])
    with pytest.raises(DomainIssue, match="CONTRACT_MISSING"):
        evaluate(rows)


def test_zero_revenue_contract_is_rejected():
    rows = parse(
        [
            contract("C1", "G1", 0),
            cover("G1", "S1", "财务部"),
        ]
    )
    with pytest.raises(DomainIssue, match="CONTRACT_AMOUNT_ZERO"):
        evaluate(rows)


def test_invalid_window_is_rejected():
    rows = parse(
        [
            contract("C1", "G1", 3000, start=100, end=100),
            cover("G1", "S1", "财务部"),
        ]
    )
    with pytest.raises(DomainIssue, match="INVALID_PERIOD"):
        evaluate(rows)


def test_three_way_split_is_exact_and_deterministic():
    rows = parse(
        [
            contract("C1", "G1", 10000),
            assign("A1", "G1", "S1", "甲", 0, 10000),
            assign("A2", "G1", "S1", "乙", 10000, 25000),
            assign("A3", "G1", "S1", "丙", 25000, W),
        ]
    )
    first = evaluate(rows)
    second = evaluate(rows)
    assert first == second
    assert sum(d["amount_cents"] for d in first["departments"]) == 10000

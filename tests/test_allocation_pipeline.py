"""合同归属的流水线、对账与签发阻塞测试。"""

import pytest

from alloc_helpers import alloc_csv, assign, contract, cover
from app.business import DomainIssue
from app.modules.pipeline import run
from app.review.service import execute, review

W = 43200


def ready_source():
    return alloc_csv(
        [
            contract("C1", "G1", 6000),
            assign("A1", "G1", "S1", "销售部", 0, W // 2),
            assign("A2", "G1", "S1", "交付部", W // 2, W),
            cover("G1", "S2", "销售部"),
        ]
    )


def overlap_source():
    return alloc_csv(
        [
            contract("C1", "G1", 3000),
            assign("A1", "G1", "S1", "销售部", 0, 21600),
            assign("A2", "G1", "S1", "交付部", 20000, W),
        ]
    )


def test_mode_is_detected_as_allocation():
    assert run(ready_source())["mode"] == "allocation"


def test_ready_allocation_is_releasable_and_reconciled():
    report = run(ready_source())
    balance = report["balance"]
    assert balance["releasable"] is True
    assert balance["reconciled"] is True
    assert balance["contract_revenue_cents"] == 6000
    assert balance["department_usage_cents"] == 6000
    assert balance["reconcile_delta_cents"] == 0
    assert report["cases"][0]["status"] == "READY"


def test_overlap_blocks_release_and_keeps_participating_records():
    report = run(overlap_source())
    assert report["balance"]["releasable"] is False
    case = report["cases"][0]
    assert case["status"] == "ASSIGN_OVERLAP"
    assert {item["record"] for item in case["issues"]} == {"A1", "A2"}


def test_gap_blocks_release():
    source = alloc_csv(
        [
            contract("C1", "G1", 3000),
            assign("A1", "G1", "S1", "销售部", 0, 21600),
            assign("A2", "G1", "S1", "交付部", 25000, W),
        ]
    )
    report = run(source)
    assert report["balance"]["releasable"] is False
    assert report["cases"][0]["status"] == "COVERAGE_GAP"


def test_intake_rejection_blocks_release():
    # 部门缺测导致采信隔离，任何情况下都不得签发。
    source = alloc_csv(
        [
            contract("C1", "G1", 3000),
            ["B1", "G1", "assign", 0, 0, W, "坏行", "S1", ""],
            cover("G1", "S2", "研发部"),
        ]
    )
    balance = run(source)["balance"]
    assert balance["isolated"] == 1 and balance["releasable"] is False


def test_rerun_same_source_keeps_single_run(store):
    first = execute(store, ready_source())
    second = execute(store, ready_source())
    assert first == second and len(store.list()) == 1


def test_rerun_preserves_all_records_without_duplicate_allocation(store):
    execute(store, ready_source())
    run = execute(store, ready_source())
    case = run["report"]["cases"][0]
    # 三条归属记录全部保留，且只产生一份归属结果。
    assert len(case["allocation"]["seat_results"]) == 2
    assert len(store.list()) == 1


def test_different_sources_start_separate_runs(store):
    assert execute(store, ready_source())["id"] != execute(store, overlap_source())["id"]
    assert len(store.list()) == 2


def test_blocked_allocation_cannot_be_approved(store):
    run = execute(store, overlap_source())
    with pytest.raises(DomainIssue, match="UNRESOLVED_ISSUES"):
        review(
            store,
            run["id"],
            dict(revision=0, status="APPROVED", note="试图签发重叠归属"),
        )
    assert store.load(run["id"])["revision"] == 0


def test_ready_allocation_can_be_approved(store):
    run = execute(store, ready_source())
    output = review(
        store,
        run["id"],
        dict(revision=0, status="APPROVED", note="部门归属与合同收入对账一致"),
    )
    assert output["status"] == "APPROVED" and output["revision"] == 1


def test_bridge_mode_still_reports_bridge_mode(clean):
    assert run(clean)["mode"] == "bridge"

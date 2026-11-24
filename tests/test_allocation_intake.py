"""归属来源的采信、表头路由与字段校验测试。"""

import pytest

from alloc_helpers import alloc_csv, contract, cover
from app.business import DomainIssue
from app.intake.reader import scan
from app.intake.schema import ALLOCATION_HEADER
from app.intake.service import inspect

W = 43200


def test_allocation_header_is_recognized_as_allocation_shape():
    shape = next(scan(alloc_csv([contract("C1", "G1", 100), cover("G1", "S1", "研发部")])))
    assert shape == "allocation"


def test_bridge_header_keeps_bridge_shape(clean):
    assert next(scan(clean)) == "bridge"


def test_inspect_marks_shape_and_accepts_valid_allocation():
    result = inspect(
        alloc_csv([contract("C1", "G1", 100), cover("G1", "S1", "研发部")])
    )
    assert result["shape"] == "allocation"
    assert result["accepted"] == 2 and result["rejected"] == 0


def test_contract_row_allows_empty_seat_and_department():
    rows = inspect(alloc_csv([contract("C1", "G1", 100)]))["rows"]
    assert rows[0]["kind"] == "contract"
    assert rows[0]["seat"] == "" and rows[0]["department"] == ""


def test_blank_department_is_isolated():
    result = inspect(
        alloc_csv([contract("C1", "G1", 100), ["B1", "G1", "assign", 0, 0, W, "x", "S1", ""]])
    )
    assert result["reasons"] == {"BAD_DEPARTMENT": 1}


def test_bad_seat_identifier_is_isolated():
    result = inspect(
        alloc_csv(
            [contract("C1", "G1", 100), ["B1", "G1", "assign", 0, 0, W, "x", "S 1", "研发部"]]
        )
    )
    assert result["reasons"] == {"BAD_SEAT": 1}


def test_extra_column_in_allocation_is_isolated():
    rows = [list(ALLOCATION_HEADER) + ["意外分隔"]]
    result = inspect(alloc_csv(rows))
    assert result["reasons"] == {"COLUMN_COUNT": 1}


def test_repeated_allocation_header_is_ignored():
    import csv
    import io

    stream = io.StringIO(newline="")
    csv.writer(stream).writerow(ALLOCATION_HEADER)
    data = alloc_csv([contract("C1", "G1", 100)]) + stream.getvalue().encode()
    result = inspect(data)
    assert result["repeated"] == 1


def test_duplicate_conflict_both_isolated():
    result = inspect(
        alloc_csv(
            [
                contract("C1", "G1", 100),
                ["D1", "G1", "assign", 0, 0, W, "v1", "S1", "研发部"],
                ["D1", "G1", "assign", 0, 0, W, "v2", "S1", "交付部"],
            ]
        )
    )
    assert result["reasons"] == {"DUPLICATE_CONFLICT": 2}


def test_full_width_numbers_canonicalized_in_allocation():
    row = contract("C1", "G1", "１,２３４")
    result = inspect(alloc_csv([row]))
    assert result["rows"][0]["mrr_cents"] == 1234


def test_foreign_bridge_kind_with_valid_fields_passes_intake():
    # 结构合法的月桥类型可通过采信，领域阶段再按归属模式拒收。
    result = inspect(
        alloc_csv([["K1", "G1", "opening", 0, 0, W, "x", "S1", "研发部"]])
    )
    assert result["accepted"] == 1 and result["rejected"] == 0


def test_foreign_bridge_kind_is_blocked_at_domain_stage():
    from app.allocation.pipeline import evaluate_case

    rows = inspect(
        alloc_csv([["K1", "G1", "opening", 0, 0, W, "x", "S1", "研发部"]])
    )["rows"]
    case = evaluate_case(rows)
    assert case["status"] == "UNKNOWN_KIND"
    assert case["issues"][0]["record"] == "K1"


def test_allocation_preserves_leading_zero_record_keys():
    result = inspect(
        alloc_csv([contract("000C1", "G1", 100), cover("G1", "S1", "研发部")])
    )
    assert result["rows"][0]["record"] == "000C1"


def test_allocation_empty_file_states():
    with pytest.raises(DomainIssue, match="FILE_EMPTY"):
        inspect(b"")
    with pytest.raises(DomainIssue, match="HEADER_ONLY"):
        inspect(alloc_csv([]))

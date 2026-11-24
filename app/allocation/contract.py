"""集团合同收入与部门归属领域。

每个业务组（case）对应一份集团合同：
- 恰好一条 ``contract`` 记录给出窗口 [window_start, window_end) 与唯一合同收入；
- 每条 ``assign`` 记录表示一个席位在某部门的归属区间 [start_minute, end_minute)。

席位的整窗金额按各归属区间的分钟占比分摊，余数用最大余额法逐分补齐，
因此各部门承担的实际使用金额之和与席位金额、进而与合同收入分毫不差。
"""

from collections import defaultdict

from app.business import DomainIssue


def issue(code, details=None):
    error = DomainIssue(code)
    error.details = details or []
    return error


def _contract(rows):
    contracts = [r for r in rows if r["kind"] == "contract"]
    if len(contracts) != 1:
        raise issue(
            "CONTRACT_NOT_SINGLE" if contracts else "CONTRACT_MISSING",
            [
                {"line": r["line"], "record": r["record"], "seat": "", "department": ""}
                for r in contracts
            ],
        )
    return contracts[0]


def _window(contract):
    start, end = contract["minute"], contract["sequence"]
    if start >= end:
        raise issue("INVALID_PERIOD", [_ref(contract)])
    if contract["mrr_cents"] <= 0:
        raise issue("CONTRACT_AMOUNT_ZERO", [_ref(contract)])
    return start, end, contract["mrr_cents"]


def _ref(row):
    return {
        "line": row["line"],
        "record": row["record"],
        "seat": row.get("seat", ""),
        "department": row.get("department", ""),
    }


def _check_seat(seat, spans, start, end):
    """校验单个席位的归属区间：无重叠、无断档、恰好覆盖整窗。"""
    ordered = sorted(spans, key=lambda r: (r["minute"], r["sequence"], r["record"]))
    if not ordered:
        raise issue("SEAT_MISSING", [{"seat": seat, "records": []}])
    first = ordered[0]
    if first["minute"] != start:
        raise issue("COVERAGE_GAP", [_ref(first)])
    cursor = first["sequence"]
    for index, row in enumerate(ordered[1:], 1):
        if row["minute"] < start or row["sequence"] > end:
            raise issue("WINDOW_BREACH", [_ref(row)])
        if row["minute"] < cursor:
            # 重叠：列出该席位全部参与记录，便于定位冲突双方。
            raise issue("ASSIGN_OVERLAP", [_ref(r) for r in ordered])
        if row["minute"] > cursor:
            # 断档：列出断档前后相邻的参与记录。
            raise issue("COVERAGE_GAP", [_ref(ordered[index - 1]), _ref(row)])
        cursor = row["sequence"]
    if cursor != end:
        raise issue("COVERAGE_GAP", [_ref(ordered[-1])])
    return ordered


def _allocate(rate_cents, ordered, window_minutes):
    """按分钟占比把席位整窗金额分摊到各归属区间，最大余额法补余分。"""
    weights = [(row["sequence"] - row["minute"]) for row in ordered]
    remainders, allocated = [], []
    for minutes in weights:
        scaled = rate_cents * minutes
        base, extra = divmod(scaled, window_minutes)
        remainders.append(extra)
        allocated.append(base)
    leftover = rate_cents - sum(allocated)
    # 余额相同则区间更长者优先，再按部门、记录键稳定排序，保证重跑可复现。
    order = sorted(
        range(len(ordered)),
        key=lambda i: (
            -remainders[i],
            -weights[i],
            ordered[i]["department"],
            ordered[i]["record"],
        ),
    )
    for index in order[:leftover]:
        allocated[index] += 1
    pieces = []
    for row, minutes, amount in zip(ordered, weights, allocated):
        pieces.append(
            {
                "record": row["record"],
                "line": row["line"],
                "department": row["department"],
                "start_minute": row["minute"],
                "end_minute": row["sequence"],
                "minutes": minutes,
                "amount_cents": amount,
            }
        )
    return pieces


def evaluate(rows):
    """评估一个合同业务组，返回可签发的归属结果或抛出领域问题。"""
    contract = _contract(rows)
    start, end, revenue_cents = _window(contract)
    window_minutes = end - start

    by_seat = defaultdict(list)
    for row in rows:
        if row["kind"] != "assign":
            continue
        if row["minute"] < start or row["sequence"] > end:
            raise issue("WINDOW_BREACH", [_ref(row)])
        if row["minute"] >= row["sequence"]:
            raise issue("ASSIGN_INVALID_SPAN", [_ref(row)])
        by_seat[row["seat"]].append(row)

    seats = sorted(by_seat)
    if not seats:
        raise issue("SEAT_MISSING", [{"seat": "", "records": []}])

    seat_rate, remainder = divmod(revenue_cents, len(seats))
    if remainder:
        raise issue("SEAT_RATE_INDIVISIBLE", [_ref(contract)])

    seat_results, department_totals = [], defaultdict(int)
    for seat in seats:
        ordered = _check_seat(seat, by_seat[seat], start, end)
        pieces = _allocate(seat_rate, ordered, window_minutes)
        seat_total = sum(piece["amount_cents"] for piece in pieces)
        seat_results.append(
            {
                "seat": seat,
                "rate_cents": seat_rate,
                "allocated_cents": seat_total,
                "assignments": pieces,
            }
        )
        for piece in pieces:
            department_totals[piece["department"]] += piece["amount_cents"]

    departments = [
        {"department": name, "amount_cents": department_totals[name]}
        for name in sorted(department_totals)
    ]
    department_sum = sum(item["amount_cents"] for item in departments)
    if department_sum != revenue_cents:
        raise issue(
            "ALLOCATION_MISMATCH",
            [{"expected_cents": revenue_cents, "actual_cents": department_sum}],
        )
    return {
        "contract_record": contract["record"],
        "window_start_minute": start,
        "window_end_minute": end,
        "window_minutes": window_minutes,
        "seats": len(seats),
        "revenue_cents": revenue_cents,
        "seat_rate_cents": seat_rate,
        "department_total_cents": department_sum,
        "reconcile_delta_cents": department_sum - revenue_cents,
        "departments": departments,
        "seat_results": seat_results,
    }

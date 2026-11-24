"""合同归属在并发重跑下的幂等性。"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from alloc_helpers import alloc_csv, assign, contract, cover
from app.review.service import execute

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


def test_parallel_allocation_rerun_commits_single_row(store):
    source = ready_source()
    barrier = Barrier(4)

    def load():
        barrier.wait(4)
        return execute(store, source)

    with ThreadPoolExecutor(max_workers=4) as threads:
        results = list(threads.map(lambda _: load(), range(4)))
    assert all(result == results[0] for result in results)
    assert len(store.list()) == 1
    # 唯一批次内只保留一份归属结果。
    cases = results[0]["report"]["cases"]
    assert len(cases) == 1 and len(cases[0]["allocation"]["seat_results"]) == 2

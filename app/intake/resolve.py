from collections import defaultdict


def partition(candidates):
    by_key = defaultdict(list)
    for line, row in candidates:
        by_key[row["record"]].append((line, row))
    accepted, rejected = [], []
    for key, records in by_key.items():
        first_line, first = records[0]
        if any(row != first for _, row in records):
            rejected.extend(
                {
                    "line": line,
                    "record": key,
                    "case": row["case"],
                    "reason": "DUPLICATE_CONFLICT",
                }
                for line, row in records
            )
            continue
        # 采信行保留源行号，供领域阶段引用参与记录。
        accepted.append({**first, "line": first_line})
        rejected.extend(
            {
                "line": line,
                "record": key,
                "case": row["case"],
                "reason": "DUPLICATE_REPLAY",
            }
            for line, row in records[1:]
        )
    return accepted, rejected

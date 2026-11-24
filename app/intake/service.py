from collections import Counter
from csv import Error

from app.business import DomainIssue
from app.intake.reader import scan
from app.intake.resolve import partition
from app.intake.schema import ALLOCATION_HEADER, HEADER, allocation_record, record


def inspect(data):
    counted = repeated = blanks = 0
    candidates, rejected = [], []
    iterator = scan(data)
    shape = next(iterator)
    if shape == "allocation":
        parse, header = allocation_record, ALLOCATION_HEADER
    else:
        parse, header = record, HEADER
    try:
        for line, values in iterator:
            counted += 1
            if not any(v.strip() for v in values):
                blanks += 1
                continue
            if tuple(values) == header:
                repeated += 1
                continue
            try:
                candidates.append((line, parse(values)))
            except DomainIssue as error:
                key = values[0][:36] if values else ""
                case = values[1][:36] if len(values) > 1 else ""
                rejected.append(
                    dict(line=line, record=key, case=case, reason=error.code)
                )
    except Error as error:
        raise DomainIssue("CSV_MALFORMED") from error
    accepted, conflicts = partition(candidates)
    rejects = sorted(rejected + conflicts, key=lambda row: row["line"])
    return dict(
        shape=shape,
        input=counted,
        accepted=len(accepted),
        repeated=repeated,
        blank=blanks,
        rejected=len(rejects),
        reasons=dict(Counter(r["reason"] for r in rejects)),
        isolation=rejects,
        rows=accepted,
    )

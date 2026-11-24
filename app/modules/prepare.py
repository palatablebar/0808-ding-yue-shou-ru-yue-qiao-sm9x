from app.business import DomainIssue, by_kind, prepared, single


def prepare(rows):
    base, close = single(rows, "opening"), single(rows, "close")
    if base["minute"] >= close["minute"]:
        raise DomainIssue("INVALID_PERIOD")
    events = {}
    for row in by_kind(rows, "change"):
        if not base["minute"] <= row["minute"] < close["minute"]:
            continue
        key = (row["minute"], row["sequence"])
        amount = row["mrr_cents"]
        if key in events and events[key] != amount:
            raise DomainIssue("CHANGE_CONFLICT")
        events[key] = amount
    return prepared(
        len(events),
        {"opening_cents": base["mrr_cents"], "closing_boundary": close["minute"]},
        (base["mrr_cents"], close["mrr_cents"], [events[k] for k in sorted(events)]),
    )

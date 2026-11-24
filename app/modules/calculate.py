from app.business import measured


def compute(data):
    current, close, changes = data
    totals = {
        "new_cents": 0,
        "expansion_cents": 0,
        "contraction_cents": 0,
        "churn_cents": 0,
    }
    opening = current
    for amount in changes:
        if amount > current:
            totals["new_cents" if current == 0 else "expansion_cents"] += (
                amount - current
            )
        if amount < current:
            totals["churn_cents" if amount == 0 else "contraction_cents"] += (
                current - amount
            )
        current = amount
    return measured(
        opening
        + totals["new_cents"]
        + totals["expansion_cents"]
        - totals["contraction_cents"]
        - totals["churn_cents"],
        close,
        "分",
        totals,
    )

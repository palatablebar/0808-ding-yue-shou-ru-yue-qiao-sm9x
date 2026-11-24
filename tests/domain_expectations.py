EXPECTED = {
    "0001": (2, 120, "READY"),
    "0002": (2, 0, "READY"),
    "0003": (0, None, "CHANGE_CONFLICT"),
    "0004": (1, 50, "MISMATCH"),
}
EVIDENCE = {
    "0001": {
        "new_cents": 0,
        "expansion_cents": 40,
        "contraction_cents": 20,
        "churn_cents": 0,
    },
    "0002": {
        "new_cents": 80,
        "expansion_cents": 0,
        "contraction_cents": 0,
        "churn_cents": 80,
    },
}

import io

from app.intake.schema import ALLOCATION_HEADER


def alloc_csv(rows):
    stream = io.StringIO(newline="")
    import csv

    csv.writer(stream).writerows([ALLOCATION_HEADER, *rows])
    return stream.getvalue().encode()


def contract(record, case, revenue, start=0, end=43200, note="合同"):
    return [record, case, "contract", start, revenue, end, note, "", ""]


def assign(record, case, seat, department, start, end, note="归属"):
    return [record, case, "assign", start, 0, end, note, seat, department]


def cover(case, seat, department, start=0, end=43200, record=None):
    """生成一条整窗归属记录。"""
    return assign(record or f"A-{case}-{seat}", case, seat, department, start, end)

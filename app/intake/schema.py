import re

from app.business import DomainIssue
from app.intake.numeric import quantity
from app.spec import ALL_KINDS, COLUMNS, KINDS

HEADER = ("record", "case", "kind", *COLUMNS, "note")
# 集团合同收入与部门归属来源在月桥列之后追加席位与部门两列。
ALLOCATION_HEADER = (*HEADER, "seat", "department")
IDENTIFIER = r"[A-Za-z0-9][A-Za-z0-9_.-]{0,35}"
# 部门允许中文名及常见分隔字符，长度与记录键口径一致。
DEPARTMENT = r"[\w一-鿿][\w一-鿿 .#&()（）-]{0,35}"


def _identifier(value, code="BAD_IDENTIFIER"):
    text = value.strip()
    if not re.fullmatch(IDENTIFIER, text):
        raise DomainIssue(code)
    return text


def record(values):
    if len(values) != len(HEADER):
        raise DomainIssue("COLUMN_COUNT")
    row = dict(zip(HEADER, values))
    row["record"] = _identifier(row["record"])
    row["case"] = _identifier(row["case"])
    if row["kind"] not in KINDS:
        raise DomainIssue("UNKNOWN_KIND")
    for column in COLUMNS:
        row[column] = quantity(row[column])
    if len(row["note"]) > 200:
        raise DomainIssue("NOTE_TOO_LONG")
    return row


def allocation_record(values):
    if len(values) != len(ALLOCATION_HEADER):
        raise DomainIssue("COLUMN_COUNT")
    row = dict(zip(ALLOCATION_HEADER, values))
    row["record"] = _identifier(row["record"])
    row["case"] = _identifier(row["case"])
    if row["kind"] not in ALL_KINDS:
        raise DomainIssue("UNKNOWN_KIND")
    for column in COLUMNS:
        row[column] = quantity(row[column])
    if len(row["note"]) > 200:
        raise DomainIssue("NOTE_TOO_LONG")
    if row["kind"] == "contract":
        # 合同行描述整份集团合同，不绑定具体席位与部门。
        row["seat"] = ""
        row["department"] = ""
        return row
    row["seat"] = _identifier(row["seat"], "BAD_SEAT")
    department = row["department"].strip()
    if not re.fullmatch(DEPARTMENT, department):
        raise DomainIssue("BAD_DEPARTMENT")
    row["department"] = department
    return row

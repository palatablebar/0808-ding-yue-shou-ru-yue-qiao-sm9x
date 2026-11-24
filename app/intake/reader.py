import csv
import io

from app.business import DomainIssue
from app.config import MAX_FILE, MAX_ROWS
from app.intake.schema import ALLOCATION_HEADER, HEADER


def scan(data):
    """读取来源并先产出表头形状，再逐行产出 (line, values)。

    首个产出为字符串形状："bridge"（月桥七列）或 "allocation"（合同归属九列）。
    后续产出为 (源行号, 列值列表)。保持惰性，由调用方消费并处理 csv.Error。
    """
    if len(data) > MAX_FILE:
        raise DomainIssue("FILE_TOO_LARGE")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DomainIssue("ENCODING_INVALID") from error
    if not text:
        raise DomainIssue("FILE_EMPTY")
    if not text.strip():
        raise DomainIssue("FILE_BLANK")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    header = tuple(next(reader))
    if header == HEADER:
        yield "bridge"
    elif header == ALLOCATION_HEADER:
        yield "allocation"
    else:
        raise DomainIssue("HEADER_MISMATCH")
    count = 0
    for number, row in enumerate(reader, 1):
        if number > MAX_ROWS:
            raise DomainIssue("ROW_LIMIT")
        count += 1
        yield reader.line_num, row
    if count == 0:
        raise DomainIssue("HEADER_ONLY")


def records(data):
    """月桥来源迭代器，保持既有 (line, values) 形状，拒绝归属来源。"""
    iterator = scan(data)
    if next(iterator) != "bridge":
        raise DomainIssue("HEADER_MISMATCH")
    yield from iterator

from flask import jsonify

LABELS = {
    "FILE_TOO_LARGE": "文件超过 256 KiB",
    "FILE_EMPTY": "文件没有内容",
    "FILE_BLANK": "文件只有空白",
    "HEADER_ONLY": "文件只有标题行",
    "HEADER_MISMATCH": "列名与字段字典不一致",
    "ENCODING_INVALID": "请使用 UTF-8 CSV",
    "CSV_MALFORMED": "CSV 引号或行格式异常",
    "ROW_LIMIT": "文件超过 2000 行",
    "FILE_REQUIRED": "请选择 CSV 文件",
    "RUN_NOT_FOUND": "批次不存在",
    "REVIEW_FIELDS": "请填写 3 至 200 字复核意见",
    "STALE_REVIEW": "批次已更新，请刷新",
    "RUN_FINALIZED": "批次已签发",
    "UNRESOLVED_ISSUES": "存在待处理差异",
    "SAMPLE_UNKNOWN": "样例不存在",
    "STAGE_UNKNOWN": "处理阶段不存在",
    "CONTRACT_MISSING": "缺少集团合同收入记录",
    "CONTRACT_NOT_SINGLE": "集团合同收入只能保留一份",
    "CONTRACT_AMOUNT_ZERO": "合同收入必须为正数",
    "INVALID_PERIOD": "结算窗口起止时刻无效",
    "ASSIGN_INVALID_SPAN": "归属区间结束时刻必须晚于开始时刻",
    "WINDOW_BREACH": "归属区间超出合同结算窗口",
    "ASSIGN_OVERLAP": "同一席位存在重叠归属，已列出全部参与记录",
    "COVERAGE_GAP": "席位归属出现断档，未覆盖完整结算窗口",
    "SEAT_MISSING": "合同席位缺少部门归属记录",
    "SEAT_RATE_INDIVISIBLE": "合同收入无法按席位整数分摊",
    "ALLOCATION_MISMATCH": "部门承担金额之和与合同收入对账不一致",
    "BAD_SEAT": "席位标识不符合字段规则",
    "BAD_DEPARTMENT": "部门名称不符合字段规则",
}


def response(error):
    code = error.code
    status = (
        404
        if code in {"RUN_NOT_FOUND", "SAMPLE_UNKNOWN", "STAGE_UNKNOWN"}
        else (
            409
            if code in {"STALE_REVIEW", "RUN_FINALIZED", "UNRESOLVED_ISSUES"}
            else 413 if code == "FILE_TOO_LARGE" else 422
        )
    )
    return jsonify(code=code, message=LABELS.get(code, code)), status

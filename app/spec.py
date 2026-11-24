COLUMNS = ("minute", "mrr_cents", "sequence")
KINDS = ("opening", "change", "close")
# 集团合同收入与部门归属模式使用的记录类型：
# contract 记录合同唯一收入，assign 记录席位在部门间的归属区间。
CONTRACT_KINDS = ("contract", "assign")
ALL_KINDS = KINDS + CONTRACT_KINDS
PROJECT = {
    "name": "订阅收入月桥",
    "actor": "订阅收入分析员",
    "stages": [
        ("intake", "样例采信"),
        ("prepare", "变更排序"),
        ("calculate", "月桥拆解"),
        ("policy", "余额平衡"),
        ("balance", "运行对账"),
        ("allocate", "归属分摊"),
    ],
    "chart": "净变动",
}

COLUMNS = ("minute", "mrr_cents", "sequence")
KINDS = ("opening", "change", "close")
PROJECT = {
    "name": "订阅收入月桥",
    "actor": "订阅收入分析员",
    "stages": [
        ("intake", "样例采信"),
        ("prepare", "变更排序"),
        ("calculate", "月桥拆解"),
        ("policy", "余额平衡"),
        ("balance", "运行对账"),
    ],
    "chart": "净变动",
}

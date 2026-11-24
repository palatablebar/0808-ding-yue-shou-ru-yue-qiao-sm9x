# 阶段接口

`POST /api/stages/<stage>` 接收 `multipart/form-data`。字段 `sample=dirty`、`sample=clean` 或 `file=<CSV>` 三选一；归属来源另支持 `sample=contracts_dirty`、`sample=contracts_clean`。阶段为 `intake`、`prepare`、`calculate`、`policy`、`balance`、`allocate`。预览不入库。来源按表头形状自动识别月桥模式（七列）或合同归属模式（九列）；`allocate` 在归属模式下产出部门归属与对账结果。

`POST /api/runs` 接收同样的输入，执行全批并返回运行报告。`GET /api/runs` 返回最近 50 批。`GET /api/runs/<id>` 查询一批和当前复核状态。

归属模式的运行报告在 `balance` 中额外给出 `contract_revenue_cents`（合同收入合计）、`department_usage_cents`（部门承担金额合计）、`reconcile_delta_cents`（对账差，须为 0）与 `reconciled`。每个分组的 `allocation` 含按席位的区间分摊明细 `seat_results` 与按部门的合计 `departments`。重叠归属返回 `ASSIGN_OVERLAP`、断档返回 `COVERAGE_GAP`，并在 `issues` 中列出全部参与记录；存在任一问题时 `releasable=false`，签发被拒。

`PATCH /api/runs/<id>` 接收 `revision`、`status` 和 `note`。状态使用 `APPROVED` 或 `HELD`。冲突返回 409，客户端读取新版本后重试。

`GET /api/runs/<id>/evidence` 下载内含运行清单、行号隔离、业务证据和复核信息的 JSON。

# 订阅收入月桥规则登记

- 规模：中型

## 功能模块

| 模块 | 动作 | 接口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 样例采信 | 预览并定位坏行 | `POST /api/stages/intake` | `app/intake/service.py` | `tests/test_intake.py` |
| M2 变更排序 | 检查领域约束 | `POST /api/stages/prepare` | `app/modules/prepare.py` | `tests/test_prepare.py` |
| M3 月桥拆解 | 查看业务计算结果 | `POST /api/stages/calculate` | `app/modules/calculate.py` | `tests/test_calculate.py` |
| M4 余额平衡 | 查看签收判定 | `POST /api/stages/policy` | `app/modules/policy.py` | `tests/test_policy.py` |
| M5 运行对账 | 对照输入、采信和隔离行 | `POST /api/stages/balance` | `app/modules/reconcile.py` | `tests/test_reconcile.py` |
| M6 批次复核 | 执行批次并签发或暂缓 | `POST /api/runs、PATCH /api/runs/<id>` | `app/review/service.py` | `tests/test_review.py` |
| M7 证据交付 | 下载复核清单 | `GET /api/runs/<id>/evidence` | `app/evidence/render.py` | `tests/test_evidence.py` |
| M8 合同归属 | 席位区间分摊与部门对账 | `POST /api/stages/allocate` | `app/allocation/contract.py` | `tests/test_allocation_domain.py`、`tests/test_allocation_pipeline.py`、`tests/test_allocation_http.py`、`tests/test_allocation_intake.py` |

## 输入陷阱

| 编号 | 规则 | 处理 | 测试 |
|---|---|---|---|
| TRAP-02 | 去除 BOM | `app/intake/reader.py` | `tests/test_intake.py::test_bom_preserves_identifier` |
| TRAP-03 | 按逻辑记录读取引号内换行 | `app/intake/reader.py` | `tests/test_intake.py::test_quoted_newline_is_one_logical_record` |
| TRAP-04 | 重复表头计入忽略行 | `app/intake/service.py` | `tests/test_intake.py::test_repeated_header_is_counted` |
| TRAP-05 | 异常列数隔离 | `app/intake/schema.py` | `tests/test_intake.py::test_extra_column_is_isolated` |
| TRAP-06 | 归一化全角数字和千分位 | `app/intake/numeric.py` | `tests/test_intake.py::test_full_width_and_grouping_are_canonical` |
| TRAP-07 | 空值行隔离 | `app/intake/numeric.py` | `tests/test_intake.py::test_sentinel_keeps_row_out_of_total` |
| TRAP-08 | 记录键保留前导零 | `app/intake/schema.py` | `tests/test_intake.py::test_bom_preserves_identifier` |
| TRAP-14 | 冲突版本都进入隔离 | `app/intake/resolve.py` | `tests/test_intake.py::test_duplicate_conflict_removes_both_copies` |
| TRAP-16 | 引号未闭合时拒收文件 | `app/intake/reader.py` | `tests/test_intake.py::test_unclosed_quote_invalidates_source` |
| TRAP-18 | 区分空文件、全空白和仅表头 | `app/intake/reader.py` | `tests/test_intake.py::test_empty_states_have_distinct_causes` |
| TRAP-26 | 拒绝旧版本复核 | `app/review/store.py` | `tests/test_review.py::test_review_optimistic_lock` |

## 领域反例

minute 为结算窗口起点后的分钟。月桥使用 [0, close) 半开区间，同一时刻按来源序列执行。新增和重新激活合计，收缩与流失作为减项。

逐组预期结论见 `tests/test_policy.py`，计算过程证据见 `tests/test_calculate.py`。

## 合同归属反例

| 情形 | 判定码 | 处理 |
|---|---|---|
| 一份合同出现多条 contract | `CONTRACT_NOT_SINGLE` | 列出全部合同记录并阻止签发 |
| 缺少 contract 或收入非正 | `CONTRACT_MISSING` / `CONTRACT_AMOUNT_ZERO` | 阻止签发 |
| 同一席位区间重叠 | `ASSIGN_OVERLAP` | 列出该席位全部参与记录并阻止签发 |
| 席位区间断档或未覆盖整窗 | `COVERAGE_GAP` | 列出断档相邻记录并阻止签发 |
| 归属区间超出合同窗口 | `WINDOW_BREACH` | 阻止签发 |
| 合同收入不能按席位整除 | `SEAT_RATE_INDIVISIBLE` | 阻止签发 |
| 席位无任何归属 | `SEAT_MISSING` | 阻止签发 |
| 部门承担金额之和不等于合同收入 | `ALLOCATION_MISMATCH` | 对账差非 0，阻止签发 |

分摊为整数分：先按分钟占比求各区间下限，再以最大余额法把余数逐分补给余额最大的区间（余额相同则区间更长、部门与记录键排序靠前者优先），保证重跑可复现且无金额丢失。逐分对账与重跑幂等见 `tests/test_allocation_pipeline.py`，并发重跑只落一批见 `tests/test_allocation_concurrency.py`。

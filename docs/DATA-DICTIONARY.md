# 字段与业务定义

输入编码 UTF-8，允许 BOM。首行必须匹配样例列顺序。记录键和业务组保留原始字符串。`kind` 允许 opening, change, close。说明列 `note` 可以跨行，限制 200 字。

业务字段按 `minute`、`mrr_cents`、`sequence` 排列。数字接受非负整数、全角数字和完整千分位。空串、短横线、N/A、NULL 与未知为缺值。无关字段用 0 占位。

minute 为结算窗口起点后的分钟。月桥使用 [0, close) 半开区间，同一时刻按来源序列执行。新增和重新激活合计，收缩与流失作为减项。

`incoming.csv` 包含四个业务组，第二组提供不同边界，第三组触发业务拒收，第四组需要核对。另含重复表头、冲突记录、重复回放与错误列数。`ready.csv` 含可以签发的两个组。

## 集团合同收入与部门归属来源

归属来源使用九列表头，在月桥七列后追加 `seat`、`department`，首行必须为：

`record,case,kind,minute,mrr_cents,sequence,note,seat,department`

`kind` 仅允许 `contract` 与 `assign`，与月桥类型互斥，按表头形状自动识别模式。

- `contract`：每个业务组（一份集团合同）恰好一条。`minute`、`sequence` 分别为结算窗口起点、终点（半开区间 `[start, end)`）；`mrr_cents` 为唯一合同收入（正整数分）；`seat`、`department` 留空。
- `assign`：一条记录表示某席位在某部门的归属区间。`minute`、`sequence` 为区间起止分钟，`seat` 为席位标识，`department` 为承担部门。同一席位的区间必须首尾相接、无重叠、无断档，恰好覆盖整个合同窗口。

合同收入按席位数整除得到席位金额；席位金额再按各归属区间的分钟占比分摊到部门，余数用最大余额法逐分补齐，因此各部门承担金额之和与合同收入逐分相等。月中转移时原部门与新部门按区间分钟数分担，任何一方都不独占整月。

样例 `contracts_ready.csv` 含两份可签发合同（含月中转移），`contracts_incoming.csv` 含重叠归属、断档、重复合同、席位缺归属、不可整除及字段缺测等拒收情形。

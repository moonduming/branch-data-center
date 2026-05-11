# performance 接口文档

## 基础说明

- 服务前缀：`/api/performance`
- 权限：登录用户
- 当前仅有 3 个接口：
  - `GET /api/performance/prop-statuses/`
  - `GET /api/performance/prop-statuses/claim-list/`
  - `GET /api/performance/prop-statuses/transfer-list/`
  - `POST /api/performance/prop-statuses/create_workflow/`
  - `GET /api/performance/org-options/`
- 不存在详情接口，也不存在用户下拉框接口
- 分页参数：`page` 默认 `1`，`page_size` 默认 `10`，最大 `100`

分页响应：

```json
{
  "message": "查询成功",
  "data": {
    "count": 1,
    "data": []
  }
}
```

失败响应：

```json
{
  "message": "错误信息",
  "errors": {}
}
```

## 1. 认领列表

- URL：`GET /api/performance/prop-statuses/claim-list/`
- 兼容入口：`GET /api/performance/prop-statuses/`
- 说明：以 `AcctSumD` 为主查询，再批量补充 `ShenzhenPropStatus`；会过滤掉最新状态为 `prop_status_flg=2` 的记录。

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- |----|
| key | string | 是 | 按 `ecif_cust_id=key OR orig_acct_id=key OR cust_name=key` 精确匹配查询 |
| org_id | string | 是 | 机构id， `OrgUnit.accnt_org_id` |
| prop_status_flg | string | 否 | 认领状态过滤：`0` 审核中，`1` 审核完成, `2` 失效|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| mng_org_id | string/null | 管理机构 |
| mng_org_name | string/null | 管理机构名称 |
| accnt_org_id | string/null | 机构编码 |
| accnt_org_name | string/null | 机构名称 |
| ecif_cust_id | string/null | 客户号 |
| orig_acct_id | string/null | 原始账号 |
| genr_acct_id | string/null | 通用账户号 |
| cust_name | string/null | 客户姓名 |
| year_daily_avg | decimal/null | 年日均，按 `bal_year_accum / (data_dt - 当年1月1日 + 1)` 计算，保留 2 位小数 |
| line_id_name | string/null | 条线名称，来自 `line_id.LINE_ID_NAME` |
| org_code | string/null | 条线机构编码，来自 `line_id.org_code` |
| mng_accnt_prod_name | string/null | 管会产品名称，来自 `mng_accnt_prod.MNG_ACCNT_PROD_NAME` |
| cust_type_cd | string/null | 客户类型 |
| biz_type_cd | string/null | 业务类型 |
| claim_status | string | 认领情况：`未认领` / `审核中` / `审核完成` |
| claim_time | datetime/null | 认领时间，取当前 `data_dt + genr_acct_id` 下最新申请记录的 `apl_data_dt` |
| prop_people_list | object[] | 当前 `genr_acct_id` 下全部占比明细，按“人 + 占比”返回 |

`prop_people_list` 字段：

| 字段 | 类型          | 说明 |
| --- |-------------|----|
| employee_no | string/null | 员工编号 |
| employee_name | string/null | 员工姓名 |
| kpi_prop | decimal/null | 业绩占比 |
| data_dt | string/null | 日期 |
| prop_status_flg | string/null | 认领状态过滤：`0` 审核中，`1` 审核完成, `2` 失效|

成功响应示例：

```json
{
  "message": "查询成功",
    "data": {
    "count": 1,
    "data": [
      {
        "mng_org_id": "44030101",
        "mng_org_name": "深圳民治支行",
        "accnt_org_id": "44030101",
        "accnt_org_name": "深圳民治支行",
        "ecif_cust_id": "PERQ001",
        "orig_acct_id": "PERF-ACCT-QRY-0001",
        "genr_acct_id": "GENR-PERF-QRY-0001",
        "cust_name": "深圳查询测试客户一",
        "year_daily_avg": 24806.2,
        "line_id_name": "公司银行条线",
        "org_code": "44030004",
        "mng_accnt_prod_name": "徽银e贷",
        "cust_type_cd": null,
        "biz_type_cd": "LN",
        "claim_status": "审核中",
        "claim_time": "2026-05-09T02:03:14Z",
        "prop_people_list": [
          {
            "employee_no": "perf_u01",
            "employee_name": "测试员工一",
            "kpi_prop": 1.0,
            "prop_status_flg": "审核中",
            "data_dt": "2026-05-09"
          }
        ]
      }
    ]
  }
}
```

## 2. 移交列表

- URL：`GET /api/performance/prop-statuses/transfer-list/`
- 说明：以 `ShenzhenPropStatus(prop_status_flg=1)` 为主查询，再批量补充 `AcctSumD/LineId/MngAccntProd/OrgUnit` 信息；当 `AcctSumD` 未命中时，仍会优先返回状态表中的基础字段与条线 `org_code`。

查询参数与返回字段同“认领列表”。

## 3. 发起业绩认领/移交流程

- URL：`POST /api/performance/prop-statuses/create_workflow/`
- 说明：`business_type`、`data_dt` 为流程共享字段；其余字段按 `items` 明细逐条处理并逐条写入占比表。

请求字段：

| 字段     | 类型  | 必填 | 说明   |
|--------|-----| --- |------|
| business_type | string | 是 | `performance_claim` 业绩认领，`performance_transfer` 业绩移交 |
| data_dt | date | 是 | 数据日期；不能大于当前日期。早于当前日期 30 天时自动调整为该月月末并查月历史表 |
| title  | string | 是 | 流程标题 |
| org_id | int | 是 | 核算机构ID |
| business_id | string/null | 否 | 流程业务 ID |
| items  | object[] | 是 | 明细列表，不能为空 |

`items` 明细字段：

| 字段 | 类型 | 必填 | 说明   |
| --- | --- | --- |------|
| user_id | int | 是 | 目标用户 ID；允许重复 |
| genr_acct_id | string | 是 | 通用账户号；`kpi_prop` 校验按该字段分组 |
| ecif_cust_id | string | 是 | ECIF 客户编号 |
| orig_acct_id | string | 是 | 原始账号 |
| accnt_org_id | string/null | 机构编码 |
| accnt_org_name | string/null | 机构名称 |
| cust_name | string | 是 | 客户名称；允许传空字符串 |
| org_code | string | 是 | 条线机构编码，来自 `line_id.org_code`；所有明细必须一致 |
| kpi_prop | decimal | 是 | 业绩占比；前端传百分数，可传整数或小数，后端会除以 `100` 后入库 |

业务规则：

- 工作流发起时，会从 `items` 中提取 `user_id`，按顺序去重后作为发起节点提交用户列表。
- `items` 中每一条明细都会单独写入一条 `ShenzhenPropStatus` 记录。
- `items` 中所有明细的 `org_code` 必须一致，否则报错；写入 `ShenzhenPropStatus.LINE_ORG_CODE`。
- `kpi_prop` 会除以 `100` 转换后入库。
- 按 `genr_acct_id` 分组后，每组所有明细的 `kpi_prop` 之和必须刚好等于 `100`，否则报错。
- `performance_claim`：任一明细命中同一 `data_dt + ecif_cust_id + orig_acct_id` 已存在占比记录时，不允许发起。
- `performance_transfer`：任一明细未命中同一 `data_dt + ecif_cust_id + orig_acct_id` 已存在占比记录时，不允许发起。
- `performance_transfer` 会按明细逐条补齐 `year_base_amount`：30 天内查日历史表，30 天前查月历史表。
- 写入占比表时，会按 `user_id` 补齐员工编号、员工姓名、认领机构编码、认领机构名称。
- 工作流实例创建后，系统会自动提交发起节点任务，再写入占比表明细。

请求示例：

```json
{
  "business_type": "performance_claim",
  "data_dt": "2026-04-29",
  "title": "4月业绩认领",
  "org_id": 1,
  "items": [
    {
      "user_id": 11,
      "accnt_org_id": "44030101",
      "accnt_org_name": "深圳民治支行",
      "genr_acct_id": "G001",
      "ecif_cust_id": "C001",
      "orig_acct_id": "A001",
      "cust_name": "客户一",
      "org_code": "44030004",
      "kpi_prop": "50.5"
    },
    {
      "user_id": 11,
      "accnt_org_id": "44030101",
      "accnt_org_name": "深圳民治支行",
      "genr_acct_id": "G001",
      "ecif_cust_id": "C002",
      "orig_acct_id": "A002",
      "cust_name": "客户二",
      "org_code": "44030004",
      "kpi_prop": "49.5"
    },
    {
      "user_id": 22,
      "accnt_org_id": "44030101",
      "accnt_org_name": "深圳民治支行",
      "genr_acct_id": "G002",
      "ecif_cust_id": "C003",
      "orig_acct_id": "A003",
      "cust_name": "客户三",
      "org_code": "44030004",
      "kpi_prop": "100"
    }
  ]
}
```

成功响应：

```json
{
  "message": "流程创建成功",
  "data": {
    "process_instance_id": 1,
    "process_def_id": 2,
    "business_type": "performance_claim",
    "data_dt": "2026-04-29",
    "created_count": 3
  }
}
```

## 17. 机构下拉接口

- URL：`POST /api/performance/org-options/`
- 仅返回支行机构数据

请求字段：

| 字段 | 类型   | 必填 | 说明 |
|----|------|----|----|
| org_types | list | 是  | 机构类型列表 |

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 机构 ID |
| org_name | string | 机构名称 |

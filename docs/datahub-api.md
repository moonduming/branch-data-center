# datahub 接口文档

## 基础说明

- 服务前缀：`/api/datahub`
- 指标定义、指标规则接口权限：管理员登录
- 看板、机构下拉、父指标下拉、指标下拉接口权限：登录即可访问
- 当前实现方式：`ModelViewSet + Router + APIView`

## 1. 指标定义列表

- URL：`GET /api/datahub/indicators/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| nested | int/bool | 否 | 默认 `1`，返回父指标及其子指标结构；传 `0/false` 返回普通分页列表 |
| status | string | 否 | 状态过滤 |
| category_code | string | 否 | 指标分类编码过滤 |
| parent_id | int | 否 | 按父指标 ID 过滤；传值时返回普通列表 |
| indicator_code | string | 否 | 指标编码模糊查询 |
| indicator_name | string | 否 | 指标名称模糊查询 |
| page | int | 否 | 页码，普通分页列表时生效 |
| page_size | int | 否 | 每页条数，普通分页列表时生效 |

参数取值说明：

- `nested`：支持 `1`、`true`、`yes`、`y` 表示返回父子结构；支持 `0`、`false`、`no`、`n` 表示返回普通分页列表
- `status`：按实际状态码精确匹配，常用值 `01`、`05`
- `category_code`：按指标分类编码精确匹配，当前常见值如 `440`、`380`、`480`
- `parent_id`：传指标主键 ID，仅返回该父指标下的直属子指标列表
- `indicator_code`：模糊查询
- `indicator_name`：模糊查询

默认返回结构说明：

- 返回所有父指标
- 每个父指标下挂 `children` 数组
- 当前指标体系只有两层

指标对象字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 ID |
| indicator_code | string | 指标编码 |
| indicator_name | string | 指标名称 |
| parent_id | int/null | 父指标 ID |
| assessment_indicator_id | string/null | 业绩考核指标 ID |
| category_code | string/null | 指标分类编码 |
| category_name | string/null | 指标分类名称 |
| line_code | string/null | 条线编码 |
| indicator_standard | string | 指标标准 |
| display_unit | string/null | 显示单位 |
| decimal_places | int | 小数位数 |
| display_type | string | 默认展示类型 |
| display_scope | string | 展示范围 |
| show_in_card | bool | 是否展示在顶部卡片 |
| show_in_trend | bool | 是否展示在趋势图下拉 |
| show_in_rank | bool | 是否展示在排名下拉 |
| sort_no | int | 排序 |
| status | string | 状态 |
| description | string/null | 指标描述 |
| remark | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 2. 创建指标定义

- URL：`POST /api/datahub/indicators/`

请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| indicator_code | string | 是 | 指标编码 |
| indicator_name | string | 是 | 指标名称 |
| parent_id | int/null | 否 | 父指标 ID；为空表示父指标 |
| assessment_indicator_id | string/null | 否 | 业绩考核指标 ID |
| category_code | string/null | 否 | 指标分类编码 |
| category_name | string/null | 否 | 指标分类名称 |
| line_code | string/null | 否 | 条线编码 |
| indicator_standard | string | 否 | 指标标准 |
| display_unit | string/null | 否 | 显示单位 |
| decimal_places | int | 否 | 小数位数 |
| display_type | string | 否 | 默认展示类型 |
| display_scope | string | 否 | 展示范围 |
| show_in_card | bool | 否 | 是否展示在顶部卡片 |
| show_in_trend | bool | 否 | 是否展示在趋势图下拉 |
| show_in_rank | bool | 否 | 是否展示在排名下拉 |
| sort_no | int | 否 | 排序 |
| status | string | 否 | 状态 |
| description | string/null | 否 | 指标描述 |
| remark | string/null | 否 | 备注 |

说明：

- 当前最多支持两级指标
- 前端多传字段会被忽略
- 可空字段允许传 `""` 或 `null`

## 3. 查询指标定义详情

- URL：`GET /api/datahub/indicators/{id}/`

说明：

- 仅返回当前指标本身，不额外拼接父子结构

## 4. 修改指标定义

- URL：`PUT /api/datahub/indicators/{id}/`

更新请求字段与创建接口一致，均为可选。

## 5. 删除指标定义

- URL：`DELETE /api/datahub/indicators/{id}/`

说明：

- 若当前指标下仍有子指标，不允许删除
- 若当前指标已被指标规则引用，不允许删除

## 6. 指标规则列表

- URL：`GET /api/datahub/indicator-rules/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| indicator_id | int | 否 | 指标 ID |
| status | string | 否 | 状态过滤 |
| indicator_code | string | 否 | 指标编码 |
| indicator_name | string | 否 | 指标名称 |
| is_current | int/bool | 否 | 是否当前生效版本 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

参数取值说明：

- `indicator_id`：传指标主键 ID，精确匹配
- `status`：按实际状态码精确匹配，常用值 `01`、`05`
- `is_current`：支持 `1`、`true`、`yes`、`y` 表示当前版本；支持 `0`、`false`、`no`、`n` 表示非当前版本

规则对象字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 ID |
| indicator_id | int | 指标 ID |
| indicator_code | string | 指标编码 |
| indicator_name | string | 指标名称 |
| rule_version | int | 规则版本号 |
| is_current | bool | 是否当前生效版本 |
| rule_name | string/null | 规则名称 |
| sql_template | string | 指标计算 SQL 模板 |
| target_sql_template | string/null | 目标值 SQL 模板 |
| calc_mode | string | 计算模式 |
| result_fields | string | SQL 输出字段定义 |
| org_prefix | string/null | 机构编码前缀 |
| need_org_filter | bool | 是否需要按机构过滤 |
| need_date_param | bool | 是否需要日期参数 |
| need_day_count_param | bool | 是否需要天数参数 |
| run_mode | string | 执行模式 |
| data_source_desc | string/null | 数据来源说明 |
| display_value_field | string | 默认展示值字段 |
| compare_value_field | string/null | 辅助比较字段 |
| status | string | 状态 |
| remark | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 7. 创建指标规则

- URL：`POST /api/datahub/indicator-rules/`

请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| indicator_id | int | 是 | 指标 ID |
| rule_version | int | 否 | 规则版本号，默认 1 |
| is_current | bool | 否 | 是否当前生效版本 |
| rule_name | string/null | 否 | 规则名称 |
| sql_template | string | 是 | 指标计算 SQL 模板 |
| target_sql_template | string/null | 否 | 目标值 SQL 模板 |
| calc_mode | string | 否 | 计算模式 |
| result_fields | string | 否 | 输出字段定义 |
| org_prefix | string/null | 否 | 机构编码前缀 |
| need_org_filter | bool | 否 | 是否按机构过滤 |
| need_date_param | bool | 否 | 是否需要日期参数 |
| need_day_count_param | bool | 否 | 是否需要天数参数 |
| run_mode | string | 否 | 执行模式 |
| data_source_desc | string/null | 否 | 数据来源说明 |
| display_value_field | string | 否 | 默认展示值字段 |
| compare_value_field | string/null | 否 | 辅助比较字段 |
| status | string | 否 | 状态 |
| remark | string/null | 否 | 备注 |

说明：

- 同一指标下规则版本号不能重复
- 当 `is_current=true` 时，会自动把同指标其它规则设为非当前版本

## 8. 查询指标规则详情

- URL：`GET /api/datahub/indicator-rules/{id}/`

## 9. 修改指标规则

- URL：`PUT /api/datahub/indicator-rules/{id}/`

更新请求字段与创建接口一致，均为可选。

## 10. 删除指标规则

- URL：`DELETE /api/datahub/indicator-rules/{id}/`

## 11. 指标看板

- URL：`GET /api/datahub/dashboard/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| data_dt | date | 是 | 指定日期，格式 `YYYY-MM-DD` |
| parent_indicator_id | int | 是 | 父指标 ID |
| org_id | string | 否 | 机构 ID；为空时不按机构过滤 |

参数取值说明：

- `data_dt`：必须是 `YYYY-MM-DD` 格式，例如 `2026-03-20`
- `parent_indicator_id`：必须传父指标主键 ID；可通过父指标下拉接口获取
- `org_id`：可为空；有值时传机构下拉接口返回的 `id`

返回规则说明：

- 只查询指定父指标下的直属叶子指标
- 顶层返回结构为：`{ "message": "查询成功", "data": [...] }`
- `data` 是数组，数组顺序与该父指标下叶子指标的排序一致
- `day_avg` 对应结果表 `metric_value`
- `point_in_time` 对应结果表 `metric_value_2`
- 当前代码返回：
  - day_avg_dod（日均日环比）
  - day_avg_dod_direction（日均环比方向标识）
  - point_in_time_dod（时点日环比）
  - point_in_time_dod_direction（时点环比方向标识）
  - completion_rate（完成率）
  - completion_rate_ratio（完成率日环比）
  - completion_rate_direction（完成率环比方向标识）
- 所有日环比单位均为百分比值，保留 1 位小数，四舍五入
- `org_values` 仅在 `org_id` 为空时返回各机构当日快照；传了 `org_id` 时通常为空数组
- `day_avg_series`、`point_in_time_series` 为近 30 天序列，包含当前日期
- 若某个维度完全无值，则对应序列返回空列表
- 当传入 `org_id` 时，会先根据机构表查出机构编码，再结合规则表 `org_prefix` 拼接结果表中的 `org_id` 进行过滤

看板返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| data | array | 看板项列表 |

叶子指标看板对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| indicator_name | string | 指标名称 |
| day_avg | number/null | 当日日均 |
| day_avg_dod | number/null | 日均日环比 |
| day_avg_dod_direction | string/null | 日均环比方向标识：up 表示增长，down 表示下降，flat 表示持平，null 表示无法计算 |
| point_in_time | number/null | 当日时点 |
| point_in_time_dod | number/null | 时点日环比 |
| point_in_time_dod_direction | string/null | 时点环比方向标识：up 表示增长，down 表示下降，flat 表示持平，null 表示无法计算 |
| completion_rate | number/null | 完成率 |
| completion_rate_ratio | number/null | 完成率日环比 |
| completion_rate_direction | string/null | 完成率环比方向标识：up 表示增长，down 表示下降，flat 表示持平，null 表示无法计算 |
| org_values | array | 各机构当日值列表 |
| day_avg_series | array | 近 30 天日均序列 |
| point_in_time_series | array | 近 30 天时点序列 |

`org_values` 对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| day_avg_org_values | array | 按日均值降序排序的机构列表 |
| point_in_time_org_values | array | 按时点值降序排序的机构列表 |

`day_avg_org_values` / `point_in_time_org_values` 内部对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| org_id | string | 结果表中的机构 ID |
| org_name | string/null | 机构名称 |
| day_avg | number/null | 该机构当日日均（仅在 day_avg_org_values 中存在） |
| point_in_time | number/null | 该机构当日時点（仅在 point_in_time_org_values 中存在） |

序列对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| data_dt | date | 日期 |
| value | number/null | 当天对应值 |

## 12. 个人业绩看板

- URL：`GET /api/datahub/dashboard/personal/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| data_dt | date | 是 | 指定日期，格式 `YYYY-MM-DD` |
| parent_indicator_id | int | 是 | 父指标 ID |
| employee_no | string | 是 | 人员编号 |
| org_id | string | 否 | 机构 ID；为空时不按机构过滤 |

参数取值说明：

- `data_dt`：必须是 `YYYY-MM-DD` 格式，例如 `2026-05-13`
- `parent_indicator_id`：必须传父指标主键 ID；可通过父指标下拉接口获取
- `employee_no`：必须传员工编号，例如 `HS0000832`
- `org_id`：可为空；有值时传机构下拉接口返回的 `id`

返回规则说明：

- 只查询指定父指标下的直属叶子指标
- 顶层返回结构为：`{ "message": "查询成功", "data": [...] }`
- `data` 是数组，数组顺序与该父指标下叶子指标的排序一致
- 数据来源为 `perf_indicator_result_post_profit`
- 除原看板按机构过滤逻辑外，额外按 `employee_no` 过滤分润结果表
- `day_avg` 对应结果表 `metric_value`
- `point_in_time` 对应结果表 `metric_value_2`
- 当前代码返回：
  - day_avg_dod（日均日环比）
  - day_avg_dod_direction（日均环比方向标识）
  - point_in_time_dod（时点日环比）
  - point_in_time_dod_direction（时点环比方向标识）
  - completion_rate（完成率）
  - completion_rate_ratio（完成率日环比）
  - completion_rate_direction（完成率环比方向标识）
- 所有日环比单位均为百分比值，保留 1 位小数，四舍五入
- 个人业绩看板不返回 `org_values`、`day_avg_series`、`point_in_time_series`
- 当传入 `org_id` 时，会先根据机构表查出机构编码，再结合分润规则表 `org_prefix` 拼接结果表中的 `org_id` 进行过滤；若未配置分润规则，则按机构编码本身过滤

个人看板返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| data | array | 看板项列表 |

叶子指标看板对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| indicator_name | string | 指标名称 |
| day_avg | number/null | 当日日均 |
| day_avg_dod | number/null | 日均日环比 |
| day_avg_dod_direction | string/null | 日均环比方向标识：up 表示增长，down 表示下降，flat 表示持平，null 表示无法计算 |
| point_in_time | number/null | 当日时点 |
| point_in_time_dod | number/null | 时点日环比 |
| point_in_time_dod_direction | string/null | 时点环比方向标识：up 表示增长，down 表示下降，flat 表示持平，null 表示无法计算 |
| completion_rate | number/null | 完成率 |
| completion_rate_ratio | number/null | 完成率日环比 |
| completion_rate_direction | string/null | 完成率环比方向标识：up 表示增长，down 表示下降，flat 表示持平，null 表示无法计算 |

## 13. 个人业绩看板占比明细

- URL：`GET /api/datahub/dashboard/personal/prop-statuses/`

查询参数：

| 字段  | 类型 | 必填 | 说明  |
|-----| --- | --- |-----|
| employee_no | string | 是 | 员工编号 |
| key | string | 是 | 客户姓名/客户编号/账号 |

返回规则说明：

- 顶层返回结构为：`{ "message": "查询成功", "data": [...] }`
- 使用原生 SQL 联查 `i01_sz_acct_sum_d`、`shenzhen_prop_status`、`mng_accnt_prod`、`line_id`
- 查询条件：
  - `a.GENR_ACCT_ID = d.GENR_ACCT_ID`
  - `a.MNG_ACCNT_PROD_ID = b.MNG_ACCNT_PROD_ID`
  - `a.LINE_ID = c.LINE_ID`
  - `c.org_code <> '44030005'`
  - `d.employee_no = <参数值>`
- 返回结果按 `line_id_name`、`ecif_cust_id`、`orig_acct_id` 排序

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| accnt_org_id | string | 核算机构编号 |
| ecif_cust_id | string | ECIF 客户编号 |
| orig_acct_id | string | 原始账号 |
| genr_acct_id | string | 通用账户号 |
| cust_name | string | 客户名称 |
| line_id_name | string | 条线名称 |
| mng_accnt_prod_name | string | 管理会计产品名称 |
| month_daily_avg | string | 月日均，SQL 中经 `FORMAT(..., 2)` 格式化后的字符串 |
| year_daily_avg | string | 年日均，SQL 中经 `FORMAT(..., 2)` 格式化后的字符串 |
| kpi_prop | decimal/null | 业绩占比 |
| apl_data_dt | datetime/null | 申请时间 |
| org_code | string | 条线机构编码 |

## 14. 导入日志查询接口

- URL：`GET /api/datahub/imports/logs/`
- 权限：管理员

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| data_dt | date | 否 | 查询的数据日期，格式 `YYYY-MM-DD`；不传时按默认导入日期规则取值 |

返回说明：

- 返回指定日期的总行文件导入日志，以及结果表导入依赖检查摘要
- `file_logs` 中每个文件都会返回当前运行次数 `run_count`
- 当文件运行次数已达到 3 次时，后续总行导入任务会跳过该文件，不再重试

导入日志接口返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| data_dt | date | 本次查询对应的数据日期 |
| summary | object | 结果表导入摘要信息 |
| file_logs | array[object] | 总行文件导入日志列表 |

`summary` 对象字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| result_import_log | [object/null] | 结果表导入日志 |
| post_profit_indicator_logs | array[object] | 分润后结果表指标导入日志 |
| dependency_ready | bool | 结果表依赖是否齐备 |
| dependency_tables | array[string] | 已配置依赖表列表 |
| missing_dependency_tables | array[string] | 当前缺失的依赖表列表 |

`result_import_log` 内部对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 日志主键 |
| data_date | date | 数据日期 |
| status | int | 状态码，`0` 待处理、`1` 成功、`2` 失败、`3` 执行中 |
| status_label | string | 状态中文名称 |
| message | string/null | 状态说明 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

`post_profit_indicator_logs` 内部对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 日志主键 |
| data_date | date | 任务日期 |
| indicator_id | int | 指标 ID |
| rule_id | int/null | 规则 ID |
| status | int | 状态码，`0` 待处理、`1` 成功、`2` 失败、`3` 执行中 |
| status_label | string | 状态中文名称 |
| message | string/null | 状态说明 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

`file_logs` 内部对象字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 日志主键 |
| file_name | string | 文件名 |
| data_date | date | 数据日期 |
| run_count | int | 实际执行次数 |
| status | int | 状态码 |
| status_label | string | 状态中文名称 |
| message | string/null | 状态说明 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 15. 手动触发总行数据导入

- URL：`POST /api/datahub/imports/head-office/trigger/`
- 权限：管理员

请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| data_dt | date | 否 | 指定导入日期，格式 `YYYY-MM-DD`；不传时按默认导入日期规则取值 |

返回示例：

```json
{
  "message": "总行下发数据导入任务已提交",
  "data": {
    "task_id": "xxxxxx",
    "data_dt": "2026-03-24"
  }
}
```

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| task_id | string | 异步任务 ID |
| data_dt | date | 本次触发的导入日期 |

补充说明：

- 任务会扫描 `AUTO_LOAD_DATA_BASE_DIR/{YYYYMMDD}` 下的 `.ok` 文件
- 已成功导入的文件不会重复执行
- 单个文件最多执行 3 次；达到上限后自动跳过

## 16. 手动触发结果表数据导入

- URL：`POST /api/datahub/imports/result/trigger/`
- 权限：管理员

请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| data_dt | date | 否 | 指定导入日期，格式 `YYYY-MM-DD`；不传时按默认导入日期规则取值 |
| force | bool | 否 | 是否强制执行，支持 `true/false` |

返回示例：

```json
{
  "message": "结果表导入任务已提交",
  "data": {
    "task_id": "xxxxxx",
    "data_dt": "2026-03-24",
    "force": false
  }
}
```

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| task_id | string | 异步任务 ID |
| data_dt | date | 本次触发的导入日期 |
| force | bool | 是否强制执行 |

补充说明：

- 未开启 `force` 时，会先检查依赖表是否都已成功导入
- 同一数据日期结果表已成功导入时，默认跳过重复执行

## 17. 手动触发分润后结果表数据导入

- URL：`POST /api/datahub/imports/result/post-profit/trigger/`
- 权限：管理员

请求字段说明：购买会员只支持银行卡支付？后续会增加新的这份方式吗

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| data_dt | date | 否 | 指定任务日期，格式 `YYYY-MM-DD`；不传时按默认导入日期规则取值 |
| force | bool | 否 | 是否强制执行，支持 `true/false` |

返回示例：

```json
{
  "message": "分润后结果表导入任务已提交",
  "data": {
    "task_id": "xxxxxx",
    "data_dt": "2026-03-24",
    "force": false
  }
}
```

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| task_id | string | 异步任务 ID |
| data_dt | date | 本次触发的任务日期 |
| force | bool | 是否强制执行 |

补充说明：

- 任务会按传入日期向前回算 30 天数据，包含当前日期。
- 单个指标的 30 天数据作为一个整体执行；中途任意一天失败，该指标整批失败，下次会从该指标的 30 天窗口重新计算。
- 指标之间互不影响；某个指标失败不会阻塞其他指标继续入库。
- 同一任务日期下，已成功的指标不会重复执行，除非显式传入 `force=true`。
- 任务执行时间较长时，会在指标批次开始和日切换时主动回收旧连接；若遇到数据库连接中断，会自动重试一次整指标批次。

## 18. 手动触发备份任务

- URL：`POST /api/datahub/imports/backup/trigger/`
- 权限：管理员

请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| data_dt | date | 否 | 手动指定需要备份的业务日期，格式 `YYYY-MM-DD` |

请求示例：

```json
{
  "data_dt": "2026-03-26"
}
```

返回示例：

```json
{
  "message": "数据备份任务已提交",
  "data": {
    "task_id": "xxxxxx",
    "data_dt": "2026-03-26"
  }
}
```

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| task_id | string | 异步任务 ID |
| data_dt | date | 本次触发的备份业务日期 |

## 19. 机构下拉接口

- URL：`GET /api/datahub/org-options/`

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 机构 ID |
| org_name | string | 机构名称 |

## 20. 父指标下拉接口

- URL：`GET /api/datahub/parent-indicator-options/`

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 父指标 ID |
| indicator_name | string | 父指标名称 |

## 21. 指标下拉接口

- URL：`GET /api/datahub/indicator-options/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| indicator_name | string | 否 | 按指标名称模糊查询 |

说明：

- 不传 `indicator_name` 时，返回全部启用中的指标选项

返回字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 指标 ID |
| indicator_name | string | 指标名称 |

# workflow 接口文档

## 基础说明

- 服务前缀：`/api/workflow`
- 定义态接口权限：管理员
- 运行态接口权限：登录即可
- 分页参数：`page` 默认 `1`，`page_size` 默认 `10`，最大 `100`

成功响应：

```json
{
  "message": "查询成功",
  "data": {}
}
```

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

## 1. 流程定义

### 1.1 获取流程定义列表

- URL：`GET /api/workflow/process-defs/`
- 权限：管理员

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_code | string | 否 | 流程编码，模糊查询 |
| process_name | string | 否 | 流程名称，模糊查询 |
| business_type | string | 否 | `report_submit` / `performance_claim` / `performance_transfer` |
| status | string | 否 | `draft` / `active` / `inactive` |
| is_latest | bool | 否 | 是否最新版本 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| process_code | string | 流程编码 |
| process_name | string | 流程名称 |
| business_type | string | 业务类型 |
| version | int | 版本号 |
| status | string | 状态编码 |
| status_label | string | 状态名称 |
| is_latest | bool | 是否最新版本 |
| remark | string/null | 备注 |
| node_count | int | 节点数量 |
| assignee_rule_count | int | 节点审核规则数量 |
| transition_count | int | 流转数量 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 1.2 获取流程定义详情

- URL：`GET /api/workflow/process-defs/{id}/`
- 权限：管理员
- 返回字段：同 1.1

### 1.3 创建流程定义

- URL：`POST /api/workflow/process-defs/`
- 权限：管理员

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_code | string | 是 | 流程编码 |
| process_name | string | 是 | 流程名称 |
| business_type | string | 是 | `report_submit` / `performance_claim` / `performance_transfer` |
| version | int | 否 | 不传时自动取同 `process_code` 下最大版本号 + 1 |
| status | string | 是 | `draft` / `active` / `inactive` |
| is_latest | bool | 否 | 是否最新版本 |
| remark | string/null | 否 | 备注 |

说明：

- 同一 `process_code` 下 `version` 不能重复
- 当 `is_latest=true` 时，同 `process_code` 下其他版本会自动更新为 `false`

### 1.4 复制流程定义

- URL：`POST /api/workflow/process-defs/{id}/copy/`
- 权限：管理员
- 请求体：无

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| process_def | object | 新流程定义，字段同 1.1 |
| copied_counts.node_count | int | 复制的节点数量 |
| copied_counts.assignee_rule_count | int | 复制的节点审核规则数量 |
| copied_counts.transition_count | int | 复制的流转数量 |
| source_process_def_id | int | 源流程定义 ID |

说明：

- 新流程版本号自动取同 `process_code` 下最大版本号 + 1
- 会同步复制源流程下全部节点、节点审核规则、流转
- 新流程固定保存为 `is_latest=true`

### 1.5 更新流程定义

- URL：`PUT /api/workflow/process-defs/{id}/`
- URL：`PATCH /api/workflow/process-defs/{id}/`
- 权限：管理员

请求字段：同 1.3，更新时均为可选。

限制：

- 当前流程已创建实例时不允许修改

### 1.6 删除流程定义

- URL：`DELETE /api/workflow/process-defs/{id}/`
- 权限：管理员

限制：

- 当前流程下仍有关联节点、节点审核规则、流转时不允许删除
- 当前流程已创建实例时不允许删除

### 1.7 流程定义筛选项

- URL：`GET /api/workflow/process-def-options/`
- 权限：管理员

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| status_options | array | 状态下拉 |
| is_latest_options | array | 是否最新版本下拉 |
| business_type_options | array | 业务类型下拉 |

## 2. 节点定义

### 2.1 获取节点列表

- URL：`GET /api/workflow/node-defs/`
- 权限：管理员

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_def_id | int | 是 | 流程定义 ID |
| node_code | string | 否 | 节点编码，模糊查询 |
| node_name | string | 否 | 节点名称，模糊查询 |
| node_type | string | 否 | 节点类型 |
| join_strategy | string | 否 | 汇聚策略 |
| is_parallel | bool | 否 | 是否并行节点 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| process_def_id | int | 流程定义 ID |
| node_code | string | 节点编码 |
| node_name | string | 节点名称 |
| node_type | string | 节点类型 |
| node_type_label | string | 节点类型名称 |
| node_order | int/null | 节点顺序 |
| is_parallel | bool | 是否并行 |
| parallel_mode | string/null | 并行模式 |
| join_strategy | string/null | 汇聚策略 |
| join_strategy_label | string/null | 汇聚策略名称 |
| can_reject | bool | 是否允许驳回 |
| can_return | bool | 是否允许退回 |
| auto_create_task | bool | 是否自动创建任务 |
| remark | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 2.2 获取节点详情

- URL：`GET /api/workflow/node-defs/{id}/`
- 权限：管理员
- 返回字段：同 2.1

### 2.3 创建节点

- URL：`POST /api/workflow/node-defs/`
- 权限：管理员

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_def_id | int | 是 | 流程定义 ID |
| node_code | string | 是 | 节点编码 |
| node_name | string | 是 | 节点名称 |
| node_type | string | 是 | `start` / `manual` / `auto` / `end` |
| node_order | int/null | 否 | 节点顺序 |
| is_parallel | bool | 否 | 是否并行节点 |
| parallel_mode | string/null | 否 | 并行模式 |
| join_strategy | string/null | 否 | `all_pass` / `any_pass` |
| can_reject | bool | 否 | 是否允许驳回 |
| can_return | bool | 否 | 是否允许退回 |
| auto_create_task | bool | 否 | 是否自动创建任务 |
| remark | string/null | 否 | 备注 |

说明：

- 同一流程下 `node_code` 不能重复

### 2.4 更新节点

- URL：`PUT /api/workflow/node-defs/{id}/`
- URL：`PATCH /api/workflow/node-defs/{id}/`
- 权限：管理员

请求字段：同 2.3，更新时均为可选。

限制：

- 当前流程已创建实例时不允许修改
- 若修改 `node_code`，系统会同步更新关联的节点审核规则和流转引用
- 若节点已被节点审核规则或流转引用，不允许修改 `process_def_id`

### 2.5 删除节点

- URL：`DELETE /api/workflow/node-defs/{id}/`
- 权限：管理员

限制：

- 当前节点仍被节点审核规则引用时不允许删除
- 当前节点仍被流转引用时不允许删除
- 当前流程已创建实例时不允许删除

### 2.6 节点辅助选项

- URL：`GET /api/workflow/node-def-options/`
- 权限：管理员

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| node_type_options | array | 节点类型下拉 |
| join_strategy_options | array | 汇聚策略下拉 |

## 3. 流转定义

### 3.1 获取流转列表

- URL：`GET /api/workflow/transition-defs/`
- 权限：管理员

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_def_id | int | 是 | 流程定义 ID |
| from_node_code | string | 否 | 来源节点编码 |
| to_node_code | string | 否 | 目标节点编码 |
| action_code | string | 否 | 动作编码 |
| condition_type | string | 否 | 条件类型 |
| is_enabled | bool | 否 | 是否启用 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| process_def_id | int | 流程定义 ID |
| from_node_code | string | 来源节点编码 |
| from_node_name | string/null | 来源节点名称 |
| to_node_code | string | 目标节点编码 |
| to_node_name | string/null | 目标节点名称 |
| action_code | string | 动作编码 |
| action_code_label | string | 动作名称 |
| condition_type | string/null | 条件类型 |
| condition_type_label | string/null | 条件类型名称 |
| condition_expr | string/null | 条件表达式 |
| priority | int | 优先级，值越小优先级越高 |
| is_enabled | bool | 是否启用 |
| remark | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.2 获取流转详情

- URL：`GET /api/workflow/transition-defs/{id}/`
- 权限：管理员
- 返回字段：同 3.1

### 3.3 创建流转

- URL：`POST /api/workflow/transition-defs/`
- 权限：管理员

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_def_id | int | 是 | 流程定义 ID |
| from_node_code | string | 是 | 来源节点编码 |
| to_node_code | string | 是 | 目标节点编码 |
| action_code | string | 是 | `submit` / `approve` / `reject` / `return` / `auto` / `complete` / `cancel` |
| condition_type | string/null | 否 | `none` / `script` |
| condition_expr | string/null | 否 | 条件表达式 |
| priority | int | 否 | 优先级，值越小优先级越高 |
| is_enabled | bool | 否 | 是否启用 |
| remark | string/null | 否 | 备注 |

说明：

- `from_node_code`、`to_node_code` 必须属于当前流程下已存在节点
- 当前运行态只支持无条件流转，`condition_type=script` 虽可配置，但执行时不支持

### 3.4 更新流转

- URL：`PUT /api/workflow/transition-defs/{id}/`
- URL：`PATCH /api/workflow/transition-defs/{id}/`
- 权限：管理员

请求字段：同 3.3，更新时均为可选。

限制：

- 当前流程已创建实例时不允许修改

### 3.5 删除流转

- URL：`DELETE /api/workflow/transition-defs/{id}/`
- 权限：管理员

限制：

- 当前流程已创建实例时不允许删除

### 3.6 流转辅助选项

- URL：`GET /api/workflow/transition-def-options/`
- 权限：管理员

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| action_code_options | array | 动作编码下拉 |
| condition_type_options | array | 条件类型下拉 |

### 3.7 获取节点可用流转操作

- URL：`GET /api/workflow/node-available-actions/`
- 权限：登录
- 说明：根据流程定义 ID 和当前节点编码，查询该节点当前可执行的流转操作列表。

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_def_id | int | 是 | 流程定义 ID |
| node_code | string | 是 | 节点编码 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| action_code | string | 动作编码 |
| action_name | string | 动作名称 |

成功响应示例：

```json
{
  "message": "查询成功",
  "data": [
    {
      "action_code": "approve",
      "action_name": "同意"
    },
    {
      "action_code": "reject",
      "action_name": "驳回"
    }
  ]
}
```

## 4. 节点审核规则

### 4.1 获取节点审核规则列表

- URL：`GET /api/workflow/node-assignee-rules/`
- 权限：管理员

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_def_id | int | 是 | 流程定义 ID |
| node_code | string | 否 | 节点编码 |
| rule_type | string | 否 | `applicant` / `employee_level` / `fixed_user` |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 |
| process_def_id | int | 流程定义 ID |
| node_code | string | 节点编码 |
| node_name | string/null | 节点名称 |
| rule_type | string | 规则类型 |
| rule_type_label | string | 规则类型名称 |
| rule_value | string/null | 规则值 |
| remark | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 4.2 获取节点审核规则详情

- URL：`GET /api/workflow/node-assignee-rules/{id}/`
- 权限：管理员
- 返回字段：同 4.1

### 4.3 创建节点审核规则

- URL：`POST /api/workflow/node-assignee-rules/`
- 权限：管理员

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| process_def_id | int | 是 | 流程定义 ID |
| node_code | string | 是 | 节点编码 |
| rule_type | string | 是 | `applicant` / `employee_level` / `fixed_user` |
| rule_value | string/null | 否 | 规则值 |
| remark | string/null | 否 | 备注 |

说明：

- `node_code` 必须属于当前流程下已存在节点
- 同一流程下每个节点只能配置一条审核规则

### 4.4 更新节点审核规则

- URL：`PUT /api/workflow/node-assignee-rules/{id}/`
- URL：`PATCH /api/workflow/node-assignee-rules/{id}/`
- 权限：管理员

请求字段：同 4.3，更新时均为可选。

限制：

- `node_code` 必须属于当前流程下已存在节点
- 当前流程已创建实例时不允许修改

### 4.5 删除节点审核规则

- URL：`DELETE /api/workflow/node-assignee-rules/{id}/`
- 权限：管理员

限制：

- 当前流程已创建实例时不允许删除

### 4.6 节点审核规则辅助选项

- URL：`GET /api/workflow/node-assignee-rule-options/`
- 权限：管理员

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| rule_type_options | array | 规则类型下拉 |

## 5. 流程实例

### 5.1 获取流程实例列表

- URL：`GET /api/workflow/instances/`
- 权限：登录

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| title | string | 否 | 实例标题，模糊查询 |
| status | string | 否 | `running` / `finished` / `rejected` / `cancelled` |
| business_type | string | 否 | `report_submit` / `performance_claim` / `performance_transfer` |
| applicant_id | int | 否 | 发起人 ID |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 实例 ID |
| title | string/null | 实例标题 |
| process_def_id | int | 流程定义 ID |
| process_name | string/null | 流程名称 |
| business_type | string | 业务类型 |
| business_id | int/null | 业务 ID |
| applicant_id | int | 发起人 ID |
| applicant_name | string/null | 发起人姓名 |
| current_node_code | string/null | 当前节点编码 |
| current_node_name | string/null | 当前节点名称 |
| status | string | 实例状态 |
| status_label | string | 实例状态名称 |
| task_count | int | 任务总数 |
| active_task_count | int | 待处理或处理中的任务数 |
| start_time | datetime | 开始时间 |
| end_time | datetime/null | 结束时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

说明：

- 非管理员只能查看自己发起或自己参与过处理的实例

### 5.2 获取流程实例详情

- URL：`GET /api/workflow/instances/{id}/`
- 权限：登录
- 返回字段：同 5.1

### 5.3 撤回流程实例

- URL：`POST /api/workflow/instances/{id}/recall/`
- 权限：登录
- 请求体：无

返回字段：

- 返回撤回后的实例详情，字段同 5.1

限制：

- 只有发起人本人可以撤回
- 仅当流程仍停留在开始节点后的首个人工审核节点，且该节点未处理完成时可撤回

## 6. 任务

### 6.1 获取任务列表

- URL：`GET /api/workflow/tasks/`
- 权限：登录

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| instance_id | int | 否 | 实例 ID |
| status | string | 否 | 任务状态 |
| assignee_id | int | 否 | 处理人 ID |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 任务 ID |
| instance_id | int | 实例 ID |
| instance_title | string/null | 实例标题 |
| process_def_id | int/null | 流程定义 ID |
| node_code | string | 节点编码 |
| node_name | string | 节点名称 |
| assignee_id | int/null | 处理人 ID |
| assignee_name | string/null | 处理人姓名 |
| branch_key | string/null | 分支标识 |
| branch_org_id | int/null | 分支机构 ID |
| branch_org_name | string/null | 分支机构名称 |
| parallel_group | string/null | 并行组标识 |
| status | string | 任务状态 |
| status_label | string | 任务状态名称 |
| result | string/null | 处理结果 |
| result_label | string/null | 处理结果名称 |
| round_no | int | 审批轮次 |
| completed_at | datetime/null | 完成时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

说明：

- 非管理员只能查看分配给自己，或自己发起实例下的任务

### 6.2 获取任务详情

- URL：`GET /api/workflow/tasks/{id}/`
- 权限：登录
- 返回字段：同 6.1

### 6.3 处理任务

- URL：`POST /api/workflow/tasks/{id}/action/`
- 权限：登录

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| action_code | string | 是 | `submit` / `approve` / `reject` / `return` / `complete` |
| comment | string/null | 否 | 处理意见 |
| selected_user_ids | array[int] | 否 | 发起节点执行 `submit` 时选择的用户 ID 列表 |
| target_branch_key | string/null | 否 | 并行汇总节点执行 `return` 时指定退回分支 |

返回：

- `data` 固定返回 `null`

限制：

- 任务只能处理一次
- 非管理员只能处理分配给自己的任务
- 发起节点执行 `submit` 时必须传 `selected_user_ids`
- 并行汇总节点执行 `return` 时必须传 `target_branch_key`
- 当前节点不允许驳回或退回时，对应动作不可用

## 7. 工作台

### 7.1 获取我的代办

- URL：`GET /api/workflow/work-items/todo/`
- 权限：登录
- 说明：列表主体是“当前用户的审批分配记录”，但展示内容已按“流程实例 + 当前审批节点 + 占比表示例信息”组装。

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| business_type | string | 否 | 按流程类型筛选：`report_submit` / `performance_claim` / `performance_transfer` |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明   |
| --- | --- |------|
| id | int | 审批分配 ID |
| instance_id | int | 实例 ID |
| instance_title | string/null | 实例标题 |
| process_def_id | int/null | 流程定义 ID |
| process_name | string/null | 流程名称 |
| business_type | string/null | 业务类型 |
| business_type_label | string/null | 业务类型名称 |
| business_id | int/null | 业务 ID |
| instance_status | string/null | 实例状态 |
| instance_status_label | string/null | 实例状态名称 |
| start_time | datetime/null | 实例开始时间 |
| end_time | datetime/null | 实例结束时间 |
| applicant_id | int/null | 发起人 ID |
| applicant_name | string/null | 发起人姓名 |
| task_id | int/null | 任务 ID |
| node_code | string | 节点编码 |
| node_name | string | 节点名称 |
| assignee_id | int | 审批人 ID |
| assignee_name | string/null | 审批人姓名 |
| round_no | int | 审批轮次 |
| task_status | string/null | 任务状态 |
| task_status_label | string/null | 任务状态名称 |
| branch_key | string/null | 分支标识 |
| branch_org_id | int/null | 分支机构 ID |
| branch_org_name | string/null | 分支机构名称 |
| cust_name | string/null | 占比表中的客户名称；同一实例下存在多条占比记录时，列表场景任取其中一条展示 |
| ecif_cust_id | string/null | 占比表中的 ECIF 客户编号；同一实例下存在多条占比记录时，列表场景任取其中一条展示 |
| accounting_org_id | string/null | 占比表中的核算机构编码；同一实例下存在多条占比记录时，列表场景任取其中一条展示 |
| accounting_org_name | string/null | 占比表中的核算机构名称；同一实例下存在多条占比记录时，列表场景任取其中一条展示 |
| result | string/null | 处理结果 |
| result_label | string/null | 处理结果名称 |
| received_at | datetime/null | 进入待办时间 |
| read_at | datetime/null | 查看时间 |
| handled_at | datetime/null | 处理时间 |
| comment | string/null | 处理意见 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 7.2 获取我的已办

- URL：`GET /api/workflow/work-items/done/`
- 权限：登录
- 说明：用户完成审批后，对应记录会从代办进入已办。

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| business_type | string | 否 | 按流程类型筛选：`report_submit` / `performance_claim` / `performance_transfer` |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

- 同 7.1

说明：

- 自动跳过的记录不会出现在已办列表

### 7.3 获取工作项详情

- URL：`GET /api/workflow/work-items/{id}/`
- 权限：登录

返回字段：

- 详情基础字段同 7.1
- 额外返回 `prop_status_list`，即当前流程实例绑定的全部占比表记录

`prop_status_list` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 占比记录 ID |
| process_instance_id | int/null | 绑定的流程实例 ID |
| data_dt | date/null | 生效日期 |
| ecif_cust_id | string/null | ECIF 客户编号 |
| orig_acct_id | string/null | 原始账号 |
| cust_name | string/null | 客户名称 |
| acctn_org_id | string/null | 认领机构编号 |
| acctn_org_name | string/null | 认领机构名称 |
| employee_no | string/null | 认领员工编号 |
| employee_name | string/null | 认领员工姓名 |
| kpi_prop | decimal/null | 业绩占比 |
| prop_status_flg | string | 占比生效状态 |
| prop_status_flg_label | string | 占比生效状态名称 |
| apl_data_dt | datetime/null | 申请时间 |
| pas_data_dt | datetime/null | 通过时间 |
| year_base_amount | decimal | 余额年累计基数 |
| genr_acct_id | string | 通用账户号 |

### 7.4 获取代办提醒

- URL：`GET /api/workflow/work-items/reminder/`
- 权限：登录

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| has_todo | bool | 是否存在待办 |
| todo_count | int | 待办数量 |

## 8. 日志

### 8.1 获取任务日志列表

- URL：`GET /api/workflow/task-logs/`
- 权限：登录

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| instance_id | int | 否 | 实例 ID |
| task_id | int | 否 | 任务 ID |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 日志 ID |
| instance_id | int | 实例 ID |
| task_id | int/null | 任务 ID |
| branch_key | string/null | 分支标识 |
| parallel_group | string/null | 并行组标识 |
| action | string | 动作编码 |
| action_label | string | 动作名称 |
| from_node_code | string/null | 来源节点编码 |
| from_node_name | string/null | 来源节点名称 |
| to_node_code | string/null | 目标节点编码 |
| to_node_name | string/null | 目标节点名称 |
| operator_id | int/null | 操作人 ID |
| operator_name | string/null | 操作人姓名 |
| result | string/null | 处理结果 |
| result_label | string/null | 处理结果名称 |
| comment | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

说明：

- 非管理员只能查看自己发起或自己参与过处理的实例日志

### 8.2 获取任务日志详情

- URL：`GET /api/workflow/task-logs/{id}/`
- 权限：登录
- 返回字段：同 8.1

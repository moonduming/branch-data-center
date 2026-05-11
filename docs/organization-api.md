# organization 接口文档

## 基础说明

- 服务前缀：`/api/organization`
- 权限：除用户下拉框接口外均要求管理员登录
- 当前实现方式：`ModelViewSet + Router`

## 1. 机构列表

- URL：`GET /api/organization/org-units/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 10 |
| org_name | string | 否 | 按机构名称模糊查询 |
| status | string | 否 | 按机构状态筛选，支持编码或中文名称 |

分页返回结构：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| count | int | 总记录数 |
| data | array | 当前页数据列表 |

机构对象字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 ID |
| org_code | string | 机构编码 |
| credit_org_code | string/null | 贷系统机构编码 |
| virtual_employee_no | string/null | 公共虚拟员工号 |
| org_name | string | 机构名称 |
| org_type | string | 机构类型：`00` 分行、`01` 部门、`02` 支行、`03` 直营 |
| org_type_label | string | 机构类型中文名称 |
| is_assessment_dept | bool | 是否考核部门 |
| leader_employee_no | string/null | 主管领导员工号 |
| manager_employee_no | string/null | 单位负责人员工号 |
| display_order | int | 排序号 |
| status | string | 状态：`01` 正常、`05` 停用、`09` 取消 |
| status_label | string | 状态中文名称 |
| parent_id | int/null | 父机构 ID |
| remark | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 2. 创建机构

- URL：`POST /api/organization/org-units/`

请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| org_code | string | 是 | 机构编码 |
| credit_org_code | string/null | 否 | 贷系统机构编码 |
| virtual_employee_no | string/null | 否 | 公共虚拟员工号 |
| org_name | string | 是 | 机构名称 |
| org_type | string | 是 | 机构类型 |
| is_assessment_dept | bool | 否 | 是否考核部门 |
| leader_employee_no | string/null | 否 | 主管领导员工号 |
| manager_employee_no | string/null | 否 | 单位负责人员工号 |
| display_order | int | 否 | 排序号 |
| status | string | 否 | 状态 |
| parent_id | int/null | 否 | 父机构 ID |
| remark | string/null | 否 | 备注 |

## 3. 查询机构详情

- URL：`GET /api/organization/org-units/{id}/`

## 4. 修改机构

- URL：`PUT /api/organization/org-units/{id}/`

更新请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| org_code | string | 否 | 机构编码 |
| credit_org_code | string/null | 否 | 贷系统机构编码 |
| virtual_employee_no | string/null | 否 | 公共虚拟员工号 |
| org_name | string | 否 | 机构名称 |
| org_type | string | 否 | 机构类型 |
| is_assessment_dept | bool | 否 | 是否考核部门 |
| leader_employee_no | string/null | 否 | 主管领导员工号 |
| manager_employee_no | string/null | 否 | 单位负责人员工号 |
| display_order | int | 否 | 排序号 |
| status | string | 否 | 状态 |
| parent_id | int/null | 否 | 父机构 ID |
| remark | string/null | 否 | 备注 |

说明：

- 前端多传字段会被忽略
- 可空字段允许传 `""` 或 `null`

## 5. 删除机构

- URL：`DELETE /api/organization/org-units/{id}/`

## 6. 机构人员关系列表

- URL：`GET /api/organization/user-org-relations/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 10 |
| org_name | string | 否 | 按机构名称模糊查询 |
| employee | string | 否 | 按员工姓名或员工编号模糊查询 |
| status | string | 否 | 按关系状态筛选，支持编码或中文名称 |

关系对象字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 ID |
| user_id | int | 用户 ID |
| org_id | int | 机构 ID |
| username | string | 员工编号 |
| full_name | string | 员工姓名 |
| org_code | string | 机构编码 |
| org_name | string | 机构名称 |
| credit_employee_no | string/null | 贷系统员工编号 |
| team_member_no | string/null | 团队成员编号 |
| team_org_code | string/null | 团队机构编码 |
| team_name | string/null | 团队名称 |
| line_code | string/null | 所属条线编码 |
| employee_level | string/null | 员工级别编码 |
| employee_level_label | string/null | 员工级别中文名称 |
| is_customer_manager | bool | 是否客户经理 |
| position_name | string/null | 岗位名称 |
| is_primary | bool | 是否主归属 |
| status | string | 状态：`01` 正常、`09` 失效 |
| status_label | string | 状态中文名称 |
| start_date | date/null | 生效日期 |
| end_date | date/null | 失效日期 |
| remark | string/null | 备注 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

## 7. 创建机构人员关系

- URL：`POST /api/organization/user-org-relations/`

请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| user_id | int | 是 | 用户 ID |
| org_id | int | 是 | 机构 ID |
| credit_employee_no | string/null | 否 | 贷系统员工编号 |
| team_member_no | string/null | 否 | 团队成员编号 |
| team_org_code | string/null | 否 | 团队机构编码 |
| team_name | string/null | 否 | 团队名称 |
| line_code | string/null | 否 | 所属条线编码 |
| employee_level | string/null | 否 | 员工级别编码 |
| is_customer_manager | bool | 否 | 是否客户经理 |
| position_name | string/null | 否 | 岗位名称 |
| is_primary | bool | 否 | 是否主归属 |
| status | string/null | 否 | 状态 |
| start_date | date/null | 否 | 生效日期 |
| end_date | date/null | 否 | 失效日期 |
| remark | string/null | 否 | 备注 |

## 8. 查询机构人员关系详情

- URL：`GET /api/organization/user-org-relations/{id}/`

## 9. 修改机构人员关系

- URL：`PUT /api/organization/user-org-relations/{id}/`

更新请求字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| user_id | int | 否 | 用户 ID |
| org_id | int | 否 | 机构 ID |
| credit_employee_no | string/null | 否 | 贷系统员工编号 |
| team_member_no | string/null | 否 | 团队成员编号 |
| team_org_code | string/null | 否 | 团队机构编码 |
| team_name | string/null | 否 | 团队名称 |
| line_code | string/null | 否 | 所属条线编码 |
| employee_level | string/null | 否 | 员工级别编码 |
| is_customer_manager | bool | 否 | 是否客户经理 |
| position_name | string/null | 否 | 岗位名称 |
| is_primary | bool | 否 | 是否主归属 |
| status | string/null | 否 | 状态 |
| start_date | date/null | 否 | 生效日期 |
| end_date | date/null | 否 | 失效日期 |
| remark | string/null | 否 | 备注 |

说明：

- 前端多传字段会被忽略
- 可空字段允许传 `""` 或 `null`

## 10. 删除机构人员关系

- URL：`DELETE /api/organization/user-org-relations/{id}/`

## 11. 用户下拉框

- URL：`GET /api/organization/options/users/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 按员工编号或员工姓名模糊查询 |
| org_id | int | 否 | 机构 ID；传入后仅返回该机构下有效关系用户 |

说明：

- 同时兼容 `value`、`query` 作为查询关键词参数
- 未传查询值时返回全量用户 ID 和用户名称
- 传 `org_id` 时，会按 `shenzhen_user_org_rel.org_id` 和有效状态过滤用户

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| user_id | int | 用户 ID |
| user_name | string | 用户名称 |
| user_code | string | 用户编码 |

## 12. 机构下拉框

- URL：`GET /api/organization/options/org-units/`

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 按机构编码或机构名称模糊查询 |

说明：

- 同时兼容 `value`、`query` 作为查询关键词参数
- 未传查询值时返回全量机构 ID 和机构名称

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| org_id | int | 机构 ID |
| org_name | string | 机构名称 |
| org_code | string | 机构编码 |

## 13. 机构类型下拉框

- URL：`GET /api/organization/options/org-types/`

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| org_type | string | 机构类型编码 |
| org_type_label | string | 机构类型中文名称 |

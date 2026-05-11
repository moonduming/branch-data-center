# users 接口文档

## 基础说明

- 服务前缀：`/api`
- 认证方式：JWT Access Token
- Access Token 有效期：15 分钟
- Token 失效处理：前端收到 `401` 且 `error_code=token_expired` 时，直接跳转登录页；跳转前可先调用登录状态检查接口
- 需要登录的接口请在请求头中携带：

```http
Authorization: Bearer <access_token>
```

## 返回格式

非分页成功响应：

```json
{
  "message": "登录成功",
  "data": {}
}
```

分页成功响应：

```json
{
  "message": "查询成功",
  "data": {
    "count": 100,
    "data": []
  }
}
```

错误响应：

```json
{
  "message": "登录已失效，请重新登录",
  "error_code": "token_expired",
  "errors": {
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid"
  }
}
```

说明：

- `message`：前端可直接展示的错误信息
- `error_code`：机器可识别错误码，token 失效时固定为 `token_expired`
- `errors`：可选，保留字段级错误或原始错误详情

## 1. 用户名密码登录

- URL：`POST /api/login/`
- 说明：通过用户名和密码登录，成功后返回用户信息和 Access Token

请求参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 是 | 员工编号 |
| password | string | 是 | 登录密码 |

成功响应示例：

```json
{
  "message": "登录成功",
  "data": {
    "logged_in": true,
    "auto_login": false,
    "user": {
      "id": 1,
      "username": "10001",
      "full_name": "张三",
      "user_status": "正常",
      "user_status_code": "01",
      "user_level": "超级管理员",
      "user_level_code": "99",
      "orgs": [
        {
          "org_id": 1,
          "org_code": "44000001",
          "org_name": "深圳分行",
          "org_type": "01",
          "is_primary": true
        }
      ],
      "bind_ip": null,
      "last_login": "2026-03-16T10:00:00+08:00",
      "last_login_ip": "127.0.0.1",
      "created_at": "2026-03-01T09:00:00+08:00",
      "updated_at": "2026-03-16T10:00:00+08:00"
    },
    "token": {
      "access": "jwt_access_token",
      "expires_in": 28800
    }
  }
}
```

## 2. 登录状态检查 / IP 自动登录

- URL：`GET /api/auth/status/`
- 说明：
  - 请求头里带有效 Access Token 时，直接返回当前登录状态
  - 未登录时，后台按客户端 IP 匹配 `bind_ip`
  - 匹配到正常状态用户后，自动登录并返回新的 Access Token

成功响应中的 `data` 结构与登录接口一致。

未登录响应示例：

```json
{
  "message": "未登录",
  "errors": {
    "logged_in": false,
    "auto_login": false,
    "request_ip": "127.0.0.1"
  }
}
```

## 3. 用户列表

- URL：`GET /api/users/`
- 说明：分页查询用户列表
- 权限：管理员

查询参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 10 |
| username | string | 否 | 按员工编号模糊查询 |
| full_name | string | 否 | 按用户名模糊查询 |
| user_status | string | 否 | 按用户状态查询，支持编码或中文名称 |

分页返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| message | string | 固定为 `查询成功` |
| data.count | int | 总记录数 |
| data.data | array | 当前页数据列表 |

用户对象字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | int | 主键 ID |
| username | string | 员工编号 |
| full_name | string | 员工姓名 |
| user_status | string | 用户状态中文名称：`正常`、`暂停`、`离职` |
| user_status_code | string | 用户状态编码：`01`、`05`、`09` |
| user_level | string | 用户级别中文名称：`超级管理员`、`普通用户` |
| user_level_code | string | 用户级别编码：`99`、`00` |
| orgs | array | 用户所属机构列表 |
| bind_ip | string/null | 绑定 IP |
| last_login | datetime/null | 最后登录时间 |
| last_login_ip | string/null | 最后登录 IP |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

`orgs` 列表元素字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| org_id | int | 机构 ID |
| org_code | string | 机构编码 |
| org_name | string | 机构名称 |
| is_primary | boolean | 是否主归属机构 |

## 4. 创建用户

- URL：`POST /api/users/`
- 权限：管理员

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 是 | 员工编号 |
| password | string | 否 | 登录密码，至少 8 位 |
| full_name | string | 是 | 员工姓名 |
| user_status | string | 否 | 用户状态，默认 `01` |
| user_level | string | 否 | 用户级别，默认 `00` |
| bind_ip | string/null | 否 | 绑定 IP，可传 `null`；传 `""` 时按空值处理 |

说明：

- `created_at`、`updated_at` 由后台自动维护，不需要传
- 前端多传字段会被忽略

## 5. 查询用户详情

- URL：`GET /api/users/{id}/`
- 权限：管理员

返回的 `data` 为单个用户对象，字段结构同“用户对象字段说明”。

## 6. 修改用户

- URL：`PUT /api/users/{id}/`
- 权限：管理员

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 否 | 员工编号 |
| full_name | string | 否 | 员工姓名 |
| user_status | string | 否 | 用户状态，传空字符串或 `null` 时忽略，不覆盖原值 |
| user_level | string | 否 | 用户级别，传空字符串或 `null` 时忽略，不覆盖原值 |
| bind_ip | string/null | 否 | 绑定 IP，传 `""` 时按空值处理 |

说明：

- `created_at`、`updated_at` 由后台自动维护，不需要传
- 未传字段保持原值

## 7. 删除用户

- URL：`DELETE /api/users/{id}/`
- 权限：管理员

成功响应：

```json
{
  "message": "删除成功",
  "data": null
}
```

失败示例：

```json
{
  "message": "当前用户已被用户机构关系数据引用，请先删除关系表中的对应数据后再删除用户",
  "errors": {
    "user_id": [
      "当前用户已被用户机构关系数据引用，请先删除关系表中的对应数据后再删除用户"
    ]
  }
}
```

## 8. 修改密码

- URL：`POST /api/users/change-password/`
- 权限：已登录用户

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| old_password | string | 是 | 原密码 |
| new_password | string | 是 | 新密码 |
| confirm_password | string | 是 | 确认新密码 |

成功响应：

```json
{
  "message": "密码修改成功，请重新登录",
  "data": null
}
```

失败示例：

```json
{
  "message": "原密码不能为空",
  "errors": {
    "old_password": [
      "原密码不能为空"
    ]
  }
}
```

## 9. 重置用户密码

- URL：`POST /api/users/{id}/reset-password/`
- 权限：管理员
- 说明：将目标用户密码重置为固定值 `123456`

成功响应：

```json
{
  "message": "密码重置成功，新密码为123456",
  "data": null
}
```

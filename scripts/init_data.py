import os
import sys
from pathlib import Path

import pandas as pd
import sqlparse
import MySQLdb

# ===== 1. Django 环境初始化 =====
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

import django
django.setup()

from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.users.models import User
from apps.organization.models import OrgUnit, UserOrgRelation


DEFAULT_PASSWORD = "123456"

# ===== 2. Excel 列名配置 =====
EMPLOYEE_NO_COL = "员工编号"
EMPLOYEE_NAME_COL = "员工姓名"
ORG_CODE_COL = "机构代码"
EMPLOYEE_LEVEL_COL = "员工级别"


def read_excel(excel_path: str, sheet_name=0) -> pd.DataFrame:
    df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str)
    df.columns = [str(col).strip() for col in df.columns]
    df = df.fillna("")

    required_columns = [
        EMPLOYEE_NO_COL,
        EMPLOYEE_NAME_COL,
        ORG_CODE_COL,
        EMPLOYEE_LEVEL_COL,
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Excel 缺少必要列: {missing_columns}")

    for col in required_columns:
        df[col] = df[col].astype(str).str.strip()

    # 去掉完全无效的空行
    df = df[
        ~(
            (df[EMPLOYEE_NO_COL] == "")
            & (df[EMPLOYEE_NAME_COL] == "")
            & (df[ORG_CODE_COL] == "")
        )
    ].copy()

    return df


def validate_employee_level(level: str) -> str | None:
    if not level:
        return None

    valid_levels = {choice[0] for choice in UserOrgRelation.EmployeeLevel.choices}
    if level not in valid_levels:
        raise ValueError(f"非法员工级别编码: {level}")
    return level


def import_users(df: pd.DataFrame):
    """
    导入用户表
    去重规则：员工编号 + 员工姓名
    如果员工编号已存在：
      - 姓名相同：跳过
      - 姓名不同：打印警告
    """
    user_keys = df[[EMPLOYEE_NO_COL, EMPLOYEE_NAME_COL]].drop_duplicates()

    now = timezone.now()

    # employee_nos = user_keys[EMPLOYEE_NO_COL].tolist()
    # existing_users = User.objects.filter(username__in=employee_nos)
    # existing_user_map = {u.username: u for u in existing_users}

    users_to_create = []
    # name_conflicts = []

    for _, row in user_keys.iterrows():
        employee_no = row[EMPLOYEE_NO_COL]
        employee_name = row[EMPLOYEE_NAME_COL]

        if not employee_no or not employee_name:
            print(f"[跳过用户] 员工编号或员工姓名为空: {employee_no=}, {employee_name=}")
            continue

        # existed_user = existing_user_map.get(employee_no)
        # if existed_user:
        #     if existed_user.full_name != employee_name:
        #         name_conflicts.append((employee_no, existed_user.full_name, employee_name))
        #     continue

        users_to_create.append(
            User(
                username=employee_no,
                full_name=employee_name,
                password=make_password(DEFAULT_PASSWORD),
                user_status=User.Status.NORMAL,
                user_level=User.Level.NORMAL,
                created_at=now,
                updated_at=now,
            )
        )

    # if name_conflicts:
    #     print("\n[警告] 发现员工编号已存在但姓名不一致：")
    #     for employee_no, db_name, excel_name in name_conflicts:
    #         print(f"  员工编号={employee_no}, 数据库姓名={db_name}, Excel姓名={excel_name}")

    if users_to_create:
        User.objects.bulk_create(users_to_create, batch_size=500)
        print(f"[用户] 成功新增 {len(users_to_create)} 个")
    else:
        print("[用户] 没有需要新增的数据")


def import_user_org_relations(df: pd.DataFrame):
    """
    导入用户机构关系表
    去重规则：user_id + org_id
    """
    # employee_nos = df[EMPLOYEE_NO_COL].drop_duplicates().tolist()
    org_codes = df[ORG_CODE_COL].drop_duplicates().tolist()

    user_map = dict(
        # User.objects.filter(username__in=employee_nos).values_list("username", "id")
        User.objects.all().values_list("username", "id")
    )
    org_map = dict(
        # OrgUnit.objects.filter(org_code__in=org_codes).values_list("org_code", "id")
        OrgUnit.objects.all().values_list("org_code", "id")
    )

    missing_org_codes = [code for code in org_codes if code and code not in org_map]
    if missing_org_codes:
        print("\n[警告] 以下机构代码在机构表中不存在：")
        for code in missing_org_codes:
            print(f"  - {code}")

    relation_data = {}

    now = timezone.now()

    for _, row in df.iterrows():
        employee_no = row[EMPLOYEE_NO_COL]
        employee_name = row[EMPLOYEE_NAME_COL]
        org_code = row[ORG_CODE_COL]
        employee_level = row[EMPLOYEE_LEVEL_COL]

        if not employee_no or not employee_name or not org_code:
            print(
                f"[跳过关系] 必要字段为空: 员工编号={employee_no!r}, 员工姓名={employee_name!r}, 机构代码={org_code!r}"
            )
            continue

        user_id = user_map.get(employee_no)
        if not user_id:
            print(f"[跳过关系] 找不到用户: 员工编号={employee_no}")
            continue

        org_id = org_map.get(org_code)
        if not org_id:
            print(f"[跳过关系] 找不到机构: 机构代码={org_code}")
            continue

        try:
            employee_level = validate_employee_level(employee_level)
        except ValueError as exc:
            print(f"[跳过关系] {exc}，员工编号={employee_no}，机构代码={org_code}")
            continue

        # 同一个 user + org 只保留一条
        relation_data[(user_id, org_id)] = {
            "employee_level": employee_level,
        }

    if not relation_data:
        print("[用户机构关系] 没有可插入的数据")
        return

    # existing_relations = UserOrgRelation.objects.filter(
    #     user_id__in=[k[0] for k in relation_data.keys()],
    #     org_id__in=[k[1] for k in relation_data.keys()],
    # )
    # existing_keys = {(r.user_id, r.org_id) for r in existing_relations}

    relations_to_create = []
    for (user_id, org_id), extra in relation_data.items():
        # if (user_id, org_id) in existing_keys:
        #     continue

        relations_to_create.append(
            UserOrgRelation(
                user_id=user_id,
                org_id=org_id,
                employee_level=extra["employee_level"],
                status=UserOrgRelation.Status.NORMAL,
                is_primary=False,
                created_at=now,
                updated_at=now,
            )
        )

    if relations_to_create:
        UserOrgRelation.objects.bulk_create(relations_to_create, batch_size=500)
        print(f"[用户机构关系] 成功新增 {len(relations_to_create)} 条")
    else:
        print("[用户机构关系] 没有需要新增的数据")


def execute_sql_file(cursor, sql_file_path):
    with open(sql_file_path, 'r') as f:
        sql = f.read()
    statements = sqlparse.split(sql)
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)


def get_conn():
    return MySQLdb.connect(
            host=(os.getenv('MYSQL_HOST') or '').strip(),
            user=(os.getenv('MYSQL_USER') or '').strip(),
            passwd=(os.getenv('MYSQL_PASSWORD') or '').strip(),
            port=int(os.getenv('MYSQL_PORT') or 3306),
            db=(os.getenv('MYSQL_DATABASE') or '').strip(),
            charset='utf8mb4',
        )


def main():
    conn = get_conn()
    cursor = conn.cursor()

    # ===== 执行初始化 SQL =====
    print("开始执行数据库初始化 SQL...")

    drop_table_sql_path = Path(__file__).parent / "drop_table.sql"
    create_table_sql_path = Path(__file__).parent / "create_table.sql"
    insert_org_sql_path = Path(__file__).parent / "insert_org_unit.sql"
    insert_perf_indicator_sql_path = Path(__file__).parent / "insert_perf_indicator_seed.sql"
    insert_result_dependency_sql_path = Path(__file__).parent / "insert_result_dependency.sql"
    insert_workflow_data_sql_path = Path(__file__).parent / "insert_workflow_data.sql"
    insert_perf_indicator_seed = Path(__file__).parent / "insert_perf_indicator_rule_post_profit_seed.sql"

    for sql_path in [
        drop_table_sql_path,
        create_table_sql_path,
        insert_org_sql_path,
        insert_perf_indicator_sql_path,
        insert_result_dependency_sql_path,
        insert_workflow_data_sql_path,
        insert_perf_indicator_seed,
    ]:
        if sql_path.exists():
            print(f"执行 SQL 文件: {sql_path}")
            execute_sql_file(cursor, sql_path)
        else:
            print(f"[跳过] SQL 文件不存在: {sql_path}")

    conn.commit()
    print("数据库初始化完成")

    excel_path = Path(__file__).parent / "深圳分行人员名单.xlsx"
    if not excel_path.exists():
        raise FileNotFoundError(f"找不到文件: {excel_path}")

    print(f"开始导入: {excel_path}")

    df = read_excel(str(excel_path))
    print(f"读取到 {len(df)} 行数据")

    with transaction.atomic():
        import_users(df)
        import_user_org_relations(df)

    print("导入完成")


if __name__ == "__main__":
    """
    注意: 执行该脚本会删除所有表进行重建，数据重新导入
    """
    main()

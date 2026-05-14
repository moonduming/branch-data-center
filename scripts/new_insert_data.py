import os
import sys
from pathlib import Path
import sqlparse
import MySQLdb

import pandas as pd

# ===== 1. Django 环境初始化 =====
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

import django
django.setup()

from django.db import transaction

from apps.users.models import User
from apps.organization.models import UserOrgRelation


EMPLOYEE_NO_COL = "员工编号"
TEAM_NAME_COL = "团队"


def read_excel(excel_path: str, sheet_name=0) -> pd.DataFrame:
    df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str)
    df.columns = [str(col).strip() for col in df.columns]
    df = df.fillna("")

    required_columns = [
        EMPLOYEE_NO_COL,
        TEAM_NAME_COL,
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
            & (df[TEAM_NAME_COL] == "")
        )
    ].copy()

    return df


def import_team_data(df: pd.DataFrame):
    users_data = User.objects.all().values_list("id", "username")
    users_data = {username: user_id for user_id, username in users_data}

    for _, row in df.iterrows():
        employee_no = row[EMPLOYEE_NO_COL]
        team_name = row[TEAM_NAME_COL]
        user_id = users_data.get(employee_no)

        if user_id is None:
            print(f"未找到员工编号对应用户: {employee_no}")
            continue

        updated_count = UserOrgRelation.objects.filter(user_id=user_id).update(team_name=team_name)
        if updated_count == 0:
            print(f"用户未找到机构关系数据: employee_no={employee_no}, user_id={user_id}")


def get_conn():
    return MySQLdb.connect(
        host=(os.getenv('MYSQL_HOST') or '').strip(),
        user=(os.getenv('MYSQL_USER') or '').strip(),
        passwd=(os.getenv('MYSQL_PASSWORD') or '').strip(),
        port=int(os.getenv('MYSQL_PORT') or 3306),
        db=(os.getenv('MYSQL_DATABASE') or '').strip(),
        charset='utf8mb4',
    )


def execute_sql_file(cursor, sql_file_path):
    with open(sql_file_path, 'r') as f:
        sql = f.read()
    statements = sqlparse.split(sql)
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)


def main():
    conn = get_conn()
    cursor = conn.cursor()

    # ===== 执行初始化 SQL =====
    print("插入新数据...")
    create_table_sql_path = Path(__file__).parent / "new_create.sql"
    insert_workflow_data_sql_path = Path(__file__).parent / "insert_workflow_data.sql"
    insert_perf_indicator_seed = Path(__file__).parent / "insert_perf_indicator_rule_post_profit_seed.sql"
    add_filed_sql_path = Path(__file__).parent / "add_field.sql"

    for sql_path in [
        create_table_sql_path,
        insert_workflow_data_sql_path,
        insert_perf_indicator_seed,
        add_filed_sql_path,
    ]:
        if sql_path.exists():
            print(f"执行 SQL 文件: {sql_path}")
            execute_sql_file(cursor, sql_path)
        else:
            print(f"[跳过] SQL 文件不存在: {sql_path}")

    conn.commit()
    print("完成")

    print("--------------------------------")

    print("机构人员关系表导入团队数据...")
    excel_path = Path(__file__).parent / "人员团队.xlsx"
    if not excel_path.exists():
        raise FileNotFoundError(f"找不到文件: {excel_path}")

    print(f"开始导入: {excel_path}")

    df = read_excel(str(excel_path))
    print(f"读取到 {len(df)} 行数据")

    with transaction.atomic():
        import_team_data(df)

    print("导入完成")


if __name__ == "__main__":
    # todo: 正式环境未执行，需要手动执行
    main()
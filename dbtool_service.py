from pathlib import Path
from flask import Flask, request, jsonify
import subprocess
import shlex
import json

app = Flask(__name__)

# 获取配置文件
BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "config.json", "r") as f:
    config = json.load(f)


def build_command(file_path: str, table_name: str, column_list: str) -> str:
    """
    构造安全的 dbtool 命令（只允许拼接白名单参数）
    """
    sql = (
        f"load data infile '{file_path}' "
        f"into table {table_name} "
        "fields terminated by '@_@' "
        "optionally enclosed by '\\\"' "
        "lines terminated by '\\n' "
        f"({column_list});"
    )

    cmd = (
        f"{config['DB_TOOL_PATH']} "
        f"-loadserver "
        f"-type=\"in\" "
        f"-clusterid={config['CLUSTER_ID']} "
        f"-user={config['DB_USER']} "
        f"-password='{config['DB_PASSWORD']}' "
        f"-db-conn-info={config['DB_CONN_INFO']} "
        f"-sql=\"{sql}\" "
        f"-loadin-support-null=\"1\""
    )

    return cmd


@app.route("/run-import", methods=["POST"])
def run_import():
    data = request.json or {}

    file_path = data.get("file_path")
    table_name = data.get("table_name")
    column_list = data.get("column_list")

    if not file_path or not table_name or not column_list:
        return jsonify({
            "code": 1,
            "msg": "file_path、table_name 和 column_list 必填"
        }), 400

    try:
        cmd = build_command(file_path, table_name, column_list)

        # 使用 sudo 切换用户执行
        full_cmd = f'''su - {config['RUN_AS_USER']} -c {shlex.quote(cmd)}'''

        result = subprocess.run(
            full_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600  # 可根据需要调整
        )

        return jsonify({
            "code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "cmd": cmd  # 调试用，可上线后去掉
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "code": 2,
            "msg": "执行超时"
        }), 500

    except Exception as e:
        return jsonify({
            "code": 3,
            "msg": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
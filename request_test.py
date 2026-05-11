# request_test_debug.py

import requests
import json

URL = "http://127.0.0.1:5001/run-import"

def test():
    payload = {
        "file_path": "/home/shenzhen_data_ftp/shenzhen_data/20250930/I01_SZ_ACCT_SUM_D_20250930.txt",
        "table_name": "shenzhen_data.i01_sz_acct_sum_d"
    }

    print("=== 请求参数 ===")
    print(json.dumps(payload, indent=2))

    try:
        resp = requests.post(URL, json=payload, timeout=600)

        print("\n=== HTTP状态 ===")
        print(resp.status_code)

        data = resp.json()

        print("\n=== 返回JSON ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        print("\n=== 关键字段 ===")
        print("code:", data.get("code"))
        print("stdout:", data.get("stdout"))
        print("stderr:", data.get("stderr"))

    except Exception as e:
        print("❌ 请求异常:", str(e))


if __name__ == "__main__":
    test()
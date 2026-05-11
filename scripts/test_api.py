import requests

BASE_URL = "http://127.0.0.1:9000"

def test_create_user():
    url = f"{BASE_URL}/api/users/"

    data = {
        "username": "test001",
        "full_name": "测试用户",
        "password": "123456",
    }

    resp = requests.post(url, json=data)

    print("创建用户状态码:", resp.status_code)
    print("返回结果:", resp.text)


def test_login():
    url = f"{BASE_URL}/api/login/"

    data = {
        "username": "test001",
        "password": "123456"
    }

    resp = requests.post(url, json=data)

    print("登录状态码:", resp.status_code)
    print("返回结果:", resp.text)


if __name__ == "__main__":
    print("开始测试接口...\n")

    test_create_user()

    print("\n------------------\n")

    test_login()

# mysqlclient==2.2.4
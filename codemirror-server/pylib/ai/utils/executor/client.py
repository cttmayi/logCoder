
import requests
from pylib.ai.utils.executor.server import DEFAULT_PORT

# 返回结果 示例 ： {'stdout': '5050\n', 'stderr': ''}
def send_code_to_server(code: str, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
    url = f"http://{host}:{port}/execute"
    payload = {"code": code}
    response = requests.post(url, json=payload)
    
    result = {}
    if response.status_code == 200:
        # print("代码执行成功，返回结果：")
        # print(response.json())
        result['stdout'] = response.json()
    else:
        print(f"代码执行失败，错误信息：{response.text}")
        result['stderr'] = response.text
    return result

if __name__ == "__main__":
    code_to_execute = """
# 计算从1到100的所有整数之和
total_sum = sum(range(1, 101))  # range(1, 101)生成从1到100的整数序列

# 打印结果
print(total_sum)
"""
    e = send_code_to_server(code=code_to_execute)
    print(e)
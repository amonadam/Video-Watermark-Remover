import requests
import json

# 发送处理请求
task_id = "10d71506-d72a-42aa-b9e9-87208c6f144a"
url = "http://localhost:8080/api/process"
data = {"task_id": task_id}

print(f"发送处理请求: {data}")
response = requests.post(url, json=data)
print(f"响应状态码: {response.status_code}")
print(f"响应内容: {response.text}")

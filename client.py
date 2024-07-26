import time

import requests

resp = requests.post(
    "http://127.0.0.1:5000/upscale",
    files={"image": open("test.png", "rb")},
)
resp_data = resp.json()
print(resp_data)

task_id = resp_data.get("task_id")
print(task_id)

resp = requests.get(f"http://127.0.0.1:5000/tasks/{task_id}")
print(resp.json())

time.sleep(8)

resp = requests.get(f"http://127.0.0.1:5000/tasks/{task_id}")
resp_data = resp.json()
print(resp_data)

if "file" in resp_data:
    resp = requests.get(f"http://127.0.0.1:5000{resp_data.get("file")}")

    print(resp.headers)

"""
웹 API 호출 예제.
실행: python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload
     python sample_web.py
"""

import json
from urllib import request

API = "http://127.0.0.1:8000"

def get(path):
    with request.urlopen(API + path, timeout=10) as r:
        return json.loads(r.read())

def post(path, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = request.Request(API + path, data=data, headers=headers, method="POST")
    with request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

print(get("/health"))
print(get("/dashboard/state"))
# print(post("/dashboard/power-on"))
# print(post("/dashboard/brake-release"))
# print(post("/dashboard/load", {"program_path": "/programs/main.urp"}))
# print(post("/dashboard/play"))
# print(post("/dashboard/stop"))
# print(post("/dashboard/start", {"program_path": "/programs/main.urp"}))

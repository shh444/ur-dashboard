# UR Dashboard

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://shh444.github.io/ur-dashboard/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Universal Robots Dashboard Server(TCP 29999) 제어 패키지.

UR e-Series 공식 Dashboard 매뉴얼의 모든 명령을 지원합니다.

📖 **문서**: https://shh444.github.io/ur-dashboard/

---

## 설치

```bash
pip install git+https://github.com/shh444/ur-dashboard.git
```

또는 로컬:

```bash
git clone https://github.com/shh444/ur-dashboard.git
cd ur-dashboard
pip install -e .
```

---

## 빠른 시작

```python
from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101")
print(ur.state())
ur.close()

기본 명령
ur.power_on() ur.brake_release() ur.load("/programs/main.urp") ur.play() ur.stop()
#시퀀스 — 상태를 보고 알아서 처리
ur.seq_servo_on()
ur.close()

#실행 결과 예시 (sequence servo_on())
Sequence: SUCCESS
  ✓ Step 1: check_state
  ✓ Step 2: power_on
  ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING']) (5.5s)
  ✓ Step 4: brake_release
  ✓ Step 5: wait_until_robotmode(RUNNING) (3.2s)
  ✓ Step 6: check_state

### Async

```python
import asyncio
from ur_dashboard import AsyncDashboard
async def main(): 
    ur = AsyncDashboard("192.168.1.101") 
    await ur.connect() 
    await ur.seq_full_boot() 
    await ur.close()
asyncio.run(main())



### Web API

```bash
python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload

Swagger UI: http://127.0.0.1:8000/docs
메서드	설명
seq_servo_on()	서보 ON (이미 켜져있으면 스킵)
seq_servo_off()	서보 OFF (이미 꺼져있으면 스킵)
seq_start(path?)	프로그램 실행 (서보 OFF면 자동으로 켬)
seq_error_reset()	에러 초기화 (정상이면 스킵)
seq_full_boot(path?)	에러 초기화 + 서보 ON + 프로그램 실행

---

## 프로젝트 구조

```text
ur-dashboard/
├─ ur_dashboard/
│   ├─ __init__.py
│   ├─ client.py              # TCP 통신 코어
│   ├─ exceptions.py          # 예외
│   ├─ async_dashboard.py     # AsyncDashboard
│   ├─ sync_dashboard.py      # SyncDashboard + 시퀀스
│   └─ server.py              # FastAPI 웹 API
├─ docs/                      # Sphinx 문서
├─ sample_sync.py
├─ sample_async.py
├─ sample_web.py
├─ pyproject.toml
└─ README.md
문서
자세한 API 문서와 시퀀스 동작 설명은 아래에서 확인할 수 있습니다.
📖 https://shh444.github.io/ur-dashboard/

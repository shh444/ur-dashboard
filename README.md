# UR Dashboard

Universal Robots Dashboard Server (TCP 29999) 제어용 Python 패키지입니다.

---

## ✨ Features

* Sync / Async API 지원
* UR e-Series Dashboard 명령 지원
* 상태 기반 시퀀스 실행
* FastAPI Web API 제공
* Sphinx 문서 지원 (GitHub Pages)

---

## 📚 Documentation

👉 https://shh444.github.io/ur-dashboard/

---

## 📦 Installation

```bash
git clone https://github.com/your-repo/ur-dashboard.git
cd ur-dashboard
pip install -e .
```

### Web API 포함 설치

```bash
pip install -e ".[api]"
```

### Docs 포함 설치

```bash
pip install -e ".[docs]"
```

---

## 🚀 Quick Start

### Sync

```python
from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101")

print(ur.state())
print(ur.robotmode())

ur.close()
```

### Async

```python
import asyncio
from ur_dashboard import AsyncDashboard

async def main():
    ur = AsyncDashboard("192.168.1.101")
    await ur.connect()

    print(await ur.state())
    print(await ur.robotmode())

    await ur.close()

asyncio.run(main())
```

---

## 🧠 Sequence Usage

시퀀스는 현재 상태를 기반으로 필요한 단계만 자동 실행합니다.

### Available Sequences

| Method                     | Description |
| -------------------------- | ----------- |
| `seq_servo_on()`           | Servo ON    |
| `seq_servo_off()`          | Servo OFF   |
| `seq_start(path=None)`     | 프로그램 실행     |
| `seq_error_reset()`        | 에러 초기화      |
| `seq_full_boot(path=None)` | 전체 부팅       |

### Example

```python
from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101")

result = ur.seq_servo_on()
print(result.summary())

ur.close()
```

### Example Output

```text
Sequence: SUCCESS
  ✓ Step 1: check_state
  ✓ Step 2: power_on
  ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING'])
  ✓ Step 4: brake_release
  ✓ Step 5: wait_until_robotmode(RUNNING)
  ✓ Step 6: check_state
```

---

## 🔧 Sync Usage

```python
from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101")

# Query
print(ur.state())
print(ur.robotmode())
print(ur.running())
print(ur.safetystatus())

# Action
print(ur.power_on())
print(ur.brake_release())
print(ur.play())

ur.close()
```

---

## ⚡ Async Usage

```python
import asyncio
from ur_dashboard import AsyncDashboard

async def main():
    ur = AsyncDashboard("192.168.1.101")
    await ur.connect()

    print(await ur.state())
    print(await ur.power_on())
    print(await ur.brake_release())
    print(await ur.play())

    await ur.close()

asyncio.run(main())
```

---

## 🌐 Web API (FastAPI)

### Run Server

```bash
python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload
```

### Swagger UI

http://127.0.0.1:8000/docs

### Example

```bash
curl http://127.0.0.1:8000/dashboard/state
curl -X POST http://127.0.0.1:8000/dashboard/power-on
curl -X POST http://127.0.0.1:8000/dashboard/play
```

---

## 📁 Project Structure

```text
ur-dashboard/
├─ ur_dashboard/
│  ├─ async_dashboard.py
│  ├─ sync_dashboard.py
│  ├─ client.py
│  ├─ exceptions.py
│  └─ server.py
├─ docs/
├─ sample_sync.py
├─ sample_async.py
├─ sample_web.py
├─ pyproject.toml
└─ README.md
```

---

## 🧩 Main Classes

### `SyncDashboard`

동기 방식 제어용 클래스

```python
from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101")
print(ur.state())
ur.close()
```

### `AsyncDashboard`

비동기 방식 제어용 클래스

```python
from ur_dashboard import AsyncDashboard
```

---

## 🛠 Common Methods

### Query

* `state()`
* `robotmode()`
* `running()`
* `programstate()`
* `safetystatus()`

### Action

* `power_on()`, `power_off()`
* `brake_release()`
* `load(path)`, `play()`, `stop()`
* `pause()`
* `unlock_protective_stop()`
* `restart_safety()`
* `shutdown()`

---

## ⚠️ Error Handling

```python
from ur_dashboard import (
    SyncDashboard,
    DashboardCommunicationError,
    DashboardCommandRejected,
)

ur = None

try:
    ur = SyncDashboard("192.168.1.101")
    ur.seq_full_boot("/programs/main.urp")

except DashboardCommunicationError:
    print("Robot connection failed")

except DashboardCommandRejected as e:
    print(f"Command rejected: {e.raw_response}")

finally:
    if ur:
        ur.close()
```

---

## 📄 Docs Build

```bash
pip install -e ".[docs]"
cd docs
make html
```

Windows:

```powershell
pip install -e ".[docs]"
cd docs
.\make.bat html
```

---

## ⚠️ Notes

* 실제 장비 사용 시 반드시 안전 확인 필요
* `unlock_protective_stop()`는 원인 제거 후 사용
* 일부 명령은 Remote Control 모드 필요
* `seq_*` 메서드는 상태 기반으로 동작

---

## 📜 License

MIT License

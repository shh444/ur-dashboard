# UR Dashboard

A Python package for controlling the Universal Robots Dashboard Server (TCP 29999).

---

## ✨ Features

* Sync / Async API support
* Supports UR e-Series Dashboard commands
* State-based sequence execution
* FastAPI Web API support
* Sphinx documentation (GitHub Pages)

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

### Install with Web API support

```bash
pip install -e ".[api]"
```

### Install with Docs support

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

Sequences execute only the required steps based on the current robot state.

### Available Sequences

| Method                     | Description        |
| -------------------------- | ------------------ |
| `seq_servo_on()`           | Turn servo ON      |
| `seq_servo_off()`          | Turn servo OFF     |
| `seq_start(path=None)`     | Start program      |
| `seq_error_reset()`        | Reset errors       |
| `seq_full_boot(path=None)` | Full boot sequence |

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

Synchronous control interface

```python
from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101")
print(ur.state())
ur.close()
```

### `AsyncDashboard`

Asynchronous control interface

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

* Always ensure safety before operating a real robot
* Use `unlock_protective_stop()` only after resolving the root cause
* Some commands require Remote Control mode
* `seq_*` methods prioritize state-based execution over fixed delays

---

## 📜 License

MIT License

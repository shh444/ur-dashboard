# UR Dashboard

Universal Robots Dashboard Server(TCP 29999) 제어 패키지입니다.

- **Sync / Async 지원**
- **UR e-Series Dashboard 명령 지원**
- **상태 기반 시퀀스 지원**
- **FastAPI Web API 지원**
- **Sphinx 문서 제공**

## Documentation

- **Docs**: https://shh444.github.io/ur-dashboard/

---

## Features

- `SyncDashboard` / `AsyncDashboard`
- 기본 Dashboard 명령 직접 호출
- 상태 기반 시퀀스 제공
  - `seq_servo_on()`
  - `seq_servo_off()`
  - `seq_start()`
  - `seq_error_reset()`
  - `seq_full_boot()`
- FastAPI 서버 제공: `ur_dashboard.server:app`
- GitHub Pages + Sphinx 문서 지원

---

## Installation

### Install from GitHub

```bash
pip install git+https://github.com/shh444/ur-dashboard.git

Local install
bash


git clone https://github.com/shh444/ur-dashboard.git
cd ur-dashboard
pip install -e .
Install with Web API support
bash


pip install -e ".[api]"
Install with Docs support
bash


pip install -e ".[docs]"
Quick Start
Sync
python


from ur_dashboard import SyncDashboard
ur = SyncDashboard("192.168.1.101")
print(ur.state()) print(ur.robotmode())
ur.close()



### Async

```python
import asyncio
from ur_dashboard import AsyncDashboard
async def main(): ur = AsyncDashboard("192.168.1.101") await ur.connect()


print(await ur.state())
print(await ur.robotmode())


await ur.close()
asyncio.run(main())



---

## Sync Usage

```python
from ur_dashboard import SyncDashboard
ur = SyncDashboard("192.168.1.101")
Query
print(ur.state()) print(ur.robotmode()) print(ur.running()) print(ur.safetystatus())
Action
print(ur.power_on()) print(ur.brake_release()) print(ur.load("/programs/main.urp")) print(ur.play()) print(ur.stop())
ur.close()



---

## Async Usage

```python
import asyncio
from ur_dashboard import AsyncDashboard
async def main(): ur = AsyncDashboard("192.168.1.101") await ur.connect()


print(await ur.state())
print(await ur.power_on())
print(await ur.brake_release())
print(await ur.play())


await ur.close()
asyncio.run(main())



---

## Sequence Usage

시퀀스는 **현재 상태를 먼저 확인하고**,  
이미 완료된 단계는 **자동으로 건너뛰고**,  
필요한 단계만 실행합니다.

### Available sequence methods

| Method | Description |
|--------|-------------|
| `seq_servo_on()` | 서보 ON |
| `seq_servo_off()` | 서보 OFF |
| `seq_start(path=None)` | 프로그램 실행 |
| `seq_error_reset()` | 에러 초기화 |
| `seq_full_boot(path=None)` | 에러 초기화 + 서보 ON + 프로그램 실행 |

### Example

```python
from ur_dashboard import SyncDashboard
ur = SyncDashboard("192.168.1.101")
result = ur.seq_servo_on() print(result.summary())
ur.close()



### Example output

```text
Sequence: SUCCESS
  ✓ Step 1: check_state
  ✓ Step 2: power_on
  ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING']) (5.5s)
  ✓ Step 4: brake_release
  ✓ Step 5: wait_until_robotmode(RUNNING) (3.2s)
  ✓ Step 6: check_state
Sequence behavior
seq_servo_on()
이미 RUNNING이면 스킵
IDLE이면 brake_release()만 수행
그 외에는 power_on() 후 brake_release()
seq_servo_off()
이미 POWER_OFF이면 스킵
아니면 power_off() 수행
seq_start(path=None)
이미 프로그램 실행 중이면 스킵
서보가 꺼져 있으면 내부적으로 seq_servo_on() 수행
path가 있으면 load(path) 후 play()
path가 없으면 play()만 수행
seq_error_reset()
safety가 정상이면 스킵
PROTECTIVE_STOP이면 보호정지 해제
그 외 safety 에러는 restart_safety() 수행
seq_full_boot(path=None)
safety 이상이 있으면 seq_error_reset()
이후 seq_start(path) 수행
Web API
FastAPI 서버를 통해 HTTP로 로봇을 제어할 수 있습니다.
Run server
bash


python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload
Swagger UI
http://127.0.0.1:8000/docs
Example
bash


curl http://127.0.0.1:8000/dashboard/state
curl -X POST http://127.0.0.1:8000/dashboard/power-on
curl -X POST http://127.0.0.1:8000/dashboard/play
Sample Files
sample_sync.py
sample_async.py
sample_web.py
Project Structure
text


ur-dashboard/
├─ ur_dashboard/
│  ├─ __init__.py
│  ├─ client.py
│  ├─ exceptions.py
│  ├─ async_dashboard.py
│  ├─ sync_dashboard.py
│  └─ server.py
├─ docs/
├─ sample_sync.py
├─ sample_async.py
├─ sample_web.py
├─ pyproject.toml
└─ README.md
Main Classes
SyncDashboard
동기 방식 제어용 클래스입니다.
python


from ur_dashboard import SyncDashboard
ur = SyncDashboard("192.168.1.101") print(ur.state()) ur.close()



### `AsyncDashboard`

비동기 방식 제어용 클래스입니다.

```python
from ur_dashboard import AsyncDashboard
Common Methods
Query
state()
robotmode()
running()
programstate()
safetystatus()
get_loaded_program()
is_in_remote_control()
polyscope_version()
version()
get_serial_number()
get_robot_model()
get_operational_mode()
is_program_saved()
ping()
Action
power_on()
power_off()
brake_release()
load(path)
play()
stop()
pause()
popup(message)
close_popup()
close_safety_popup()
unlock_protective_stop()
restart_safety()
add_to_log(message)
set_operational_mode(mode)
clear_operational_mode()
load_installation(path)
shutdown()
raw(command)
Error Handling
python


from ur_dashboard import (
    SyncDashboard,
    DashboardCommunicationError,
    DashboardCommandRejected,
)
ur = None
try: ur = SyncDashboard("192.168.1.101") ur.seq_full_boot("/programs/main.urp")
except DashboardCommunicationError: print("Robot connection failed")
except DashboardCommandRejected as e: print(f"Command rejected: {e.raw_response}")
finally: if ur is not None: ur.close()



---

## Docs Build

### Build Sphinx docs locally

```bash
pip install -e ".[docs]"
cd docs
make html
Windows:
powershell


pip install -e ".[docs]"
cd docs
.\make.bat html
Notes
실제 장비에서는 반드시 안전 확인 후 사용하세요.
unlock_protective_stop()는 원인 제거 후 사용하세요.
e-Series는 일부 명령에서 Remote Control 모드가 필요합니다.
seq_ 메서드는 고정 시간 대기보다 상태 기반 제어를 우선합니다.
License
MIT License
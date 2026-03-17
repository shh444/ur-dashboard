# UR Dashboard

Universal Robots Dashboard Server(TCP 29999) 제어 패키지.

## 설치

```powershell
pip install -e .
```

웹 API 사용 시:

```powershell
pip install -e ".[api]"
```

## 사용법

```python
from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101") ur.seq_full_boot("/programs/main.urp") ur.close()



## 구조

```text
ur-dashboard/
├─ ur_dashboard/
│   ├─ __init__.py
│   ├─ client.py              # TCP 통신 코어
│   ├─ exceptions.py          # 예외
│   ├─ async_dashboard.py     # AsyncDashboard
│   ├─ sync_dashboard.py      # SyncDashboard + 시퀀스
│   └─ server.py              # FastAPI 웹 API
├─ sample_sync.py
├─ sample_async.py
├─ sample_web.py
├─ pyproject.toml
└─ README.md
Sync
python


from ur_dashboard import SyncDashboard
ur = SyncDashboard("192.168.1.101")
ur.state() # 전체 상태 ur.robotmode() # 로봇 모드 ur.safetystatus() # 안전 상태 ur.power_on() # 전원 ON ur.brake_release() # 브레이크 해제 ur.load("/programs/main.urp") ur.play() # 실행 ur.stop() # 정지
ur.seq_servo_on() # 서보 ON (알아서 처리) ur.seq_servo_off() # 서보 OFF ur.seq_start(path) # 프로그램 시작 ur.seq_error_reset() # 에러 초기화 ur.seq_full_boot(path) # 전체 부팅
ur.close()



## Async

```python
import asyncio
from ur_dashboard import AsyncDashboard
async def main(): ur = AsyncDashboard("192.168.1.101") await ur.connect() await ur.seq_full_boot("/programs/main.urp") await ur.close()
asyncio.run(main())



## Web API

```powershell
python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload
Swagger UI: http://127.0.0.1:8000/docs
명령 목록
조회
메서드	설명
state()	전체 상태
robotmode()	로봇 모드
running()	실행 여부
programstate()	프로그램 상태
safetystatus()	안전 상태
get_loaded_program()	로드된 프로그램
is_in_remote_control()	Remote Control 여부
polyscope_version()	PolyScope 버전
version()	소프트웨어 버전
get_serial_number()	시리얼 번호
get_robot_model()	로봇 모델
get_operational_mode()	운영 모드
is_program_saved()	저장 여부
ping()	연결 확인

Export as CSV
제어
메서드	설명
power_on()	전원 ON
power_off()	전원 OFF
brake_release()	브레이크 해제
load(path)	프로그램 로드
play()	실행
stop()	정지
pause()	일시정지
popup(msg)	팝업
close_popup()	팝업 닫기
close_safety_popup()	Safety 팝업 닫기
unlock_protective_stop()	보호정지 해제
restart_safety()	Safety 재시작
add_to_log(msg)	로그 추가
set_operational_mode(mode)	운영 모드 설정
clear_operational_mode()	운영 모드 해제
load_installation(path)	설치 파일 로드
shutdown()	시스템 종료
raw(cmd)	Raw 명령

Export as CSV
시퀀스
메서드	설명
seq_servo_on()	서보 ON
seq_servo_off()	서보 OFF
seq_start(path)	프로그램 시작
seq_error_reset()	에러 초기화
seq_full_boot(path)	전체 부팅

Export as CSV
에러 처리
python


from ur_dashboard import SyncDashboard, DashboardCommunicationError, DashboardCommandRejected
try: ur = SyncDashboard("192.168.1.101") ur.seq_full_boot("/programs/main.urp") except DashboardCommunicationError: print("연결 실패") except DashboardCommandRejected as e: print(f"명령 거부: {e.raw_response}") finally: ur.close()
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
print(ur.state()) # 전체 상태 조회 ur.seq_full_boot() # 에러 초기화 → 서보 ON → 프로그램 실행
ur.close()

기본 명령
ur.power_on() ur.brake_release() ur.load("/programs/main.urp") ur.play() ur.stop()
시퀀스 — 상태를 보고 알아서 처리
ur.seq_servo_on() # 서보 ON ur.seq_servo_off() # 서보 OFF ur.seq_start() # play ur.seq_start("/programs/main.urp") # load + play ur.seq_error_reset() # 에러 초기화 ur.seq_full_boot("/programs/main.urp") # 전체 부팅
ur.close()



### Async

```python
import asyncio
from ur_dashboard import AsyncDashboard
async def main(): ur = AsyncDashboard("192.168.1.101") await ur.connect() await ur.seq_full_boot("/programs/main.urp") await ur.close()
asyncio.run(main())



### Web API

```bash
pip install -e ".[api]"
python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload
Swagger UI: http://127.0.0.1:8000/docs
시퀀스
시퀀스는 현재 상태를 확인하고, 필요한 단계만 실행합니다.
고정 시간 대기가 아니라, Dashboard에서 상태를 폴링하여 완료를 확인합니다.
메서드	설명
seq_servo_on()	서보 ON (이미 켜져있으면 스킵)
seq_servo_off()	서보 OFF (이미 꺼져있으면 스킵)
seq_start(path?)	프로그램 실행 (서보 OFF면 자동으로 켬)
seq_error_reset()	에러 초기화 (정상이면 스킵)
seq_full_boot(path?)	에러 초기화 + 서보 ON + 프로그램 실행

Export as CSV
seq_full_boot 하나면 로봇이 어떤 상태에 있든 알아서 처리합니다:
text


seq_full_boot(path)
├─ seq_error_reset()      ← safety 이상 시에만
└─ seq_start(path)
    └─ seq_servo_on()     ← 서보 OFF 시에만
python


# 에러 상태 → 복구 → 서보 ON → 실행
# 이미 실행중 → 아무것도 안 함
# 서보만 꺼져있음 → 서보 ON → 실행
ur.seq_full_boot("/programs/main.urp")
결과 확인:
python


result = ur.seq_servo_on()
if result.ok: print("성공") else: print(f"실패: {result.stopped_at}")
print(result.summary())



```text
Sequence: SUCCESS
  ✓ Step 1: check_state
  ✓ Step 2: power_on
  ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING']) (5.5s)
  ✓ Step 4: brake_release
  ✓ Step 5: wait_until_robotmode(RUNNING) (3.2s)
  ✓ Step 6: check_state
전체 명령 목록
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
에러 처리
python


from ur_dashboard import SyncDashboard, DashboardCommunicationError, DashboardCommandRejected
try: ur = SyncDashboard("192.168.1.101") ur.seq_full_boot("/programs/main.urp") except DashboardCommunicationError: print("연결 실패") except DashboardCommandRejected as e: print(f"명령 거부: {e.raw_response}") finally: ur.close()



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

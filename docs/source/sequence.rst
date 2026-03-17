시퀀스 (Sequence)
=================

개념
----

시퀀스란 **미리 정해진 순서에 따라 각 단계별로 제어가 진행되는 방식** 입니다.

이 패키지의 시퀀스(``seq_`` 메서드)는 UR 로봇 제어에서 자주 쓰는 **복합 동작을
하나의 메서드로 묶은 것** 입니다.

핵심 원칙:

- **현재 상태를 먼저 확인** 한다
- **이미 완료된 단계는 건너뛴다**
- **각 단계 후 Dashboard에서 상태를 폴링** 하여 완료를 확인한다
- **실패하면 즉시 중단** 하고 결과를 반환한다

기존 방식(고정 시간 대기)과의 차이:

.. code-block:: text

   # 나쁜 예: 고정 시간 대기
   ur.power_on()
   time.sleep(5)          # 5초가 충분한지 알 수 없음
   ur.brake_release()
   time.sleep(3)          # 이미 끝났는데 3초를 더 기다림

   # 좋은 예: 상태 폴링
   ur.seq_servo_on()      # 내부에서 IDLE/RUNNING이 될 때까지만 대기


동작 원리
---------

모든 시퀀스는 내부적으로 동일한 패턴을 따릅니다.

.. code-block:: text

   1. 현재 상태 조회 (robotmode, safetystatus 등)
   2. 이미 목표 상태이면 → 즉시 반환 (스킵)
   3. 아니면 → 명령 전송 (power_on, brake_release 등)
   4. Dashboard에 주기적으로 상태 질의 (폴링)
   5. 목표 상태 도달 → 다음 단계로
   6. 타임아웃 초과 → 실패, 즉시 중단


폴링 방식
~~~~~~~~~

시퀀스 내부에서 상태 확인은 **폴링(polling)** 으로 동작합니다.

.. code-block:: text

   ┌─ 명령 전송 (예: power on) ─┐
   │                              │
   │   ┌── 0.5초 간격으로 ──┐    │
   │   │  robotmode 조회     │    │
   │   │  IDLE인가? → 아니오 │    │
   │   │  0.5초 대기         │    │
   │   │  robotmode 조회     │    │
   │   │  IDLE인가? → 아니오 │    │
   │   │  ...                │    │
   │   │  IDLE인가? → 예!    │    │
   │   └─────────────────────┘    │
   │                              │
   └─ 다음 단계로 ───────────────┘

기본 설정:

- **폴링 간격**: 0.5초
- **타임아웃**: 30초

둘 다 ``SyncDashboard`` 생성 시 변경 가능합니다:

.. code-block:: python

   ur = SyncDashboard("192.168.1.101", seq_timeout=60.0)


시퀀스 목록
-----------

seq_servo_on
~~~~~~~~~~~~

로봇 서보를 켭니다. **현재 상태에 따라 필요한 단계만 실행합니다.**

.. code-block:: text

   현재 상태 확인
   │
   ├─ RUNNING (이미 켜짐)
   │   └─ 아무것도 안 함 ✓
   │
   ├─ IDLE (전원 켜짐, 브레이크 잠김)
   │   └─ brake_release
   │       └─ RUNNING 될 때까지 폴링 ✓
   │
   └─ POWER_OFF / 기타
       ├─ power_on
       │   └─ IDLE 또는 RUNNING 될 때까지 폴링
       │
       ├─ (RUNNING이면 끝) ✓
       │
       └─ brake_release
           └─ RUNNING 될 때까지 폴링 ✓

사용:

.. code-block:: python

   ur.seq_servo_on()

출력 예시 — POWER_OFF에서 시작:

.. code-block:: text

   Sequence: SUCCESS
     ✓ Step 1: check_state
     ✓ Step 2: power_on
     ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING']) (5.5s)
     ✓ Step 4: brake_release
     ✓ Step 5: wait_until_robotmode(RUNNING) (3.2s)
     ✓ Step 6: check_state

출력 예시 — 이미 RUNNING:

.. code-block:: text

   Sequence: SUCCESS
     ✓ Step 1: check_state
     ✓ Step 2: expect_robotmode(RUNNING)


seq_servo_off
~~~~~~~~~~~~~

로봇 서보를 끕니다.

.. code-block:: text

   현재 상태 확인
   │
   ├─ POWER_OFF (이미 꺼짐)
   │   └─ 아무것도 안 함 ✓
   │
   └─ 그 외
       └─ power_off
           └─ POWER_OFF 될 때까지 폴링 ✓

사용:

.. code-block:: python

   ur.seq_servo_off()


seq_start
~~~~~~~~~

프로그램을 실행합니다. **서보가 안 켜져있으면 자동으로 켭니다.**

``program_path`` 를 넘기면 load도 하고, 안 넘기면 play만 합니다.

.. code-block:: text

   현재 상태 확인
   │
   ├─ 프로그램 이미 실행중
   │   └─ 아무것도 안 함 ✓
   │
   ├─ 서보 OFF (RUNNING 아님)
   │   ├─ seq_servo_on() 자동 실행
   │   │   └─ 실패하면 중단 ✗
   │   └─ (program_path 있으면 load) + play
   │       └─ 프로그램 실행 확인 폴링 ✓
   │
   └─ 서보 ON (RUNNING)
       └─ (program_path 있으면 load) + play
           └─ 프로그램 실행 확인 폴링 ✓

사용:

.. code-block:: python

   # 이미 로드된 프로그램 play만
   ur.seq_start()

   # 로드 + play
   ur.seq_start("/programs/main.urp")


seq_full_boot
~~~~~~~~~~~~~

**에러 초기화 → 서보 ON → 프로그램 실행** 을 한번에 합니다.

사용:

.. code-block:: python

   # play만
   ur.seq_full_boot()

   # 로드 + play
   ur.seq_full_boot("/programs/main.urp")


seq_error_reset
~~~~~~~~~~~~~~~

에러를 초기화합니다. **에러 종류에 따라 다른 복구 절차를 실행합니다.**

.. code-block:: text

   현재 safety 확인
   │
   ├─ NORMAL (정상)
   │   └─ 아무것도 안 함 ✓
   │
   ├─ PROTECTIVE_STOP
   │   ├─ safety popup 닫기
   │   ├─ popup 닫기
   │   ├─ 6초 대기 (UR 공식 요구사항: 최소 5초)
   │   ├─ unlock_protective_stop
   │   └─ NORMAL 될 때까지 폴링 ✓
   │
   └─ FAULT / VIOLATION / EMERGENCY 등
       ├─ safety popup 닫기
       ├─ popup 닫기
       ├─ restart_safety
       ├─ POWER_OFF 될 때까지 폴링
       └─ NORMAL 될 때까지 폴링 ✓

사용:

.. code-block:: python

   ur.seq_error_reset()

.. note::

   ``PROTECTIVE_STOP`` 의 경우 UR 공식 문서에 따라 최소 5초 대기가 필요합니다:

      *"Cannot unlock protective stop until 5s after occurrence.
      Always inspect cause of protective stop before unlocking"*


seq_full_boot
~~~~~~~~~~~~~

**에러 초기화 → 서보 ON → 프로그램 시작** 을 한번에 합니다.
모든 단계에서 현재 상태를 확인하고 필요한 것만 실행합니다.

.. code-block:: text

   현재 safety 확인
   │
   ├─ safety 이상 있음
   │   ├─ seq_error_reset() 자동 실행
   │   │   └─ 실패하면 중단 ✗
   │   └─ seq_start() 실행
   │       └─ (내부에서 seq_servo_on도 자동 실행)
   │
   └─ safety 정상
       └─ seq_start() 실행
           └─ (내부에서 seq_servo_on도 자동 실행)

사용:

.. code-block:: python

   ur.seq_full_boot("/programs/main.urp")

즉, 로봇이 어떤 상태에 있든 이 한 줄이면 됩니다:

.. code-block:: python

   # 에러 상태 → 정상 복구 → 서보 ON → 프로그램 실행
   # 이미 실행중 → 아무것도 안 함
   # 서보만 꺼져있음 → 서보 ON → 프로그램 실행
   ur.seq_full_boot("/programs/main.urp")

출력 예시 — 에러 상태에서 전체 부팅:

.. code-block:: text

   Sequence: SUCCESS
     ✓ Step 1: check_state
     ✓ Step 2: close_safety_popup
     ✓ Step 3: close_popup
     ✓ Step 4: restart_safety
     ✓ Step 5: wait_until_robotmode(POWER_OFF) (4.5s)
     ✓ Step 6: wait_until_safety(NORMAL) (2.1s)
     ✓ Step 7: check_state
     ✓ Step 8: power_on
     ✓ Step 9: wait_until_robotmode_any(['IDLE', 'RUNNING']) (6.2s)
     ✓ Step 10: brake_release
     ✓ Step 11: wait_until_robotmode(RUNNING) (3.8s)
     ✓ Step 12: check_state
     ✓ Step 13: load(/programs/main.urp)
     ✓ Step 14: play
     ✓ Step 15: wait_until_running(True) (1.2s)
     ✓ Step 16: check_state

출력 예시 — 이미 실행중:

.. code-block:: text

   Sequence: SUCCESS
     ✓ Step 1: check_state

출력 예시 — 실패:

.. code-block:: text

   Sequence: FAILED at 'wait_until_robotmode(RUNNING)'
     ✓ Step 1: check_state
     ✓ Step 2: power_on
     ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING']) (5.5s)
     ✓ Step 4: brake_release
     ✗ Step 5: wait_until_robotmode(RUNNING) — Timeout 30s. Expected RUNNING, last=IDLE


호출 관계
---------

시퀀스 메서드들은 서로를 호출합니다:

.. code-block:: text

   seq_full_boot(path)
   ├─ seq_error_reset()      ← safety 이상 시에만
   └─ seq_start(path)
       └─ seq_servo_on()     ← 서보 OFF 시에만

따라서 ``seq_full_boot`` 하나만 호출하면 내부에서 상태에 따라
``seq_error_reset``, ``seq_servo_on`` 이 자동으로 호출됩니다.


결과 확인
---------

모든 시퀀스는 ``SequenceResult`` 를 반환합니다.

.. code-block:: python

   result = ur.seq_servo_on()

   # 성공 여부
   if result.ok:
       print("성공")
   else:
       print(f"실패: {result.stopped_at}")

   # 상세 로그
   print(result.summary())

``SequenceResult`` 속성:

- ``ok``: 전체 성공 여부 (``bool``)
- ``stopped_at``: 실패한 스텝 이름 (``str | None``)
- ``steps``: 각 스텝 결과 리스트
- ``summary()``: 사람이 읽기 좋은 요약 문자열


UR Robot Mode 상태 전이
-----------------------

시퀀스를 이해하려면 UR 로봇의 상태 전이를 알아야 합니다.

.. code-block:: text

   POWER_OFF ──power on──→ BOOTING → POWER_ON → IDLE
                                                  │
                                          brake release
                                                  │
                                                  ▼
                                              RUNNING
                                                  │
                                              power off
                                                  │
                                                  ▼
                                              POWER_OFF

각 시퀀스가 하는 일:

.. code-block:: text

   seq_servo_on:   POWER_OFF → ··· → RUNNING
   seq_servo_off:  RUNNING   → ··· → POWER_OFF
   seq_start:      (any)     → ··· → RUNNING + 프로그램 실행
   seq_error_reset: (error)  → ··· → NORMAL safety
   seq_full_boot:  (any)     → ··· → RUNNING + 프로그램 실행


Safety Status 복구 경로
-----------------------

.. code-block:: text

   PROTECTIVE_STOP
   │
   ├─ 6초 대기
   ├─ unlock_protective_stop
   └─ NORMAL ✓

   FAULT / VIOLATION / EMERGENCY
   │
   ├─ close_safety_popup
   ├─ restart_safety
   ├─ → POWER_OFF (safety 재부팅)
   └─ → NORMAL ✓


커스텀 시퀀스
-------------

``DashboardSequence`` 를 직접 사용하면 커스텀 시퀀스를 만들 수 있습니다.

.. code-block:: python

   from ur_dashboard.sync_dashboard import DashboardSequence

   with SyncDashboard("192.168.1.101") as ur:
       result = (
           DashboardSequence(ur)
           .check_state()
           .close_safety_popup()
           .power_on()
           .wait_until_robotmode("IDLE", timeout=30)
           .brake_release()
           .wait_until_robotmode("RUNNING", timeout=30)
           .load("/programs/main.urp")
           .play()
           .wait_until_running(True, timeout=10)
           .check_state()
           .run()
       )
       print(result.summary())

사용 가능한 빌더 메서드:

**대기 (폴링)**

- ``.wait_until_robotmode(mode, timeout)``
- ``.wait_until_robotmode_any([modes], timeout)``
- ``.wait_until_safety(status, timeout)``
- ``.wait_until_running(bool, timeout)``
- ``.wait(seconds)`` — 고정 대기 (특수한 경우만)

**상태 확인**

- ``.check_state()`` — 현재 상태 기록 (항상 성공)
- ``.expect_robotmode(mode)`` — 모드 불일치 시 실패
- ``.expect_remote_control()`` — remote control 아니면 실패

**조건부 스킵**

- ``.skip_if_robotmode(mode, skip_count)`` — 조건 맞으면 다음 N스텝 건너뜀

**액션**

- ``.power_on()``, ``.power_off()``, ``.brake_release()``
- ``.play()``, ``.stop()``, ``.pause()``
- ``.load(path)``, ``.close_popup()``, ``.close_safety_popup()``
- ``.unlock_protective_stop()``, ``.restart_safety()``
- ``.raw(cmd)``

**실행**

- ``.run()`` — 파이프라인 실행, ``SequenceResult`` 반환

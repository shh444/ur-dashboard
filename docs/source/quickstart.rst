Quick Start
===========

설치
----

.. code-block:: bash

   pip install -e .

Sync 사용
---------

.. code-block:: python

   from ur_dashboard import SyncDashboard

   ur = SyncDashboard("192.168.1.101")

   # 상태 조회
   print(ur.state())
   print(ur.robotmode())

   # 제어
   ur.power_on()
   ur.brake_release()
   ur.load("/programs/main.urp")
   ur.play()

   # 시퀀스
   ur.seq_servo_on()
   ur.seq_full_boot("/programs/main.urp")

   ur.close()

Async 사용
----------

.. code-block:: python

   import asyncio
   from ur_dashboard import AsyncDashboard

   async def main():
       ur = AsyncDashboard("192.168.1.101")
       await ur.connect()
       await ur.seq_full_boot("/programs/main.urp")
       await ur.close()

   asyncio.run(main())

Web API
-------

.. code-block:: bash

   pip install -e ".[api]"
   python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload

Swagger UI: http://127.0.0.1:8000/docs

에러 처리
---------

.. code-block:: python

   from ur_dashboard import SyncDashboard, DashboardCommunicationError, DashboardCommandRejected

   try:
       ur = SyncDashboard("192.168.1.101")
       ur.seq_full_boot("/programs/main.urp")
   except DashboardCommunicationError:
       print("연결 실패")
   except DashboardCommandRejected as e:
       print(f"명령 거부: {e.raw_response}")
   finally:
       ur.close()

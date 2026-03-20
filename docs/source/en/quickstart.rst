Quick Start
===========

Installation
------------

.. code-block:: bash

   pip install -e .

Using Sync
----------

.. code-block:: python

   from ur_dashboard import SyncDashboard

   ur = SyncDashboard("192.168.1.101")

   # Query state
   print(ur.state())
   print(ur.robotmode())

   # Control
   ur.power_on()
   ur.brake_release()
   ur.load("/programs/main.urp")
   ur.play()

   # Sequences
   ur.seq_servo_on()
   ur.seq_full_boot("/programs/main.urp")

   ur.close()

Using Async
-----------

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

Error Handling
--------------

.. code-block:: python

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
       print("Connection failed")
   except DashboardCommandRejected as e:
       print(f"Command rejected: {e.raw_response}")
   finally:
       if ur is not None:
           ur.close()

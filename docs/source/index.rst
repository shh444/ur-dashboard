UR Dashboard
============

Universal Robots Dashboard Server(TCP 29999) 제어 패키지.

.. code-block:: python

   from ur_dashboard import SyncDashboard

   ur = SyncDashboard("192.168.1.101")
   ur.seq_full_boot()
   ur.close()

.. toctree::
   :maxdepth: 2
   :caption: Contents

   quickstart
   sequence
   api

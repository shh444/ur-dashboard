Sequence
========

Concept
-------

A sequence is **a control flow that executes each step in a predefined order**.

In this package, sequence methods (``seq_`` methods) bundle **compound operations that
are commonly used in UR robot control into a single method**.

Core principles:

- **Check the current state first**
- **Skip steps that are already complete**
- **Poll the Dashboard after each step** to confirm completion
- **Stop immediately on failure** and return the result

Difference from the old fixed-wait approach:

.. code-block:: text

   # Bad example: fixed delays
   ur.power_on()
   time.sleep(5)          # No guarantee that 5 seconds is enough
   ur.brake_release()
   time.sleep(3)          # The robot may already be ready, but you still wait

   # Good example: state polling
   ur.seq_servo_on()      # Internally waits only until IDLE/RUNNING is reached

How it works
------------

All sequences follow the same internal pattern.

.. code-block:: text

   1. Query current state (robotmode, safetystatus, etc.)
   2. If already at the target state -> return immediately (skip)
   3. Otherwise -> send command (power_on, brake_release, etc.)
   4. Poll the Dashboard periodically
   5. When the target state is reached -> continue to the next step
   6. If the timeout expires -> fail and stop immediately

Polling
~~~~~~~

State checks inside sequences use **polling**.

.. code-block:: text

   ┌─ Send command (example: power on) ─┐
   │                                    │
   │   ┌── every 0.5 seconds ───────┐   │
   │   │  query robotmode           │   │
   │   │  is it IDLE? -> no         │   │
   │   │  wait 0.5 seconds          │   │
   │   │  query robotmode           │   │
   │   │  is it IDLE? -> no         │   │
   │   │  ...                       │   │
   │   │  is it IDLE? -> yes!       │   │
   │   └────────────────────────────┘   │
   │                                    │
   └─ Move to the next step ────────────┘

Default settings:

- **Polling interval**: 0.5 seconds
- **Timeout**: 30 seconds

You can change both when creating ``SyncDashboard``:

.. code-block:: python

   ur = SyncDashboard("192.168.1.101", seq_timeout=60.0)

Sequence list
-------------

seq_servo_on
~~~~~~~~~~~~

Turns the robot servo on. **Only the required steps are executed based on the current state.**

.. code-block:: text

   Check current state
   │
   ├─ RUNNING (already on)
   │   └─ do nothing ✓
   │
   ├─ IDLE (power on, brake locked)
   │   └─ brake_release
   │       └─ poll until RUNNING ✓
   │
   └─ POWER_OFF / others
       ├─ power_on
       │   └─ poll until IDLE or RUNNING
       │
       ├─ (if RUNNING, finish) ✓
       │
       └─ brake_release
           └─ poll until RUNNING ✓

Usage:

.. code-block:: python

   ur.seq_servo_on()

Example output — starting from POWER_OFF:

.. code-block:: text

   Sequence: SUCCESS
     ✓ Step 1: check_state
     ✓ Step 2: power_on
     ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING']) (5.5s)
     ✓ Step 4: brake_release
     ✓ Step 5: wait_until_robotmode(RUNNING) (3.2s)
     ✓ Step 6: check_state

Example output — already RUNNING:

.. code-block:: text

   Sequence: SUCCESS
     ✓ Step 1: check_state
     ✓ Step 2: expect_robotmode(RUNNING)

seq_servo_off
~~~~~~~~~~~~~

Turns the robot servo off.

.. code-block:: text

   Check current state
   │
   ├─ POWER_OFF (already off)
   │   └─ do nothing ✓
   │
   └─ anything else
       └─ power_off
           └─ poll until POWER_OFF ✓

Usage:

.. code-block:: python

   ur.seq_servo_off()

seq_start
~~~~~~~~~

Starts a program. **If the servo is not on, it is turned on automatically.**

If you pass ``program_path``, the program is loaded first. If you omit it, only ``play`` is executed.

.. code-block:: text

   Check current state
   │
   ├─ program already running
   │   └─ do nothing ✓
   │
   ├─ servo OFF (not RUNNING)
   │   ├─ run seq_servo_on() automatically
   │   │   └─ stop if it fails ✗
   │   └─ (load if program_path exists) + play
   │       └─ poll until program is running ✓
   │
   └─ servo ON (RUNNING)
       └─ (load if program_path exists) + play
           └─ poll until program is running ✓

Usage:

.. code-block:: python

   # Only play the already loaded program
   ur.seq_start()

   # Load + play
   ur.seq_start("/programs/main.urp")

seq_error_reset
~~~~~~~~~~~~~~~

Resets errors. **Different recovery procedures are executed depending on the error type.**

.. code-block:: text

   Check current safety state
   │
   ├─ NORMAL
   │   └─ do nothing ✓
   │
   ├─ PROTECTIVE_STOP
   │   ├─ close safety popup
   │   ├─ close popup
   │   ├─ wait 6 seconds (UR official requirement: at least 5 seconds)
   │   ├─ unlock_protective_stop
   │   └─ poll until NORMAL ✓
   │
   └─ FAULT / VIOLATION / EMERGENCY / etc.
       ├─ close safety popup
       ├─ close popup
       ├─ restart_safety
       ├─ poll until POWER_OFF
       └─ poll until NORMAL ✓

Usage:

.. code-block:: python

   ur.seq_error_reset()

.. note::

   For ``PROTECTIVE_STOP``, UR documentation requires a wait of at least 5 seconds:

      *"Cannot unlock protective stop until 5s after occurrence.
      Always inspect cause of protective stop before unlocking"*

seq_full_boot
~~~~~~~~~~~~~

Performs **error reset -> servo ON -> program start** in one call.
It checks the current state at every stage and only executes what is necessary.

.. code-block:: text

   Check current safety state
   │
   ├─ safety issue exists
   │   ├─ run seq_error_reset() automatically
   │   │   └─ stop if it fails ✗
   │   └─ run seq_start()
   │       └─ (seq_servo_on is also called automatically inside)
   │
   └─ safety is normal
       └─ run seq_start()
           └─ (seq_servo_on is also called automatically inside)

Usage:

.. code-block:: python

   ur.seq_full_boot("/programs/main.urp")

In other words, no matter what state the robot is in, this one line is enough:

.. code-block:: python

   # Error state -> recover -> servo ON -> start program
   # Already running -> do nothing
   # Servo only is off -> servo ON -> start program
   ur.seq_full_boot("/programs/main.urp")

Example output — full boot from an error state:

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

Example output — already running:

.. code-block:: text

   Sequence: SUCCESS
     ✓ Step 1: check_state

Example output — failure:

.. code-block:: text

   Sequence: FAILED at 'wait_until_robotmode(RUNNING)'
     ✓ Step 1: check_state
     ✓ Step 2: power_on
     ✓ Step 3: wait_until_robotmode_any(['IDLE', 'RUNNING']) (5.5s)
     ✓ Step 4: brake_release
     ✗ Step 5: wait_until_robotmode(RUNNING) — Timeout 30s. Expected RUNNING, last=IDLE

Call relationships
------------------

Sequence methods call each other like this:

.. code-block:: text

   seq_full_boot(path)
   ├─ seq_error_reset()      ← only when safety is abnormal
   └─ seq_start(path)
       └─ seq_servo_on()     ← only when the servo is off

So if you call only ``seq_full_boot``, it will automatically call
``seq_error_reset`` and ``seq_servo_on`` as needed.

Checking results
----------------

All sequences return ``SequenceResult``.

.. code-block:: python

   result = ur.seq_servo_on()

   # Success or failure
   if result.ok:
       print("Success")
   else:
       print(f"Failed: {result.stopped_at}")

   # Detailed log
   print(result.summary())

``SequenceResult`` fields:

- ``ok``: overall success (``bool``)
- ``stopped_at``: name of the step where it failed (``str | None``)
- ``steps``: list of step results
- ``summary()``: human-readable summary string

UR Robot Mode transitions
-------------------------

To understand the sequences, it helps to understand UR robot mode transitions.

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

What each sequence does:

.. code-block:: text

   seq_servo_on:    POWER_OFF → ··· → RUNNING
   seq_servo_off:   RUNNING   → ··· → POWER_OFF
   seq_start:       (any)     → ··· → RUNNING + program execution
   seq_error_reset: (error)   → ··· → NORMAL safety
   seq_full_boot:   (any)     → ··· → RUNNING + program execution

Safety Status recovery path
---------------------------

.. code-block:: text

   PROTECTIVE_STOP
   │
   ├─ wait 6 seconds
   ├─ unlock_protective_stop
   └─ NORMAL ✓

   FAULT / VIOLATION / EMERGENCY
   │
   ├─ close_safety_popup
   ├─ restart_safety
   ├─ → POWER_OFF (safety reboot)
   └─ → NORMAL ✓

Custom sequences
----------------

You can build your own sequence directly with ``DashboardSequence``.

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

Available builder methods:

**Wait (polling)**

- ``.wait_until_robotmode(mode, timeout)``
- ``.wait_until_robotmode_any([modes], timeout)``
- ``.wait_until_safety(status, timeout)``
- ``.wait_until_running(bool, timeout)``
- ``.wait(seconds)`` — fixed wait (only for special cases)

**State checks**

- ``.check_state()`` — records current state (always succeeds)
- ``.expect_robotmode(mode)`` — fails if the mode does not match
- ``.expect_remote_control()`` — fails unless remote control is enabled

**Conditional skips**

- ``.skip_if_robotmode(mode, skip_count)`` — skip the next N steps if the condition matches

**Actions**

- ``.power_on()``, ``.power_off()``, ``.brake_release()``
- ``.play()``, ``.stop()``, ``.pause()``
- ``.load(path)``, ``.close_popup()``, ``.close_safety_popup()``
- ``.unlock_protective_stop()``, ``.restart_safety()``
- ``.raw(cmd)``

**Execution**

- ``.run()`` — executes the pipeline and returns ``SequenceResult``

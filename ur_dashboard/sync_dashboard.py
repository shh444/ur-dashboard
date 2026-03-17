"""
UR Dashboard 동기(sync) 클래스.

    from ur_dashboard import SyncDashboard

    ur = SyncDashboard("192.168.1.101")
    ur.seq_full_boot("/programs/main.urp")
    ur.close()
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Callable

from .async_dashboard import AsyncDashboard
from .client import DashboardResponse, RobotState

logger = logging.getLogger(__name__)


def _to_dict(v: Any) -> Any:
    if is_dataclass(v) and not isinstance(v, type):
        return asdict(v)
    if isinstance(v, list):
        return [_to_dict(i) for i in v]
    return v


# =================================================================
# Sequence Engine
# =================================================================

@dataclass
class StepResult:
    step_name: str
    ok: bool
    data: Any = None
    error: str | None = None
    skipped: bool = False


@dataclass
class SequenceResult:
    ok: bool
    steps: list[StepResult] = field(default_factory=list)
    stopped_at: str | None = None

    def summary(self) -> str:
        lines = []
        for i, s in enumerate(self.steps, 1):
            icon = "✓" if s.ok else ("⊘" if s.skipped else "✗")
            line = f"  {icon} Step {i}: {s.step_name}"
            if s.error:
                line += f" — {s.error}"
            if s.data and isinstance(s.data, dict):
                elapsed = s.data.get("elapsed")
                if elapsed is not None:
                    line += f" ({elapsed:.1f}s)"
            lines.append(line)
        status = "SUCCESS" if self.ok else f"FAILED at '{self.stopped_at}'"
        lines.insert(0, f"Sequence: {status}")
        return "\n".join(lines)


class DashboardSequence:

    DEFAULT_TIMEOUT = 30.0
    DEFAULT_POLL = 0.5

    def __init__(self, robot) -> None:
        self._robot = robot
        self._steps: list[tuple[str, Callable]] = []

    def _add(self, name: str, fn: Callable) -> "DashboardSequence":
        self._steps.append((name, fn))
        return self

    # --- Wait ---

    def wait(self, seconds: float) -> "DashboardSequence":
        def _w():
            time.sleep(seconds)
            return StepResult(step_name=f"wait({seconds}s)", ok=True)
        return self._add(f"wait({seconds}s)", _w)

    # --- Polling ---

    def _poll(self, name, query_fn, key, check_fn, desc, timeout, interval):
        start = time.time()
        last = None
        while True:
            elapsed = time.time() - start
            try:
                last = query_fn().get("data", {}).get(key)
            except Exception as e:
                last = f"ERROR: {e}"
            if check_fn(last):
                return StepResult(name, True, {"expected": desc, "actual": last, "elapsed": elapsed})
            if elapsed >= timeout:
                return StepResult(name, False, {"expected": desc, "actual": last, "elapsed": elapsed},
                                  error=f"Timeout {timeout}s. Expected {desc}, last={last}")
            time.sleep(interval)

    def wait_until_robotmode(self, expected, timeout=DEFAULT_TIMEOUT, interval=DEFAULT_POLL):
        name = f"wait_until_robotmode({expected})"
        def _do():
            return self._poll(name, self._robot.robotmode, "robot_mode",
                              lambda v: isinstance(v, str) and v.strip().upper() == expected.upper(),
                              expected, timeout, interval)
        return self._add(name, _do)

    def wait_until_robotmode_any(self, modes, timeout=DEFAULT_TIMEOUT, interval=DEFAULT_POLL):
        upper = [m.upper() for m in modes]
        name = f"wait_until_robotmode_any({modes})"
        def _do():
            return self._poll(name, self._robot.robotmode, "robot_mode",
                              lambda v: isinstance(v, str) and v.strip().upper() in upper,
                              f"one of {modes}", timeout, interval)
        return self._add(name, _do)

    def wait_until_safety(self, expected, timeout=DEFAULT_TIMEOUT, interval=DEFAULT_POLL):
        name = f"wait_until_safety({expected})"
        def _do():
            return self._poll(name, self._robot.safetystatus, "safety_status",
                              lambda v: isinstance(v, str) and v.strip().upper() == expected.upper(),
                              expected, timeout, interval)
        return self._add(name, _do)

    def wait_until_running(self, expected=True, timeout=DEFAULT_TIMEOUT, interval=DEFAULT_POLL):
        name = f"wait_until_running({expected})"
        def _do():
            return self._poll(name, self._robot.running, "program_running",
                              lambda v: v == expected, str(expected), timeout, interval)
        return self._add(name, _do)

    # --- Instant checks ---

    def expect_robotmode(self, expected):
        def _c():
            actual = self._robot.robotmode().get("data", {}).get("robot_mode", "").strip()
            ok = actual.upper() == expected.upper()
            return StepResult(f"expect_robotmode({expected})", ok,
                              {"expected": expected, "actual": actual},
                              error=None if ok else f"Expected {expected}, got {actual}")
        return self._add(f"expect_robotmode({expected})", _c)

    def expect_remote_control(self):
        def _c():
            rc = self._robot.is_in_remote_control().get("data", {}).get("remote_control")
            return StepResult("expect_remote_control", bool(rc),
                              {"remote_control": rc},
                              error=None if rc else "Not in remote control")
        return self._add("expect_remote_control", _c)

    def check_state(self):
        def _c():
            state = self._robot.state()
            return StepResult("check_state", True, state)
        return self._add("check_state", _c)

    # --- Skip ---

    def skip_if_robotmode(self, mode, skip_count=1):
        def _c():
            actual = self._robot.robotmode().get("data", {}).get("robot_mode", "").strip().upper()
            skip = actual == mode.upper()
            return StepResult(f"skip_if_robotmode({mode})", True,
                              {"actual": actual, "skip": skip, "skip_count": skip_count})
        return self._add(f"skip_if_robotmode({mode})", _c)

    # --- Actions ---

    def _act(self, name, fn):
        def _do():
            try:
                return StepResult(name, True, fn())
            except Exception as e:
                return StepResult(name, False, error=str(e))
        return self._add(name, _do)

    def power_on(self):               return self._act("power_on", self._robot.power_on)
    def power_off(self):              return self._act("power_off", self._robot.power_off)
    def brake_release(self):          return self._act("brake_release", self._robot.brake_release)
    def play(self):                   return self._act("play", self._robot.play)
    def stop(self):                   return self._act("stop", self._robot.stop)
    def pause(self):                  return self._act("pause", self._robot.pause)
    def close_popup(self):            return self._act("close_popup", self._robot.close_popup)
    def close_safety_popup(self):     return self._act("close_safety_popup", self._robot.close_safety_popup)
    def unlock_protective_stop(self): return self._act("unlock_protective_stop", self._robot.unlock_protective_stop)
    def restart_safety(self):         return self._act("restart_safety", self._robot.restart_safety)
    def shutdown(self):               return self._act("shutdown", self._robot.shutdown)
    def load(self, p):                return self._act(f"load({p})", lambda: self._robot.load(p))
    def popup(self, m):               return self._act(f"popup({m})", lambda: self._robot.popup(m))
    def raw(self, c):                 return self._act(f"raw({c})", lambda: self._robot.raw(c))

    # --- Run ---

    def run(self) -> SequenceResult:
        results = SequenceResult(ok=True)
        skip = 0
        for i, (name, fn) in enumerate(self._steps):
            if skip > 0:
                skip -= 1
                results.steps.append(StepResult(name, True, skipped=True))
                continue
            try:
                step = fn()
            except Exception as e:
                step = StepResult(name, False, error=str(e))
            results.steps.append(step)
            if step.ok and step.data and isinstance(step.data, dict) and step.data.get("skip"):
                skip = step.data.get("skip_count", 1)
            if not step.ok:
                results.ok = False
                results.stopped_at = name
                break
        self._steps.clear()
        return results


# =================================================================
# SyncDashboard
# =================================================================

class SyncDashboard:

    def __init__(
        self,
        host: str,
        port: int = 29999,
        *,
        connect_timeout: float = 3.0,
        command_timeout: float = 5.0,
        lazy: bool = False,
        auto_connect: bool = True,
        seq_timeout: float = 30.0,
    ) -> None:
        self._loop = asyncio.new_event_loop()
        self._a = AsyncDashboard(
            host=host, port=port,
            connect_timeout=connect_timeout,
            command_timeout=command_timeout,
            lazy=lazy,
        )
        self._seq_timeout = seq_timeout
        if auto_connect:
            self._run(self._a.connect())

    def _run(self, coro):
        return self._loop.run_until_complete(coro)

    def __enter__(self):  return self
    def __exit__(self, *a): self.close()
    def __repr__(self):   return f"SyncDashboard({self._a!r})"

    # --- Connection ---
    def connect(self):          self._run(self._a.connect())
    def close(self):
        try: self._run(self._a.close())
        finally: self._loop.close()
    def ping(self) -> bool:     return self._run(self._a.ping())

    @property
    def is_connected(self): return self._a.is_connected
    @property
    def greeting(self):     return self._a.greeting

    # --- Query ---
    def state(self) -> dict:                return _to_dict(self._run(self._a.state()))
    def running(self) -> dict:              return _to_dict(self._run(self._a.running()))
    def robotmode(self) -> dict:            return _to_dict(self._run(self._a.robotmode()))
    def get_loaded_program(self) -> dict:   return _to_dict(self._run(self._a.get_loaded_program()))
    def programstate(self) -> dict:         return _to_dict(self._run(self._a.programstate()))
    def polyscope_version(self) -> dict:    return _to_dict(self._run(self._a.polyscope_version()))
    def version(self) -> dict:              return _to_dict(self._run(self._a.version()))
    def safetystatus(self) -> dict:         return _to_dict(self._run(self._a.safetystatus()))
    def get_serial_number(self) -> dict:    return _to_dict(self._run(self._a.get_serial_number()))
    def get_robot_model(self) -> dict:      return _to_dict(self._run(self._a.get_robot_model()))
    def is_in_remote_control(self) -> dict: return _to_dict(self._run(self._a.is_in_remote_control()))
    def is_program_saved(self) -> dict:     return _to_dict(self._run(self._a.is_program_saved()))
    def get_operational_mode(self) -> dict: return _to_dict(self._run(self._a.get_operational_mode()))

    # --- Action ---
    def load(self, p) -> dict:              return _to_dict(self._run(self._a.load(p)))
    def play(self) -> dict:                 return _to_dict(self._run(self._a.play()))
    def stop(self) -> dict:                 return _to_dict(self._run(self._a.stop()))
    def pause(self) -> dict:                return _to_dict(self._run(self._a.pause()))
    def power_on(self) -> dict:             return _to_dict(self._run(self._a.power_on()))
    def power_off(self) -> dict:            return _to_dict(self._run(self._a.power_off()))
    def brake_release(self) -> dict:        return _to_dict(self._run(self._a.brake_release()))
    def shutdown(self) -> dict:             return _to_dict(self._run(self._a.shutdown()))
    def popup(self, m) -> dict:             return _to_dict(self._run(self._a.popup(m)))
    def close_popup(self) -> dict:          return _to_dict(self._run(self._a.close_popup()))
    def close_safety_popup(self) -> dict:   return _to_dict(self._run(self._a.close_safety_popup()))
    def unlock_protective_stop(self) -> dict: return _to_dict(self._run(self._a.unlock_protective_stop()))
    def add_to_log(self, m) -> dict:        return _to_dict(self._run(self._a.add_to_log(m)))
    def raw(self, c) -> dict:               return _to_dict(self._run(self._a.raw(c)))
    def restart_safety(self) -> dict:       return _to_dict(self._run(self._a.restart_safety()))
    def set_operational_mode(self, m) -> dict: return _to_dict(self._run(self._a.set_operational_mode(m)))
    def clear_operational_mode(self) -> dict:  return _to_dict(self._run(self._a.clear_operational_mode()))
    def load_installation(self, p) -> dict:    return _to_dict(self._run(self._a.load_installation(p)))
    def generate_flight_report(self, t="system") -> dict: return _to_dict(self._run(self._a.generate_flight_report(t)))
    def generate_support_file(self, d) -> dict: return _to_dict(self._run(self._a.generate_support_file(d)))

    # --- Sequence helpers ---

    def _get_mode(self) -> str:
        return (self.robotmode().get("data", {}).get("robot_mode") or "").strip().upper()

    def _get_safety(self) -> str:
        return (self.safetystatus().get("data", {}).get("safety_status") or "").strip().upper()

    def _is_running(self) -> bool:
        return self.running().get("data", {}).get("program_running") is True

    def _has_safety_issue(self) -> bool:
        return self._get_safety() not in ("NORMAL", "REDUCED", "")

    # --- Sequences ---

    def seq_servo_on(self) -> SequenceResult:
        mode = self._get_mode()
        t = self._seq_timeout
        seq = DashboardSequence(self).check_state()

        if mode == "RUNNING":
            return seq.expect_robotmode("RUNNING").run()
        if mode == "IDLE":
            return seq.brake_release().wait_until_robotmode("RUNNING", timeout=t).check_state().run()

        return (seq.power_on()
                .wait_until_robotmode_any(["IDLE", "RUNNING"], timeout=t)
                .skip_if_robotmode("RUNNING", skip_count=2)
                .brake_release()
                .wait_until_robotmode("RUNNING", timeout=t)
                .check_state().run())

    def seq_servo_off(self) -> SequenceResult:
        mode = self._get_mode()
        t = self._seq_timeout
        seq = DashboardSequence(self).check_state()

        if mode == "POWER_OFF":
            return seq.expect_robotmode("POWER_OFF").run()

        return seq.power_off().wait_until_robotmode("POWER_OFF", timeout=t).check_state().run()

    def seq_error_reset(self) -> SequenceResult:
        safety = self._get_safety()
        t = self._seq_timeout
        seq = DashboardSequence(self).check_state()

        if not self._has_safety_issue():
            return seq.run()

        seq.close_safety_popup().close_popup()

        if safety == "PROTECTIVE_STOP":
            return (seq.wait(6.0).unlock_protective_stop()
                    .wait_until_safety("NORMAL", timeout=t).check_state().run())

        return (seq.restart_safety()
                .wait_until_robotmode("POWER_OFF", timeout=t)
                .wait_until_safety("NORMAL", timeout=t)
                .check_state().run())

    def seq_start(self, program_path: str | None = None) -> SequenceResult:
        mode = self._get_mode()
        t = self._seq_timeout

        if self._is_running():
            return DashboardSequence(self).check_state().run()
        if mode != "RUNNING":
            result = self.seq_servo_on()
            if not result.ok:
                return result

        seq = DashboardSequence(self).check_state()
        if program_path:
            seq.load(program_path)
        return seq.play().wait_until_running(True, timeout=t).check_state().run()
    
    def seq_full_boot(self, program_path: str | None = None) -> SequenceResult:
        if self._has_safety_issue():
            result = self.seq_error_reset()
            if not result.ok:
                return result
        return self.seq_start(program_path)

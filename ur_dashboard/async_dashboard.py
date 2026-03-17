from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict, dataclass, is_dataclass

from .client import DashboardResponse, RobotState, URDashboardClient

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BootResult:
    steps: list[DashboardResponse]
    final_state: RobotState


class AsyncDashboard:

    def __init__(
        self,
        host: str,
        port: int = 29999,
        *,
        connect_timeout: float = 3.0,
        command_timeout: float = 5.0,
        lazy: bool = False,
        seq_timeout: float = 30.0,
        seq_poll_interval: float = 0.5,
    ) -> None:
        self._client = URDashboardClient(
            host=host, port=port,
            connect_timeout=connect_timeout,
            command_timeout=command_timeout,
        )
        self._lazy = lazy
        self._seq_timeout = seq_timeout
        self._seq_poll_interval = seq_poll_interval

    def __repr__(self) -> str:
        m = "lazy" if self._lazy else "persistent"
        return f"AsyncDashboard({self._client!r}, {m})"

    @property
    def is_connected(self) -> bool: return self._client.is_connected
    @property
    def greeting(self) -> str | None: return self._client.greeting

    async def __aenter__(self): await self.connect(); return self
    async def __aexit__(self, *a): await self.close()

    async def connect(self):
        if self._lazy:
            logger.info("Lazy mode: skip startup connect.")
            return
        await self._client.connect()

    async def close(self): await self._client.close()

    # ==================================================================
    # Basic commands
    # ==================================================================

    async def state(self) -> RobotState:             return await self._client.snapshot()
    async def ping(self) -> bool:                    return await self._client.ping()
    async def raw(self, cmd: str) -> DashboardResponse: return await self._client.raw(cmd)

    async def load(self, path: str) -> DashboardResponse:  return await self._client.load(path)
    async def play(self) -> DashboardResponse:              return await self._client.play()
    async def stop(self) -> DashboardResponse:              return await self._client.stop()
    async def pause(self) -> DashboardResponse:             return await self._client.pause()
    async def power_on(self) -> DashboardResponse:          return await self._client.power_on()
    async def power_off(self) -> DashboardResponse:         return await self._client.power_off()
    async def brake_release(self) -> DashboardResponse:     return await self._client.brake_release()
    async def shutdown(self) -> DashboardResponse:          return await self._client.shutdown()
    async def quit(self) -> DashboardResponse:              return await self._client.quit()

    async def running(self) -> DashboardResponse:           return await self._client.running()
    async def robotmode(self) -> DashboardResponse:         return await self._client.robotmode()
    async def get_loaded_program(self) -> DashboardResponse: return await self._client.get_loaded_program()
    async def programstate(self) -> DashboardResponse:      return await self._client.programstate()
    async def polyscope_version(self) -> DashboardResponse: return await self._client.polyscope_version()
    async def version(self) -> DashboardResponse:           return await self._client.version()
    async def safetystatus(self) -> DashboardResponse:      return await self._client.safetystatus()
    async def get_serial_number(self) -> DashboardResponse: return await self._client.get_serial_number()
    async def get_robot_model(self) -> DashboardResponse:   return await self._client.get_robot_model()
    async def is_in_remote_control(self) -> DashboardResponse: return await self._client.is_in_remote_control()
    async def is_program_saved(self) -> DashboardResponse:  return await self._client.is_program_saved()
    async def get_operational_mode(self) -> DashboardResponse: return await self._client.get_operational_mode()

    async def popup(self, msg: str) -> DashboardResponse:   return await self._client.popup(msg)
    async def close_popup(self) -> DashboardResponse:       return await self._client.close_popup()
    async def close_safety_popup(self) -> DashboardResponse: return await self._client.close_safety_popup()
    async def add_to_log(self, msg: str) -> DashboardResponse: return await self._client.add_to_log(msg)
    async def unlock_protective_stop(self) -> DashboardResponse: return await self._client.unlock_protective_stop()
    async def restart_safety(self) -> DashboardResponse:    return await self._client.restart_safety()
    async def set_operational_mode(self, mode: str) -> DashboardResponse: return await self._client.set_operational_mode(mode)
    async def clear_operational_mode(self) -> DashboardResponse: return await self._client.clear_operational_mode()
    async def load_installation(self, path: str) -> DashboardResponse: return await self._client.load_installation(path)
    async def generate_flight_report(self, t: str = "system") -> DashboardResponse: return await self._client.generate_flight_report(t)
    async def generate_support_file(self, d: str) -> DashboardResponse: return await self._client.generate_support_file(d)

    # ==================================================================
    # Internal helpers for sequences
    # ==================================================================

    async def _get_mode(self) -> str:
        r = await self.robotmode()
        return (r.data.get("robot_mode") or "").strip().upper()

    async def _get_safety(self) -> str:
        r = await self.safetystatus()
        return (r.data.get("safety_status") or "").strip().upper()

    async def _is_program_running(self) -> bool:
        r = await self.running()
        return r.data.get("program_running") is True

    async def _has_safety_issue(self) -> bool:
        return (await self._get_safety()) not in ("NORMAL", "REDUCED", "")

    async def _poll_until(
        self, query_fn, data_key: str, expected, timeout: float = None,
    ) -> dict:
        timeout = timeout or self._seq_timeout
        interval = self._seq_poll_interval
        start = time.time()

        while True:
            elapsed = time.time() - start
            result = await query_fn()
            value = result.data.get(data_key)

            if isinstance(expected, list):
                ok = isinstance(value, str) and value.strip().upper() in [e.upper() for e in expected]
            elif isinstance(expected, bool):
                ok = value == expected
            else:
                ok = isinstance(value, str) and value.strip().upper() == str(expected).upper()

            if ok:
                return {"ok": True, "value": value, "elapsed": round(elapsed, 1)}
            if elapsed >= timeout:
                return {"ok": False, "value": value, "elapsed": round(elapsed, 1),
                        "error": f"Timeout {timeout}s. Expected {expected}, got {value}"}

            await asyncio.sleep(interval)

    # ==================================================================
    # Sequence commands (seq_ 접두어)
    # ==================================================================

    async def seq_servo_on(self) -> dict:
        """
        서보 ON.
        RUNNING → 스킵 / IDLE → brake만 / 그 외 → power + brake
        """
        mode = await self._get_mode()
        steps = [{"step": "check_mode", "ok": True, "mode": mode}]
        logger.info("seq_servo_on: mode=%s", mode)

        if mode == "RUNNING":
            steps.append({"step": "skip", "ok": True, "reason": "already RUNNING"})
            return {"ok": True, "steps": steps}

        if mode == "IDLE":
            await self.brake_release()
            steps.append({"step": "brake_release", "ok": True})
            poll = await self._poll_until(self.robotmode, "robot_mode", "RUNNING")
            steps.append({"step": "wait_RUNNING", **poll})
            return {"ok": poll["ok"], "steps": steps, "error": poll.get("error")}

        await self.power_on()
        steps.append({"step": "power_on", "ok": True})

        poll = await self._poll_until(self.robotmode, "robot_mode", ["IDLE", "RUNNING"])
        steps.append({"step": "wait_IDLE_or_RUNNING", **poll})
        if not poll["ok"]:
            return {"ok": False, "steps": steps, "error": poll["error"]}

        if poll["value"].strip().upper() == "RUNNING":
            return {"ok": True, "steps": steps}

        await self.brake_release()
        steps.append({"step": "brake_release", "ok": True})
        poll = await self._poll_until(self.robotmode, "robot_mode", "RUNNING")
        steps.append({"step": "wait_RUNNING", **poll})
        return {"ok": poll["ok"], "steps": steps, "error": poll.get("error")}

    async def seq_servo_off(self) -> dict:
        """서보 OFF. POWER_OFF → 스킵 / 그 외 → power off"""
        mode = await self._get_mode()
        steps = [{"step": "check_mode", "ok": True, "mode": mode}]
        logger.info("seq_servo_off: mode=%s", mode)

        if mode == "POWER_OFF":
            steps.append({"step": "skip", "ok": True, "reason": "already POWER_OFF"})
            return {"ok": True, "steps": steps}

        await self.power_off()
        steps.append({"step": "power_off", "ok": True})
        poll = await self._poll_until(self.robotmode, "robot_mode", "POWER_OFF")
        steps.append({"step": "wait_POWER_OFF", **poll})
        return {"ok": poll["ok"], "steps": steps, "error": poll.get("error")}

    async def seq_error_reset(self) -> dict:
        """에러 초기화. NORMAL → 스킵 / PROTECTIVE_STOP → unlock / 그 외 → restart"""
        safety = await self._get_safety()
        steps = [{"step": "check_safety", "ok": True, "safety": safety}]
        logger.info("seq_error_reset: safety=%s", safety)

        if safety in ("NORMAL", "REDUCED", ""):
            steps.append({"step": "skip", "ok": True, "reason": "already NORMAL"})
            return {"ok": True, "steps": steps}

        try: await self.close_safety_popup(); steps.append({"step": "close_safety_popup", "ok": True})
        except: steps.append({"step": "close_safety_popup", "ok": True, "note": "ignored"})
        try: await self.close_popup(); steps.append({"step": "close_popup", "ok": True})
        except: steps.append({"step": "close_popup", "ok": True, "note": "ignored"})

        if safety == "PROTECTIVE_STOP":
            await asyncio.sleep(6.0)
            steps.append({"step": "wait(6s)", "ok": True})
            await self.unlock_protective_stop()
            steps.append({"step": "unlock_protective_stop", "ok": True})
            poll = await self._poll_until(self.safetystatus, "safety_status", "NORMAL")
            steps.append({"step": "wait_NORMAL", **poll})
            return {"ok": poll["ok"], "steps": steps, "error": poll.get("error")}

        await self.restart_safety()
        steps.append({"step": "restart_safety", "ok": True})
        poll = await self._poll_until(self.robotmode, "robot_mode", "POWER_OFF")
        steps.append({"step": "wait_POWER_OFF", **poll})
        if not poll["ok"]: return {"ok": False, "steps": steps, "error": poll["error"]}
        poll = await self._poll_until(self.safetystatus, "safety_status", "NORMAL")
        steps.append({"step": "wait_NORMAL", **poll})
        return {"ok": poll["ok"], "steps": steps, "error": poll.get("error")}

    async def seq_start(self, program_path: str | None = None) -> dict:
        mode = await self._get_mode()
        running = await self._is_program_running()
        steps = [{"step": "check", "ok": True, "mode": mode, "running": running}]

        if running:
            steps.append({"step": "skip", "ok": True, "reason": "already running"})
            return {"ok": True, "steps": steps}

        if mode != "RUNNING":
            result = await self.seq_servo_on()
            steps.extend(result.get("steps", []))
            if not result["ok"]:
                return {"ok": False, "steps": steps, "error": result.get("error")}

        if program_path:
            await self.load(program_path)
            steps.append({"step": f"load({program_path})", "ok": True})

        await self.play()
        steps.append({"step": "play", "ok": True})
        poll = await self._poll_until(self.running, "program_running", True)
        steps.append({"step": "wait_running", **poll})
        return {"ok": poll["ok"], "steps": steps, "error": poll.get("error")}

    async def seq_full_boot(self, program_path: str | None = None) -> dict:
        steps = []
        if await self._has_safety_issue():
            result = await self.seq_error_reset()
            steps.extend(result.get("steps", []))
            if not result["ok"]:
                return {"ok": False, "steps": steps, "error": result.get("error")}

        result = await self.seq_start(program_path)
        steps.extend(result.get("steps", []))
        return {"ok": result["ok"], "steps": steps, "error": result.get("error")}


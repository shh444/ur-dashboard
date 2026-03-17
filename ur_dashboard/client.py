from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from .exceptions import (
    DashboardCommandRejected,
    DashboardCommunicationError,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DashboardResponse:
    command: str
    raw: str
    ok: bool = True
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RobotState:
    connected: bool
    greeting: str | None = None
    robot_mode: str | None = None
    safety_status: str | None = None
    program_running: bool | None = None
    program_state: str | None = None
    loaded_program: str | None = None
    polyscope_version: str | None = None
    version: str | None = None
    serial_number: str | None = None
    robot_model: str | None = None
    remote_control: bool | None = None
    operational_mode: str | None = None
    program_saved: bool | None = None
    errors: dict[str, str] = field(default_factory=dict)


class URDashboardClient:
    """
    Async client for UR Dashboard Server (TCP 29999).

    All commands from the official UR e-Series Dashboard Server manual
    are implemented.
    """

    _ERROR_PREFIXES = (
        "failed",
        "error",
        "cannot",
        "could not",
        "not allowed",
        "no program loaded",
        "is not allowed",
        "no log message",
    )

    _ERROR_CONTAINS = (
        "unknown command",
        "file not found",
    )

    def __init__(
        self,
        host: str,
        port: int = 29999,
        *,
        connect_timeout: float = 3.0,
        command_timeout: float = 5.0,
    ) -> None:
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout
        self._command_timeout = command_timeout

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._greeting: str | None = None

    def __repr__(self) -> str:
        s = "connected" if self.is_connected else "disconnected"
        return f"URDashboardClient({self._host}:{self._port}, {s})"

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def greeting(self) -> str | None:
        return self._greeting

    @property
    def is_connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def __aenter__(self) -> "URDashboardClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        async with self._lock:
            await self._connect_locked()

    async def close(self) -> None:
        async with self._lock:
            await self._reset_locked()

    async def _connect_locked(self) -> None:
        if self.is_connected:
            return

        logger.info("Connecting to %s:%s ...", self._host, self._port)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._connect_timeout,
            )
            greeting = await asyncio.wait_for(
                reader.readline(), timeout=self._command_timeout,
            )
            self._reader = reader
            self._writer = writer
            self._greeting = greeting.decode(errors="replace").strip() or None
            logger.info("Connected. Greeting: %s", self._greeting)

        except Exception as exc:
            await self._reset_locked()
            raise DashboardCommunicationError(
                f"Connect failed {self._host}:{self._port}: {exc}"
            ) from exc

    async def _reset_locked(self) -> None:
        w = self._writer
        self._reader = None
        self._writer = None
        if w:
            w.close()
            try:
                await w.wait_closed()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _clean(value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        if "\n" in value or "\r" in value:
            raise ValueError("must be single-line")
        return value

    @staticmethod
    def _after_colon(raw: str) -> str:
        return raw.split(":", 1)[1].strip() if ":" in raw else raw.strip()

    @classmethod
    def _is_ok(cls, raw: str) -> bool:
        low = raw.lower().strip()
        for p in cls._ERROR_PREFIXES:
            if low.startswith(p):
                return False
        for m in cls._ERROR_CONTAINS:
            if m in low:
                return False
        return True

    @staticmethod
    def _parse_bool(raw: str) -> bool | None:
        v = URDashboardClient._after_colon(raw).lower().strip()
        if v == "true":
            return True
        if v == "false":
            return False
        return None

    async def _send(self, command: str) -> str:
        command = self._clean(command)
        async with self._lock:
            for attempt in range(2):
                try:
                    if not self.is_connected:
                        await self._connect_locked()
                    assert self._reader and self._writer

                    logger.debug("TX -> %s", command)
                    self._writer.write((command + "\n").encode())
                    await self._writer.drain()

                    raw = await asyncio.wait_for(
                        self._reader.readline(),
                        timeout=self._command_timeout,
                    )
                    if not raw:
                        raise ConnectionError("Connection closed")

                    resp = raw.decode(errors="replace").strip()
                    logger.debug("RX <- %s", resp)
                    return resp

                except (asyncio.TimeoutError, OSError, ConnectionError) as exc:
                    logger.warning("Attempt %d failed (%s): %s", attempt + 1, command, exc)
                    await self._reset_locked()
                    if attempt == 0:
                        continue
                    raise DashboardCommunicationError(
                        f"Command {command!r} failed: {exc}"
                    ) from exc

        raise DashboardCommunicationError("Unreachable")

    async def _action(self, command: str) -> DashboardResponse:
        raw = await self._send(command)
        if not self._is_ok(raw):
            raise DashboardCommandRejected(command=command, raw_response=raw)
        logger.info("OK: %s -> %s", command, raw)
        return DashboardResponse(command=command, raw=raw, ok=True)

    async def _query(self, command: str, parser=None) -> DashboardResponse:
        raw = await self._send(command)
        data = parser(raw) if parser else {}
        return DashboardResponse(command=command, raw=raw, ok=True, data=data)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        try:
            await self._send("robotmode")
            return True
        except Exception:
            return False

    async def raw(self, command: str) -> DashboardResponse:
        raw = await self._send(command)
        return DashboardResponse(command=command, raw=raw)

    # ==================================================================
    # Official Dashboard Commands (UR e-Series Manual)
    # ==================================================================

    # --- Program Control (Remote Control required) --------------------

    async def load(self, program_path: str) -> DashboardResponse:
        """load <program.urp>"""
        return await self._action(f"load {self._clean(program_path)}")

    async def play(self) -> DashboardResponse:
        """play"""
        return await self._action("play")

    async def stop(self) -> DashboardResponse:
        """stop"""
        return await self._action("stop")

    async def pause(self) -> DashboardResponse:
        """pause"""
        return await self._action("pause")

    # --- Connection ---------------------------------------------------

    async def quit(self) -> DashboardResponse:
        """quit — closes dashboard connection"""
        return await self._action("quit")

    # --- System -------------------------------------------------------

    async def shutdown(self) -> DashboardResponse:
        """shutdown"""
        return await self._action("shutdown")

    async def power_on(self) -> DashboardResponse:
        """power on (Remote Control required)"""
        return await self._action("power on")

    async def power_off(self) -> DashboardResponse:
        """power off (Remote Control required)"""
        return await self._action("power off")

    async def brake_release(self) -> DashboardResponse:
        """brake release (Remote Control required)"""
        return await self._action("brake release")

    # --- Query --------------------------------------------------------

    async def running(self) -> DashboardResponse:
        """running → program_running: bool"""
        return await self._query(
            "running",
            lambda r: {"program_running": self._parse_bool(r)},
        )

    async def robotmode(self) -> DashboardResponse:
        """robotmode → robot_mode: str"""
        return await self._query(
            "robotmode",
            lambda r: {"robot_mode": self._after_colon(r)},
        )

    async def get_loaded_program(self) -> DashboardResponse:
        """get loaded program → loaded_program: str | None"""
        raw = await self._send("get loaded program")
        loaded = None if raw.lower().startswith("no program") else self._after_colon(raw)
        return DashboardResponse(
            command="get loaded program", raw=raw, ok=True,
            data={"loaded_program": loaded},
        )

    async def programstate(self) -> DashboardResponse:
        """programState → program_state: STOPPED/PLAYING/PAUSED"""
        return await self._query(
            "programState",
            lambda r: {"program_state": self._after_colon(r).split()[0]},
        )

    async def polyscope_version(self) -> DashboardResponse:
        """PolyscopeVersion → polyscope_version: str"""
        return await self._query(
            "PolyscopeVersion",
            lambda r: {"polyscope_version": r},
        )

    async def version(self) -> DashboardResponse:
        """version → version: str (5.13.0+)"""
        return await self._query(
            "version",
            lambda r: {"version": r.strip()},
        )

    async def safetystatus(self) -> DashboardResponse:
        """safetystatus → safety_status: str"""
        raw = await self._send("safetystatus")
        if "unknown command" in raw.lower():
            raw = await self._send("safetymode")
        return DashboardResponse(
            command="safetystatus", raw=raw, ok=True,
            data={"safety_status": self._after_colon(raw)},
        )

    async def get_serial_number(self) -> DashboardResponse:
        """get serial number → serial_number: str"""
        return await self._query(
            "get serial number",
            lambda r: {"serial_number": r.strip()},
        )

    async def get_robot_model(self) -> DashboardResponse:
        """get robot model → robot_model: str"""
        return await self._query(
            "get robot model",
            lambda r: {"robot_model": r.strip()},
        )

    async def is_in_remote_control(self) -> DashboardResponse:
        """is in remote control → remote_control: bool"""
        return await self._query(
            "is in remote control",
            lambda r: {"remote_control": self._parse_bool(r)},
        )

    async def is_program_saved(self) -> DashboardResponse:
        """isProgramSaved → saved: bool, program_name: str"""
        raw = await self._send("isProgramSaved")
        parts = raw.strip().split(maxsplit=1)
        saved = parts[0].lower() == "true" if parts else None
        name = parts[1] if len(parts) > 1 else None
        return DashboardResponse(
            command="isProgramSaved", raw=raw, ok=True,
            data={"program_saved": saved, "program_name": name},
        )

    async def get_operational_mode(self) -> DashboardResponse:
        """get operational mode → operational_mode: str"""
        return await self._query(
            "get operational mode",
            lambda r: {"operational_mode": r.strip()},
        )

    # --- Action (additional) ------------------------------------------

    async def popup(self, message: str) -> DashboardResponse:
        """popup <text>"""
        return await self._action(f"popup {self._clean(message)}")

    async def close_popup(self) -> DashboardResponse:
        """close popup"""
        return await self._action("close popup")

    async def close_safety_popup(self) -> DashboardResponse:
        """close safety popup (Remote Control required)"""
        return await self._action("close safety popup")

    async def add_to_log(self, message: str) -> DashboardResponse:
        """addToLog <message>"""
        return await self._action(f"addToLog {self._clean(message)}")

    async def set_operational_mode(self, mode: str) -> DashboardResponse:
        """set operational mode <manual|automatic>"""
        mode = self._clean(mode).lower()
        if mode not in ("manual", "automatic"):
            raise ValueError("mode must be 'manual' or 'automatic'")
        return await self._action(f"set operational mode {mode}")

    async def clear_operational_mode(self) -> DashboardResponse:
        """clear operational mode"""
        return await self._action("clear operational mode")

    async def unlock_protective_stop(self) -> DashboardResponse:
        """unlock protective stop (Remote Control required)"""
        return await self._action("unlock protective stop")

    async def load_installation(self, path: str) -> DashboardResponse:
        """load installation <path> (Remote Control required)"""
        return await self._action(f"load installation {self._clean(path)}")

    async def restart_safety(self) -> DashboardResponse:
        """restart safety (Remote Control required)"""
        return await self._action("restart safety")

    async def generate_flight_report(self, report_type: str = "system") -> DashboardResponse:
        """generate flight report <controller|software|system>"""
        report_type = self._clean(report_type).lower()
        if report_type not in ("controller", "software", "system"):
            raise ValueError("report_type must be controller, software, or system")
        return await self._action(f"generate flight report {report_type}")

    async def generate_support_file(self, directory_path: str) -> DashboardResponse:
        """generate support file <path>"""
        return await self._action(f"generate support file {self._clean(directory_path)}")

    # ------------------------------------------------------------------
    # Snapshot (partial-failure tolerant)
    # ------------------------------------------------------------------

    async def snapshot(self) -> RobotState:
        state = RobotState(connected=self.is_connected, greeting=self.greeting)

        queries = [
            ("robot_mode", self.robotmode, "robot_mode"),
            ("safety_status", self.safetystatus, "safety_status"),
            ("program_running", self.running, "program_running"),
            ("program_state", self.programstate, "program_state"),
            ("loaded_program", self.get_loaded_program, "loaded_program"),
            ("polyscope_version", self.polyscope_version, "polyscope_version"),
            ("version", self.version, "version"),
            ("serial_number", self.get_serial_number, "serial_number"),
            ("robot_model", self.get_robot_model, "robot_model"),
            ("remote_control", self.is_in_remote_control, "remote_control"),
            ("operational_mode", self.get_operational_mode, "operational_mode"),
            ("program_saved", self.is_program_saved, "program_saved"),
        ]

        for name, fn, key in queries:
            try:
                result = await fn()
                setattr(state, key, result.data.get(key))
            except Exception as exc:
                logger.warning("snapshot '%s' failed: %s", name, exc)
                state.errors[name] = str(exc)

        return state

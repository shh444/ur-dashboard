"""
UR Dashboard 웹 API 서버.

실행:
    python -m uvicorn ur_dashboard.server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .async_dashboard import AsyncDashboard
from .exceptions import DashboardCommandRejected, DashboardCommunicationError, DashboardError

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

ROBOT_HOST = os.getenv("UR_ROBOT_HOST", "192.168.1.101")
DASHBOARD_PORT = int(os.getenv("UR_DASHBOARD_PORT", "29999"))
CONNECT_TIMEOUT = float(os.getenv("UR_CONNECT_TIMEOUT", "3.0"))
COMMAND_TIMEOUT = float(os.getenv("UR_COMMAND_TIMEOUT", "5.0"))
CONNECT_AT_STARTUP = os.getenv("UR_CONNECT_AT_STARTUP", "true").lower() in ("true", "1", "yes")


class ProgramBody(BaseModel):
    program_path: str

class MessageBody(BaseModel):
    message: str

class RawBody(BaseModel):
    command: str

class StartBody(BaseModel):
    program_path: str | None = None

class ModeBody(BaseModel):
    mode: str

class BootBody(BaseModel):
    power_wait: float = 5.0
    brake_wait: float = 3.0

class InstallBody(BaseModel):
    path: str


def j(v: Any) -> Any:
    if is_dataclass(v) and not isinstance(v, type): return asdict(v)
    if isinstance(v, list): return [j(i) for i in v]
    if isinstance(v, dict): return {k: j(val) for k, val in v.items()}
    return v


def ur(r: Request) -> AsyncDashboard:
    return r.app.state.robot


@asynccontextmanager
async def lifespan(app: FastAPI):
    robot = AsyncDashboard(
        host=ROBOT_HOST, port=DASHBOARD_PORT,
        connect_timeout=CONNECT_TIMEOUT, command_timeout=COMMAND_TIMEOUT,
        lazy=not CONNECT_AT_STARTUP,
    )
    app.state.robot = robot
    try:
        if CONNECT_AT_STARTUP:
            try: await robot.connect(); logger.info("Connected at startup.")
            except DashboardCommunicationError as e: logger.warning("Startup connect failed: %s", e)
        else:
            logger.info("Lazy mode.")
        yield
    finally:
        await robot.close()


app = FastAPI(title="UR Dashboard API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(DashboardCommandRejected)
async def _(r, e): return JSONResponse(409, {"detail": "rejected", "command": e.command, "raw": e.raw_response})

@app.exception_handler(DashboardCommunicationError)
async def _(r, e): return JSONResponse(503, {"detail": str(e)})

@app.exception_handler(DashboardError)
async def _(r, e): return JSONResponse(500, {"detail": str(e)})


# System
@app.get("/health")
async def health(): return {"ok": True}

@app.get("/health/robot")
async def health_robot(r: Request): return {"reachable": await ur(r).ping()}

# Query
@app.get("/dashboard/state")
async def q_state(r: Request): return j(await ur(r).state())

@app.get("/dashboard/robot-mode")
async def q_mode(r: Request): return j(await ur(r).robotmode())

@app.get("/dashboard/running")
async def q_running(r: Request): return j(await ur(r).running())

@app.get("/dashboard/program-state")
async def q_pstate(r: Request): return j(await ur(r).programstate())

@app.get("/dashboard/loaded-program")
async def q_loaded(r: Request): return j(await ur(r).get_loaded_program())

@app.get("/dashboard/safety-status")
async def q_safety(r: Request): return j(await ur(r).safetystatus())

@app.get("/dashboard/version")
async def q_ver(r: Request): return j(await ur(r).polyscope_version())

@app.get("/dashboard/serial-number")
async def q_serial(r: Request): return j(await ur(r).get_serial_number())

@app.get("/dashboard/robot-model")
async def q_model(r: Request): return j(await ur(r).get_robot_model())

@app.get("/dashboard/remote-control")
async def q_remote(r: Request): return j(await ur(r).is_in_remote_control())

@app.get("/dashboard/operational-mode")
async def q_opmode(r: Request): return j(await ur(r).get_operational_mode())

@app.get("/dashboard/program-saved")
async def q_saved(r: Request): return j(await ur(r).is_program_saved())

# Action
@app.post("/dashboard/power-on")
async def a_pon(r: Request): return j(await ur(r).power_on())

@app.post("/dashboard/power-off")
async def a_poff(r: Request): return j(await ur(r).power_off())

@app.post("/dashboard/brake-release")
async def a_brake(r: Request): return j(await ur(r).brake_release())

@app.post("/dashboard/play")
async def a_play(r: Request): return j(await ur(r).play())

@app.post("/dashboard/pause")
async def a_pause(r: Request): return j(await ur(r).pause())

@app.post("/dashboard/stop")
async def a_stop(r: Request): return j(await ur(r).stop())

@app.post("/dashboard/load")
async def a_load(b: ProgramBody, r: Request): return j(await ur(r).load(b.program_path))

@app.post("/dashboard/popup")
async def a_popup(b: MessageBody, r: Request): return j(await ur(r).popup(b.message))

@app.post("/dashboard/close-popup")
async def a_cpopup(r: Request): return j(await ur(r).close_popup())

@app.post("/dashboard/close-safety-popup")
async def a_cspopup(r: Request): return j(await ur(r).close_safety_popup())

@app.post("/dashboard/unlock-protective-stop")
async def a_unlock(r: Request): return j(await ur(r).unlock_protective_stop())

@app.post("/dashboard/restart-safety")
async def a_restart(r: Request): return j(await ur(r).restart_safety())

@app.post("/dashboard/log")
async def a_log(b: MessageBody, r: Request): return j(await ur(r).add_to_log(b.message))

@app.post("/dashboard/set-operational-mode")
async def a_setmode(b: ModeBody, r: Request): return j(await ur(r).set_operational_mode(b.mode))

@app.post("/dashboard/clear-operational-mode")
async def a_clrmode(r: Request): return j(await ur(r).clear_operational_mode())

@app.post("/dashboard/raw")
async def a_raw(b: RawBody, r: Request): return j(await ur(r).raw(b.command))

@app.post("/dashboard/shutdown")
async def a_shutdown(r: Request): return j(await ur(r).shutdown())

# Sequence
@app.post("/dashboard/start")
async def s_start(b: StartBody, r: Request): return j(await ur(r).seq_start(b.program_path))

@app.post("/dashboard/power-on-and-release")
async def s_servo(r: Request): return await ur(r).seq_servo_on()

@app.post("/dashboard/safe-boot")
async def s_boot(b: BootBody, r: Request): return await ur(r).seq_full_boot(b.program_path if hasattr(b, 'program_path') else "/programs/main.urp")

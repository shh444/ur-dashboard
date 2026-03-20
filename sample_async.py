import asyncio
from ur_dashboard import AsyncDashboard


async def main():
    ur = AsyncDashboard("192.168.163.128")
    await ur.connect()

    # --- 상태 조회 ---
    print(await ur.state())
    # print(await ur.robotmode())
    # print(await ur.running())
    # print(await ur.programstate())
    # print(await ur.safetystatus())
    # print(await ur.get_loaded_program())
    # print(await ur.is_in_remote_control())
    # print(await ur.polyscope_version())
    # print(await ur.version())
    # print(await ur.get_serial_number())
    # print(await ur.get_robot_model())
    # print(await ur.get_operational_mode())
    # print(await ur.is_program_saved())
    # print(await ur.ping())

    # --- 제어 ---
    # print(await ur.power_on())
    # print(await ur.power_off())
    # print(await ur.brake_release())
    # print(await ur.load("/programs/main.urp"))
    # print(await ur.play())
    # print(await ur.pause())
    # print(await ur.stop())

    # --- 팝업 / 로그 ---
    # print(await ur.popup("테스트 팝업"))
    # print(await ur.close_popup())
    # print(await ur.close_safety_popup())
    # print(await ur.add_to_log("테스트 로그"))

    # --- 안전 ---
    # print(await ur.unlock_protective_stop())
    # print(await ur.restart_safety())

    # --- 운영 모드 ---
    # print(await ur.set_operational_mode("manual"))
    # print(await ur.clear_operational_mode())

    # --- Raw ---
    # print(await ur.raw("robotmode"))

    # --- 시퀀스 ---
    # print(await ur.seq_servo_on())
    # print(await ur.seq_servo_off())
    # print(await ur.seq_start())
    # print(await ur.seq_error_reset())
    # print(await ur.seq_full_boot())

    await ur.close()


asyncio.run(main())

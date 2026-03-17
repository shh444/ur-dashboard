from ur_dashboard import SyncDashboard

ur = SyncDashboard("192.168.1.101")

# --- 상태 조회 ---
print(ur.state())
# print(ur.robotmode())
# print(ur.running())
# print(ur.programstate())
# print(ur.safetystatus())
# print(ur.get_loaded_program())
# print(ur.is_in_remote_control())
# print(ur.polyscope_version())
# print(ur.version())
# print(ur.get_serial_number())
# print(ur.get_robot_model())
# print(ur.get_operational_mode())
# print(ur.is_program_saved())
# print(ur.ping())

# --- 제어 ---
# print(ur.power_on())
# print(ur.power_off())
# print(ur.brake_release())
# print(ur.load("/programs/main.urp"))
# print(ur.play())
# print(ur.pause())
# print(ur.stop())

# --- 팝업 / 로그 ---
# print(ur.popup("테스트 팝업"))
# print(ur.close_popup())
# print(ur.close_safety_popup())
# print(ur.add_to_log("테스트 로그"))

# --- 안전 ---
# print(ur.unlock_protective_stop())
# print(ur.restart_safety())

# --- 운영 모드 ---
# print(ur.set_operational_mode("manual"))
# print(ur.clear_operational_mode())

# --- Raw ---
# print(ur.raw("robotmode"))

# --- 시퀀스 ---
print(ur.seq_servo_on().summary())
# print(ur.seq_servo_off().summary())
# print(ur.seq_start().summary())
# print(ur.seq_error_reset().summary())
# print(ur.seq_full_boot().summary())

ur.close()

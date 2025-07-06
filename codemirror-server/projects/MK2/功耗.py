# 声明全局变量(定义需要的变量)
power_events = {}
found_names = set()

prompt = "检查功耗相关的日志条目"

def looper1(name, args, timestamp, line):
    # 检查与功耗相关的日志条目
    if name in [
        "battery_changed", "charging_speed", "hbm_brightness", 
        "update_is_powered_locked", "refresh_battery_info", 
        "update_charging_status", "plugged_type", "handle_battery_update"
    ]:
        if name not in found_names:
            power_events[name] = (args, timestamp, line)
            found_names.add(name)

def looper2(name, args, timestamp, line):
    # 二次检查日志，如果没有必要可以不定义
    pass

def end():
    # 打印出输出最后的结论
    if power_events:
        print("### 功耗相关日志条目")
        for name, (args, timestamp, line) in power_events.items():
            print(f"- **{name}**: {args} (时间戳: {timestamp}, 行号: {line})")
        return True
    else:
        print("### 未发现功耗相关日志条目")
        return False
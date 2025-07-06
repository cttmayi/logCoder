# 声明全局变量
battery_changes = []
charging_speeds = []
plugged_types = []

prompt = "检查功耗相关的信息，包括电池变化、充电速度和电池插拔类型。"

def looper1(name, args, timestamp, line):
    if name == "battery_changed":
        battery_changes.append((timestamp, args))
    elif name == "charging_speed":
        charging_speeds.append((timestamp, args))
    elif name == "plugged_type":
        plugged_types.append((timestamp, args))

def looper2(name, args, timestamp, line):
    pass  # 在这里可以添加二次检查的逻辑，如果需要的话

def end():
    # 打印检查结果
    print("**电池变化记录：**")
    for ts, args in battery_changes:
        print(f"时间戳: {ts}, 参数: {args}")
    
    print("\n**充电速度记录：**")
    for ts, args in charging_speeds:
        print(f"时间戳: {ts}, 参数: {args}")
    
    print("\n**电池插拔类型记录：**")
    for ts, args in plugged_types:
        print(f"时间戳: {ts}, 参数: {args}")
    
    # 返回是否发现需要检查的项目
    return len(battery_changes) > 0 or len(charging_speeds) > 0 or len(plugged_types) > 0
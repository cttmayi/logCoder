# 声明全局变量
battery_info = []
prompt = ""  # 返回文字的细节描述,用于送给大模型对执行的结果进行分析, 必须定义

def looper1(name, args, timestamp, line):
    global battery_info
    if name == "battery_changed":
        # 记录电池变化信息
        battery_info.append({
            "name": name,
            "args": args,
            "timestamp": timestamp,
            "line": line
        })
    elif name == "charging_speed":
        # 记录充电速度信息
        battery_info.append({
            "name": name,
            "args": args,
            "timestamp": timestamp,
            "line": line
        })

def looper2(name, args, timestamp, line):
    pass  # 不需要额外处理

def end():
    global battery_info, prompt
    abnormal_alerts = []
    
    for info in battery_info:
        if info["name"] == "battery_changed":
            # 检查电池变化是否有异常
            if "level" in info["args"] and info["args"]["level"] < 10:
                abnormal_alerts.append(f"低电量警报: 电量 {info['args']['level']}%, 时间戳 {info['timestamp']}, 行号 {info['line']}")
        elif info["name"] == "charging_speed":
            # 检查充电速度是否有异常
            if "speed" in info["args"] and info["args"]["speed"] < 0.5:
                abnormal_alerts.append(f"充电速度异常: 速度 {info['args']['speed']} mA, 时间戳 {info['timestamp']}, 行号 {info['line']}")
    
    if abnormal_alerts:
        prompt = "发现以下电量异常报警:\n" + "\n".join(abnormal_alerts)
        print(prompt)
        return True
    else:
        prompt = "未发现电量异常报警"
        print(prompt)
        return True
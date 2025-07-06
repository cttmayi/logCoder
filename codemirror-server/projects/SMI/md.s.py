# 声明全局变量(定义需要的变量)
power_info = []

prompt = "检查功耗相关的信息"

def looper1(name, args, timestamp, line):
    # 检查与功耗相关的日志条目
    if name in ['battery_changed', 'charging_speed', 'update_charging_status']:
        power_info.append({
            'name': name,
            'args': args,
            'timestamp': timestamp,
            'line': line
        })

def looper2(name, args, timestamp, line):
    # 如果没有其他特定的日志条目需要检查，可以不实现这个函数
    pass

def end():
    # 打印出输出最后的结论.
    if power_info:
        print("### 功耗相关信息")
        for info in power_info:
            print(f"- **{info['name']}**: {info['args']} (时间戳: {info['timestamp']}, 行号: {info['line']})")
        return False
    else:
        print("### 未发现功耗相关信息")
        return False
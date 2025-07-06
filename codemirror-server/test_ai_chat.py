#!/usr/bin/env python3
"""
测试AI对话功能的脚本
"""

import requests
import json

# API基础URL
API_BASE_URL = 'http://localhost:8000/api'

def test_ai_chat():
    """测试AI对话功能"""
    
    # 测试数据
    test_cases = [
        {
            "type": "ai_chat",
            "message": "你好",
            "currentFile": "test.py",
            "currentCode": "# 测试代码\nprint('Hello World')"
        },
        {
            "type": "ai_chat", 
            "message": "帮我写一个函数",
            "currentFile": "functions.py",
            "currentCode": ""
        },
        {
            "type": "ai_chat",
            "message": "什么是类？",
            "currentFile": "classes.py", 
            "currentCode": "# 学习类"
        }
    ]
    
    print("🤖 测试AI对话功能...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {test_case['message']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/execute",
                headers={'Content-Type': 'application/json'},
                json=test_case,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功: {result['message']}")
                print(f"📄 解释部分:")
                print(result['explanation'])
                print(f"\n💻 代码部分:")
                print(result['code'])
                print(f"📊 解释长度: {len(result['explanation'])} 字符")
                print(f"📊 代码长度: {len(result['code'])} 字符")
            else:
                print(f"❌ 失败: HTTP {response.status_code}")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败: 请确保后端服务器正在运行 (python main.py)")
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print("\n💡 新功能说明：")
    print("- AI回复分为两部分：解释和代码")
    print("- 解释部分显示在对话框中")
    print("- 代码部分自动写入编辑器")
    print("- 执行结果也会显示在对话中")

if __name__ == "__main__":
    test_ai_chat() 
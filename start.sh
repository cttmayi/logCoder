#!/bin/bash

echo "🚀 启动 CodeMirror 项目..."

# 检查是否在正确的目录
if [ ! -d "codemirror-app" ] || [ ! -d "codemirror-server" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    echo "当前目录应包含 codemirror-app 和 codemirror-server 文件夹"
    exit 1
fi

# 启动后端服务器
echo "📡 启动 FastAPI 后端服务器..."
cd codemirror-server
python -m venv venv 2>/dev/null || echo "虚拟环境已存在"
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1 || echo "依赖安装中..."
python main.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "⏳ 等待后端服务器启动..."
sleep 3

# 启动前端应用
echo "🎨 启动 React 前端应用..."
cd codemirror-app
npm install > /dev/null 2>&1 || echo "依赖安装中..."
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ 服务启动完成！"
echo "📡 后端 API: http://localhost:8000"
echo "🎨 前端应用: http://localhost:3000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait 
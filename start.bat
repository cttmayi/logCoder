@echo off
echo 🚀 启动 CodeMirror 项目...

REM 检查是否在正确的目录
if not exist "codemirror-app" (
    echo ❌ 错误：请在项目根目录运行此脚本
    echo 当前目录应包含 codemirror-app 和 codemirror-server 文件夹
    pause
    exit /b 1
)

if not exist "codemirror-server" (
    echo ❌ 错误：请在项目根目录运行此脚本
    echo 当前目录应包含 codemirror-app 和 codemirror-server 文件夹
    pause
    exit /b 1
)

REM 启动后端服务器
echo 📡 启动 FastAPI 后端服务器...
cd codemirror-server
pip install -r requirements.txt >nul 2>&1
start "FastAPI Backend" python main.py
cd ..

REM 等待后端启动
echo ⏳ 等待后端服务器启动...
timeout /t 3 /nobreak >nul

REM 启动前端应用
echo 🎨 启动 React 前端应用...
cd codemirror-app
npm install >nul 2>&1
start "React Frontend" npm start
cd ..

echo ✅ 服务启动完成！
echo 📡 后端 API: http://localhost:8000
echo 🎨 前端应用: http://localhost:3000
echo 📚 API 文档: http://localhost:8000/docs
echo.
echo 按任意键退出...
pause >nul 
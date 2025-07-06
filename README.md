# CodeMirror 远程文件编辑器

一个基于 React + CodeMirror + FastAPI 的远程文件编辑器，支持 Python 文件的在线编辑、执行和管理。

## 项目结构

```
LogCoder/
├── codemirror-app/          # React 前端应用
│   ├── src/
│   │   ├── App.tsx         # 主应用组件
│   │   ├── App.css         # 样式文件
│   │   └── components/
│   │       └── CodeEditor.tsx  # CodeMirror 编辑器组件
│   ├── package.json        # 前端依赖
│   └── README.md           # 前端说明
├── codemirror-server/       # FastAPI 后端服务器
│   ├── main.py             # 主服务器文件
│   ├── requirements.txt    # Python 依赖
│   └── README.md           # 后端说明
├── start.sh                # Linux/Mac 启动脚本
├── start.bat               # Windows 启动脚本
└── README.md               # 项目说明
```

## 功能特性

### 前端功能
- 📁 目录和文件树管理
- 📝 基于 CodeMirror 的代码编辑器
- 💬 AI 对话界面
- 🔄 文件拖拽上传
- 💾 自动保存提示
- 🎨 现代化 UI 设计

### 后端功能
- 🗂️ 目录结构管理（创建、重命名、删除）
- 📄 文件内容操作（读取、保存、创建）
- 🚀 代码执行（文件、目录、全部）
- 📤 文件上传
- 🔍 健康检查
- 📚 自动 API 文档

## 快速启动

### 方法一：使用启动脚本（推荐）

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

### 方法二：手动启动

1. **启动后端服务器**
```bash
cd codemirror-server
pip install -r requirements.txt
python main.py
```

2. **启动前端应用**
```bash
cd codemirror-app
npm install
npm start
```

## 访问地址

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## API 端点

### 目录操作
- `GET /api/dirs` - 获取目录结构
- `POST /api/dir` - 创建目录
- `PUT /api/dir/{old_name}` - 重命名目录
- `DELETE /api/dir/{dir_name}` - 删除目录

### 文件操作
- `GET /api/file/{dir_name}/{file_name}` - 获取文件内容
- `POST /api/file/{dir_name}/{file_name}` - 保存文件内容
- `POST /api/file/{dir_name}` - 创建文件

### 其他功能
- `POST /api/execute` - 执行代码
- `POST /api/upload` - 上传文件
- `GET /api/health` - 健康检查

## 使用说明

### 基本操作
1. **浏览文件**: 点击目录展开/折叠，点击文件打开编辑
2. **编辑代码**: 在 CodeMirror 编辑器中编写 Python 代码
3. **保存文件**: 点击"保存文件"按钮或切换文件时自动提示
4. **执行代码**: 选择执行当前文件、当前目录或全部目录

### 目录管理
1. **添加目录**: 点击"添加目录"按钮
2. **重命名目录**: 点击目录旁的"编辑"按钮
3. **删除目录**: 在编辑对话框中点击"删除"按钮

### 文件管理
1. **添加文件**: 展开目录后点击"添加文件"按钮
2. **上传文件**: 拖拽文件到上传区域或点击选择文件

### AI 对话
- 在左侧聊天界面与 AI 进行对话
- 支持 Shift+Enter 换行
- AI 回复的代码会自动写入编辑器

## 技术栈

### 前端
- **React 18** - 用户界面框架
- **CodeMirror 6** - 代码编辑器
- **TypeScript** - 类型安全
- **CSS3** - 样式设计

### 后端
- **FastAPI** - 现代 Python Web 框架
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器
- **Python 3.8+** - 编程语言

## 开发说明

### 前端开发
```bash
cd codemirror-app
npm install
npm start
```

### 后端开发
```bash
cd codemirror-server
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 添加新功能
1. 在后端 `main.py` 中添加新的 API 端点
2. 在前端 `App.tsx` 中添加对应的处理函数
3. 更新样式文件 `App.css`

## 注意事项

- 服务器会自动创建 `projects` 目录用于存储文件
- 只支持 `.py` 文件的显示和操作
- 所有操作都有错误处理和日志记录
- 支持 CORS，可以从前端应用访问
- 提供完整的 API 文档和类型检查

## 故障排除

### 常见问题

1. **端口被占用**
   - 检查 3000 和 8000 端口是否被占用
   - 修改端口号或停止占用进程

2. **依赖安装失败**
   - 确保 Python 3.8+ 和 Node.js 16+ 已安装
   - 检查网络连接

3. **API 连接失败**
   - 确保后端服务器正在运行
   - 检查 CORS 配置

4. **文件权限问题**
   - 确保对 `projects` 目录有读写权限

## 许可证

MIT License 
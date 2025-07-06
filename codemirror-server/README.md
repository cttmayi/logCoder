# CodeMirror FastAPI 服务器

基于 FastAPI 框架的 CodeMirror 远程文件操作服务器。

## 功能特性

- 📁 目录结构管理（获取、创建、重命名、删除）
- 📄 文件内容操作（读取、保存、创建）
- 🚀 代码执行（文件、目录、全部）
- 📤 文件上传
- 🔍 健康检查
- 📚 自动API文档

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

## 安装和运行

1. 创建虚拟环境（推荐）

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动服务器：
```bash
python main.py
```

4. 开发模式（自动重启）：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务器将在 http://localhost:8000 启动。

## API 文档

启动服务器后，可以访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
codemirror-server/
├── main.py              # FastAPI 主应用
├── requirements.txt     # Python 依赖
├── README.md           # 说明文档
└── projects/           # 项目文件存储目录（自动创建）
```

## 前端集成

在 CodeMirror 前端应用中，将模拟的 API 调用替换为真实的 HTTP 请求：

```javascript
// 获取目录结构
const response = await fetch('http://localhost:8000/api/dirs');
const dirs = await response.json();

// 保存文件
await fetch(`http://localhost:8000/api/file/${dir}/${file}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: fileContent })
});

// 创建目录
await fetch('http://localhost:8000/api/dir', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'new_project' })
});
```

## 数据模型

### DirectoryCreate
```json
{
  "name": "project_name"
}
```

### FileContent
```json
{
  "content": "# Python code here\nprint('Hello World')"
}
```

### ExecuteRequest
```json
{
  "type": "file",
  "dir": "project1",
  "file": "main.py",
  "content": "# code content"
}
```

## 注意事项

- 服务器会自动创建 `projects` 目录用于存储文件
- 只支持 `.py` 文件的显示和操作
- 所有操作都有错误处理和日志记录
- 支持 CORS，可以从前端应用访问
- 提供完整的 API 文档和类型检查

## 开发

### 添加新的API端点

1. 在 `main.py` 中添加新的路由函数
2. 定义相应的 Pydantic 模型
3. 更新 API 文档

### 扩展功能

- 添加文件上传的实际实现
- 集成 Python 解释器执行代码
- 添加用户认证和权限控制
- 支持更多文件类型 
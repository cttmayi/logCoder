from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import helper.llm as llm
import io
import contextlib
import traceback
import datetime
import time

app = FastAPI(title="CodeMirror Server", version="1.0.0")

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 项目根目录
PROJECT_ROOT = Path("projects")
PROJECT_ROOT.mkdir(exist_ok=True)

TMP_ROOT = Path(__file__).parent / 'tmp'
TMP_ROOT.mkdir(exist_ok=True)

# 用户凭据（实际应用中应该使用数据库和加密密码）
VALID_USERS = {
    "admin": "admin123",
    "user": "password123",
    "test": "test123",
    "guest": ""  # guest用户不需要密码
}

# 数据模型
class DirectoryCreate(BaseModel):
    name: str

class DirectoryRename(BaseModel):
    newName: str

class FileCreate(BaseModel):
    fileName: str

class FileContent(BaseModel):
    content: str

class ExecuteRequest(BaseModel):
    type: str  # 'file', 'dir', 'all', 'code'
    dir: Optional[str] = None
    file: Optional[str] = None
    content: Optional[str] = None
    code: Optional[str] = None
    uploadedFiles: Optional[list] = None

class AIChatRequest(BaseModel):
    message: str
    currentFile: Optional[str] = None
    currentCode: Optional[str] = None
    currentDir: Optional[str] = None
    messages: Optional[list] = None

class UploadResponse(BaseModel):
    success: bool
    message: str
    fileName: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None

# 工具函数
def get_python_files(directory: Path) -> List[dict]:
    """获取目录下的Python文件列表"""
    files = []
    if directory.exists():
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix == '.py':
                files.append({"name": file_path.name})
    return files

def ensure_directory(directory: Path):
    """确保目录存在"""
    directory.mkdir(parents=True, exist_ok=True)

# API端点
@app.post("/api/login")
async def login(login_request: LoginRequest):
    """用户登录验证"""
    try:
        username = login_request.username
        password = login_request.password
        
        # 验证用户名和密码
        if username in VALID_USERS:
            # guest用户不需要密码验证
            if username == "guest" or VALID_USERS[username] == password:
                return LoginResponse(
                    success=True,
                    message="登录成功",
                    token=f"token_{username}_{int(time.time())}"  # 简单的token生成
                )
            else:
                return LoginResponse(
                    success=False,
                    message="密码错误"
                )
        else:
            return LoginResponse(
                success=False,
                message="用户名不存在"
            )
    except Exception as e:
        return LoginResponse(
            success=False,
            message=f"登录失败: {str(e)}"
        )

@app.get("/api/dirs")
async def get_directories():
    """获取目录结构"""
    try:
        dirs = []
        for item in PROJECT_ROOT.iterdir():
            if item.is_dir():
                files = get_python_files(item)
                dirs.append({
                    "name": item.name,
                    "files": files
                })
        return dirs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get directories: {str(e)}")

@app.get("/api/file/{dir_name}/{file_name}")
async def get_file_content(dir_name: str, file_name: str):
    """获取文件内容"""
    try:
        file_path = PROJECT_ROOT / dir_name / file_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        content = file_path.read_text(encoding='utf-8')
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@app.post("/api/file/{dir_name}/{file_name}")
async def save_file_content(dir_name: str, file_name: str, file_content: FileContent):
    """保存文件内容"""
    try:
        dir_path = PROJECT_ROOT / dir_name
        file_path = dir_path / file_name
        
        ensure_directory(dir_path)
        file_path.write_text(file_content.content, encoding='utf-8')
        
        return {"success": True, "message": "File saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

@app.post("/api/dir")
async def create_directory(directory: DirectoryCreate):
    """创建目录"""
    try:
        dir_path = PROJECT_ROOT / directory.name
        if dir_path.exists():
            raise HTTPException(status_code=400, detail="Directory already exists")
        
        dir_path.mkdir(parents=True, exist_ok=True)
        return {"success": True, "message": "Directory created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")

@app.put("/api/dir/{old_name}")
async def rename_directory(old_name: str, rename_data: DirectoryRename):
    """重命名目录"""
    try:
        old_path = PROJECT_ROOT / old_name
        new_path = PROJECT_ROOT / rename_data.newName
        
        if not old_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if new_path.exists():
            raise HTTPException(status_code=400, detail="Directory name already exists")
        
        old_path.rename(new_path)
        return {"success": True, "message": "Directory renamed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename directory: {str(e)}")

@app.delete("/api/dir/{dir_name}")
async def delete_directory(dir_name: str):
    """删除目录"""
    try:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        shutil.rmtree(dir_path)
        return {"success": True, "message": "Directory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete directory: {str(e)}")

@app.post("/api/file/{dir_name}")
async def create_file(dir_name: str, file_data: FileCreate):
    """创建文件"""
    try:
        dir_path = PROJECT_ROOT / dir_name
        file_path = dir_path / file_data.fileName
        
        ensure_directory(dir_path)
        
        if file_path.exists():
            raise HTTPException(status_code=400, detail="File already exists")
        
        # 创建空文件
        file_path.write_text("# New file\n", encoding='utf-8')
        return {"success": True, "message": "File created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")

@app.post("/api/ai_chat")
async def ai_chat(ai_request: AIChatRequest):
    """AI对话接口，生成解释和代码"""
    try:
        message = ai_request.message
        current_file = ai_request.currentFile
        current_code = ai_request.currentCode or ""
        current_dir = ai_request.currentDir
        messages = ai_request.messages
        ai_response = generate_ai_response(message, current_file, current_code, current_dir, messages)
        return {
            "success": True,
            "explanation": ai_response["explanation"],
            "code": ai_response["code"]
        }
    except Exception as e:
        return {
            "success": False,
            "explanation": f"# AI 回复 (错误)\n# 错误信息: {str(e)}",
            "code": "print('处理失败')"
        }

def run_code_with_context(code: str, current_dir: str = None, uploaded_files: list = None):
    # 自动替换全角引号为半角引号
    code = code.replace('‘', "'").replace('’', "'").replace('"', '"').replace('"', '"')
    abs_dir = None
    if current_dir:
        abs_dir = str((PROJECT_ROOT / current_dir).resolve())
    if not code:
        return {
            "success": False,
            "message": "没有提供代码内容",
            "result": ""
        }
    full_code = llm.gen_full_code(code, abs_dir, uploaded_files)
    output = llm.run_code(full_code)
    if output:
        output = output.replace('\n', '  \n') #  for markdown line break
    
    return {
        "success": True,
        "message": "执行完成",
        "result": output
    }

@app.post("/api/execute")
async def execute_code(execute_request: ExecuteRequest):
    """执行代码（不再处理AI对话）"""
    try:
        # print(f"Executing {execute_request.type}:", execute_request.model_dump())
        request_data = execute_request.model_dump()
        uploaded_files = request_data.get('uploadedFiles', None)
        # 检查是否有上传文件
        if not uploaded_files or not any(f.get('content') for f in uploaded_files):
            return {
                "success": False,
                "message": "未检测到需要上传的文件，请先选择并上传文件后再执行。",
                "result": ""
            }
        # 清理超过1分钟的旧文件
        current_time = time.time()
        for file_path in TMP_ROOT.rglob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 60:  # 超过1分钟
                    try:
                        file_path.unlink()
                        print(f"已删除旧文件: {file_path}")
                    except Exception as e:
                        print(f"删除旧文件失败: {file_path}, 错误: {e}")

        # TMP_ROOT = Path(__file__).parent / 'tmp'
        # TMP_ROOT.mkdir(exist_ok=True)
        uploaded_file_paths = []
        if uploaded_files:
            for f in uploaded_files:
                rel_path = f.get('relativePath')
                content = f.get('content')
                if not rel_path or content is None:
                    continue
                # 为文件名添加时间戳（精确到秒）
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path_parts = Path(rel_path).parts
                if len(path_parts) > 1:
                    # 如果有目录结构，在文件名前添加时间戳
                    filename = path_parts[-1]
                    name_without_ext, ext = os.path.splitext(filename)
                    timestamped_filename = f"{name_without_ext}_{timestamp}{ext}"
                    new_rel_path = str(Path(*path_parts[:-1]) / timestamped_filename)
                else:
                    # 如果只是文件名，直接添加时间戳
                    name_without_ext, ext = os.path.splitext(rel_path)
                    timestamped_filename = f"{name_without_ext}_{timestamp}{ext}"
                    new_rel_path = timestamped_filename

                save_path = TMP_ROOT / new_rel_path
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'w', encoding='utf-8') as wf:
                    wf.write(content)
                uploaded_file_paths.append(str(save_path.resolve()))
        # print("uploaded_files:", uploaded_files)
        # print("uploaded_file_paths:", uploaded_file_paths)
        if execute_request.type == 'code':
            code = request_data.get('code', '')
            current_dir = request_data.get('currentDir', None)
            messages = request_data.get('messages', None)
            return run_code_with_context(code, current_dir, uploaded_file_paths)
        elif execute_request.type == 'file':
            code = execute_request.content
            current_dir = execute_request.dir
            # 可选: messages = request_data.get('messages', None)
            return run_code_with_context(code, current_dir, uploaded_file_paths)
        elif execute_request.type == 'dir' and execute_request.dir:
            dir_name = execute_request.dir
            dir_path = PROJECT_ROOT / dir_name
            if not dir_path.exists() or not dir_path.is_dir():
                return {
                    "success": False,
                    "message": f"目录 {dir_name} 不存在",
                    "result": ""
                }
            results = []
            for file in dir_path.iterdir():
                if file.is_file() and file.suffix == '.py':
                    code = file.read_text(encoding='utf-8')
                    res = run_code_with_context(code, dir_name, uploaded_file_paths)
                    if res['result']:
                        results.append(f"## {file.name}\n{res['result']}\n")
            return {
                "success": True,
                "message": f"成功执行目录 {dir_name} 下所有 Python 文件",
                "result": "\n".join(results)
            }
        elif execute_request.type == 'all':
            results = []
            for dir_item in PROJECT_ROOT.iterdir():
                if dir_item.is_dir():
                    dir_name = dir_item.name
                    for file in dir_item.iterdir():
                        if file.is_file() and file.suffix == '.py':
                            code = file.read_text(encoding='utf-8')
                            res = run_code_with_context(code, dir_name, uploaded_file_paths)
                            if res['result']:
                                results.append(f"## {dir_name}/{file.name}\n{res['result']}\n")
            return {
                "success": True,
                "message": "成功执行全部目录下所有 Python 文件",
                "result": "\n".join(results)
            }
        else:
            result = f"Successfully executed {execute_request.type}"
        return {
            "success": True,
            "message": f"Executed {execute_request.type}",
            "result": result
        }
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        print('execute_code error:', tb_str)
        return {
            "success": False,
            "message": f"后端异常: {str(e)}",
            "result": ""
        }

@app.post("/api/upload")
async def upload_file():
    """上传文件（模拟）"""
    try:
        # 这里可以添加实际的文件上传逻辑
        return UploadResponse(
            success=True,
            message="File uploaded successfully",
            fileName="uploaded_file.py"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "OK",
        "timestamp": str(Path().cwd()),
        "project_root": str(PROJECT_ROOT.absolute())
    }

@app.post("/api/dir/{dir_name}/upload_jsonl")
async def upload_jsonl_to_dir(dir_name: str, jsonl_content: str = Form(...)):
    """接收前端上传的JSONL内容，保存为指定目录下的format.jsonl文件"""
    try:
        dir_path = PROJECT_ROOT / dir_name
        ensure_directory(dir_path)
        file_path = dir_path / "format.jsonl"
        # 直接保存内容，不做整体json校验
        file_path.write_text(jsonl_content, encoding='utf-8')
        return {"success": True, "message": f"format.jsonl 已保存到 {dir_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save format.jsonl: {str(e)}")

@app.post("/api/file/{dir_name}/{file_name}/rename")
async def rename_file(dir_name: str, file_name: str, data: dict = Body(...)):
    """重命名文件"""
    try:
        dir_path = PROJECT_ROOT / dir_name
        old_file = dir_path / file_name
        new_name = data.get('newName', '').strip()
        if not new_name or new_name == file_name:
            return {"success": False, "message": "新文件名无效"}
        new_file = dir_path / new_name
        if not old_file.exists():
            return {"success": False, "message": "原文件不存在"}
        if new_file.exists():
            return {"success": False, "message": "新文件名已存在"}
        old_file.rename(new_file)
        return {"success": True, "message": "文件重命名成功"}
    except Exception as e:
        return {"success": False, "message": f"重命名失败: {e}"}

@app.delete("/api/file/{dir_name}/{file_name}")
async def delete_file(dir_name: str, file_name: str):
    """删除文件"""
    try:
        file_path = PROJECT_ROOT / dir_name / file_name
        if not file_path.exists():
            return {"success": False, "message": "文件不存在"}
        file_path.unlink()
        return {"success": True, "message": "文件删除成功"}
    except Exception as e:
        return {"success": False, "message": f"删除失败: {e}"}

def generate_ai_response(message: str, current_file: str = None, current_code: str = "", current_dir: str = None, messages: list = None) -> dict:
    """生成AI回复，返回解释和代码两部分"""
    prompt = message
    abs_dir = None
    if current_dir:
        abs_dir = str((PROJECT_ROOT / current_dir).resolve())
    # 你可以在这里用messages做上下文拼接
    content, code = llm.llm_gen_code(prompt, abs_dir, messages)
    # print(content)
    return {
        "explanation": content,
        "code": code or "# AI未能提取出代码"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
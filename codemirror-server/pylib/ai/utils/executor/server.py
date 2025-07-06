
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import traceback
import os, sys, io

DEFAULT_PORT = 8860

app = FastAPI()

class CodeRequest(BaseModel):
    code: str

@app.post("/execute")
async def execute_code(request: CodeRequest):
    try:
        # 创建一个安全的执行环境
        restricted_globals = {}# {"__builtins__": {}}
        # result = {}

        output = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = output
        exec(request.code, restricted_globals)
        sys.stdout = original_stdout
        output_content = output.getvalue()
        output.close()
        return JSONResponse(content=output_content, status_code=200)
    except Exception as e:
        error_msg = f"代码执行出错：{traceback.format_exc()}"
        print(error_msg)
        # raise HTTPException(status_code=400, detail=error_msg)
        raise JSONResponse(content=traceback.format_exc(), status_code=400)


def run(host="0.0.0.0", port=DEFAULT_PORT):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
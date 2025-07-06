import asyncio
import atexit
import base64
import io
import json
import os
import queue
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid
import threading
from pathlib import Path
from typing import Dict, List, Optional, Union

import json5

from qwen_agent.log import logger
from qwen_agent.tools.base import BaseToolWithFileAccess, register_tool
from qwen_agent.utils.utils import append_signal_handler, extract_code, has_chinese_chars, print_traceback
from qwen_agent.agents import Assistant
from qwen_agent.agents.fncall_agent import FnCallAgent


LAUNCH_KERNEL_PY = """
from ipykernel import kernelapp as app
app.launch_new_instance()
"""

INIT_CODE_FILE = str(Path(__file__).absolute().parent / 'resource' / 'code_interpreter_init_kernel.py')

_KERNEL_CLIENTS: dict = {}
_MISC_SUBPROCESSES: Dict[str, subprocess.Popen] = {}


def _kill_kernels_and_subprocesses(_sig_num=None, _frame=None):
    for v in _KERNEL_CLIENTS.values():
        v.shutdown()
    for k in list(_KERNEL_CLIENTS.keys()):
        del _KERNEL_CLIENTS[k]

    for v in _MISC_SUBPROCESSES.values():
        v.terminate()
    for k in list(_MISC_SUBPROCESSES.keys()):
        del _MISC_SUBPROCESSES[k]


# Make sure all subprocesses are terminated even if killed abnormally:
# If not running in the main thread, (for example run in streamlit)
# register a signal would cause a RuntimeError
if threading.current_thread() is threading.main_thread():
    atexit.register(_kill_kernels_and_subprocesses)
    append_signal_handler(signal.SIGTERM, _kill_kernels_and_subprocesses)
    append_signal_handler(signal.SIGINT, _kill_kernels_and_subprocesses)


class CodeExecutor():
    SYSTEM_INSTRUCTION_FILE = None
    TOOL_NAME = None
    AGENT_NAME = None
    AGENT_DESCRIPTION = None
    PROMPT_SUGGESTIONS = None

    def __init__(self, work_dir='work_dir', copy_dirs=[]):
        self.work_dir: str = work_dir
        self.instance_id: str = str(uuid.uuid4())
        self.pid = os.getpid()
        _check_deps_for_code_interpreter()
        for dir_name in copy_dirs:
            self.copy_dir(dir_name)

    def copy_dir(self, src_dir):
        dst_dir = os.path.join(self.work_dir, src_dir)
        shutil.copytree(src_dir, dst_dir,symlinks=True, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'), dirs_exist_ok=True)

    def get_init_code(self):
        with open(INIT_CODE_FILE, encoding='utf-8') as fin:
            start_code = fin.read()
            start_code += '\n%xmode Plain' # Plain mode, Minimal mode, Context mode, Verbose mode
        return start_code

    def get_run_code(self, code, files=None):
        return code

    def call(self, code: str, timeout: Optional[int] = 30, **kwargs) -> str:
        if not code.strip():
            return ''

        kernel_id: str = f'{self.instance_id}_{self.pid}'
        if kernel_id in _KERNEL_CLIENTS:
            kc = _KERNEL_CLIENTS[kernel_id]
        else:
            kc, subproc = self._start_kernel(kernel_id)
            start_code = self.get_init_code()
            logger.info(self._execute_code(kc, start_code))
            _KERNEL_CLIENTS[kernel_id] = kc
            _MISC_SUBPROCESSES[kernel_id] = subproc

        run_code = self.get_run_code(code)
        if timeout:
            run_code = f'_M6CountdownTimer.start({timeout})\n{run_code}'

        run_code += '\n\n'  # Prevent code not executing in notebook due to no line breaks at the end
        result = self._execute_code(kc, run_code)

        if timeout:
            self._execute_code(kc, '_M6CountdownTimer.cancel()')

        return result if result.strip() else 'Finished execution.'

    def __del__(self):
        # Recycle the jupyter subprocess:
        k: str = f'{self.instance_id}_{self.pid}'
        if _KERNEL_CLIENTS is not None and k in _KERNEL_CLIENTS:
            _KERNEL_CLIENTS[k].shutdown()
            del _KERNEL_CLIENTS[k]
        if _MISC_SUBPROCESSES is not None and k in _MISC_SUBPROCESSES:
            _MISC_SUBPROCESSES[k].terminate()
            del _MISC_SUBPROCESSES[k]

    def _start_kernel(self, kernel_id: str):
        connection_file = os.path.join(self.work_dir, f'kernel_connection_file_{kernel_id}.json')
        launch_kernel_script = os.path.join(self.work_dir, f'launch_kernel_{kernel_id}.py')
        for f in [connection_file, launch_kernel_script]:
            if os.path.exists(f):
                logger.info(f'WARNING: {f} already exists')
                os.remove(f)

        os.makedirs(self.work_dir, exist_ok=True)
        with open(launch_kernel_script, 'w') as fout:
            fout.write(LAUNCH_KERNEL_PY)

        kernel_process = subprocess.Popen(
            [
                sys.executable,
                os.path.abspath(launch_kernel_script),
                '--IPKernelApp.connection_file',
                os.path.abspath(connection_file),
                # '--matplotlib=inline',
                '--quiet',
            ],
            cwd=os.path.abspath(self.work_dir),
        )
        logger.info(f"INFO: kernel process's PID = {kernel_process.pid}")

        # Wait for kernel connection file to be written
        while True:
            if not os.path.isfile(connection_file):
                time.sleep(0.1)
            else:
                # Keep looping if JSON parsing fails, file may be partially written
                try:
                    with open(connection_file, 'r') as fp:
                        json.load(fp)
                    break
                except json.JSONDecodeError:
                    pass

        # Client
        from jupyter_client import BlockingKernelClient

        kc = BlockingKernelClient(connection_file=connection_file)
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        kc.load_connection_file()
        kc.start_channels()
        kc.wait_for_ready()
        return kc, kernel_process

    def _execute_code(self, kc, code: str) -> str:
        kc.wait_for_ready()
        kc.execute(code)
        result = ''
        image_idx = 0
        while True:
            text = ''
            image = ''
            finished = False
            msg_type = 'error'
            try:
                msg = kc.get_iopub_msg()
                msg_type = msg['msg_type']
                if msg_type == 'status':
                    if msg['content'].get('execution_state') == 'idle':
                        finished = True
                elif msg_type == 'execute_result':
                    text = msg['content']['data'].get('text/plain', '')
                    if 'image/png' in msg['content']['data']:
                        image_b64 = msg['content']['data']['image/png']
                        image_url = self._serve_image(image_b64)
                        image_idx += 1
                        image = '![fig-%03d](%s)' % (image_idx, image_url)
                elif msg_type == 'display_data':
                    if 'image/png' in msg['content']['data']:
                        image_b64 = msg['content']['data']['image/png']
                        image_url = self._serve_image(image_b64)
                        image_idx += 1
                        image = '![fig-%03d](%s)' % (image_idx, image_url)
                    else:
                        text = msg['content']['data'].get('text/plain', '')
                elif msg_type == 'stream':
                    msg_type = msg['content']['name']  # stdout, stderr
                    text = msg['content']['text']
                elif msg_type == 'error':
                    text = _escape_ansi('\n'.join(msg['content']['traceback']))
                    if 'M6_CODE_INTERPRETER_TIMEOUT' in text:
                        text = 'Timeout: Code execution exceeded the time limit.'
            except queue.Empty:
                text = 'Timeout: Code execution exceeded the time limit.'
                finished = True
            except Exception:
                text = 'The code interpreter encountered an unexpected error.'
                print_traceback()
                finished = True
            if text:
                result += f'\n\n{msg_type}:\n\n```\n{text}\n```'
            if image:
                result += f'\n\n{image}'
            if finished:
                break
        result = result.lstrip('\n')
        return result

    def _serve_image(self, image_base64: str) -> str:
        import PIL.Image

        image_file = f'{uuid.uuid4()}.png'
        local_image_file = os.path.join(self.work_dir, image_file)

        png_bytes = base64.b64decode(image_base64)
        assert isinstance(png_bytes, bytes)
        bytes_io = io.BytesIO(png_bytes)
        PIL.Image.open(bytes_io).save(local_image_file, 'png')

        image_server_url = os.getenv('M6_CODE_INTERPRETER_STATIC_URL', '')
        if image_server_url:
            return f'{image_server_url}/{image_file}'
        return local_image_file


def _check_deps_for_code_interpreter():
    try:
        # import matplotlib  # noqa
        # import matplotlib.pyplot as plt  # noqa
        import numpy as np  # noqa
        import pandas as pd  # noqa
        # import PIL.Image  # noqa
        # import seaborn as sns  # noqa
        from jupyter_client import BlockingKernelClient  # noqa
        from sympy import Eq, solve, symbols  # noqa
    except ImportError as e:
        raise ImportError(
            'The dependencies for Code Interpreter support are not installed. '
            'Please install the required dependencies by running: pip install *') from e


def _escape_ansi(line: str) -> str:
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


#
# The _BasePolicy and AnyThreadEventLoopPolicy below are borrowed from Tornado.
# Ref: https://www.tornadoweb.org/en/stable/_modules/tornado/platform/asyncio.html#AnyThreadEventLoopPolicy
#

if sys.platform == 'win32' and hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    _BasePolicy = asyncio.WindowsSelectorEventLoopPolicy  # type: ignore
else:
    _BasePolicy = asyncio.DefaultEventLoopPolicy


class AnyThreadEventLoopPolicy(_BasePolicy):  # type: ignore
    """Event loop policy that allows loop creation on any thread.

    The default `asyncio` event loop policy only automatically creates
    event loops in the main threads. Other threads must create event
    loops explicitly or `asyncio.get_event_loop` (and therefore
    `.IOLoop.current`) will fail. Installing this policy allows event
    loops to be created automatically on any thread.

    Usage::
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
    """

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        try:
            return super().get_event_loop()
        except RuntimeError:
            # "There is no current event loop in thread %r"
            loop = self.new_event_loop()
            self.set_event_loop(loop)
            return loop


if __name__ == '__main__':

    code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)
plt.show()
"""
    
    executor = CodeExecutor()
    result = executor.call(code)
    print(result)

import io
import contextlib

from pathlib import Path

from pylib.ai.llmv2 import LLM
from pylib.ai.utils.executor.extract import extract_code_from_markdown

from helper.lparser.op import get_op_infos, op_reset

RUN_CODE_FILE = str(Path(__file__).absolute().parent / 'resource' / 'run_code.py')
SYSTEM_INSTRUCTION_FILE = str(Path(__file__).absolute().parent / 'resource' / 'system_instruction.txt')
DEFAULT_FILE = str(Path(__file__).absolute().parent / 'resource' / '2k.log')


def _extract_code(content):
    codes = extract_code_from_markdown(content)
    python_code = None
    python_codes = codes.get('python') or codes.get('inline')
    if python_codes:
        python_code = python_codes[0]

    return python_code


def _llm(model, system_prompt, user_prompt, history=None):
    llm = LLM(model)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        for message in history:
            if message['role'] == 'ai':
                message['role'] = 'assistant'
            messages.append(message)

    messages.append({"role": "user", "content": user_prompt})

    messages = llm.stream(messages)

    for message in messages:
        pass

    return message['content']


def llm_gen_code(prompt, current_dir, history=None):
    model = 'qwen-max'

    format_file = str((Path(current_dir) / 'format.jsonl').resolve())
    op_maps = op_reset(format_file)

    with open(SYSTEM_INSTRUCTION_FILE, encoding='utf-8') as fin:
        system_instruction = fin.read()
        system_instruction = system_instruction.replace('### OP_INFOS ###', '\n'.join(get_op_infos(op_maps)))

    content = _llm(model, system_instruction, prompt, history)

    code = _extract_code(content)

    return content, code
    

def gen_full_code(code, current_dir, files=None):
    format_file = str((Path(current_dir) / 'format.jsonl').resolve())

    # if files is None:
        # files = [DEFAULT_FILE, ]

    with open(RUN_CODE_FILE, encoding='utf-8') as fin:
        run_code = fin.read()
        run_code = run_code.replace('### <FORMAT_FILE> ###', 'format_file = "' + format_file + '"')
        run_code = run_code.replace('### <FILES> ###', 'files = ' + str(files))
        run_code = run_code.replace('### <CODE> ###', code)
    return run_code


def run_code(code):
    buf = io.StringIO()
    try:
        global_vars = {}
        with contextlib.redirect_stdout(buf):
            exec(code, global_vars)

        output = None
        if global_vars['result']:
            output = buf.getvalue()
    except Exception as e:
        output = f"执行出错: {e}"
    return output
import re

def extract_code_from_markdown(markdown_text):
    """
    从Markdown文本中提取代码块和行内代码。
    参数:
        markdown_text (str): Markdown格式的文本。
    返回:
        dict: 包含代码块和行内代码的列表。
    """
    # 匹配代码块（包括语言标识和代码内容）
    block_pattern = r"```(\w+)?\n([\s\S]+?)\n```"
    # 匹配行内代码
    inline_pattern = r"`([^`\n]+)`"

    result = {}
    # 先匹配代码块
    for match in re.finditer(block_pattern, markdown_text):
        language = match.group(1) if match.group(1) else "plaintext"
        code = match.group(2).strip()
        if language not in result:
            result[language] = []
        result[language].append(code)

    # 再匹配行内代码
    for match in re.finditer(inline_pattern, markdown_text):
        if language not in result:
            result[language] = []
        result[language].append(code)

    if not result:
        if is_python_code(markdown_text):
            result["python"] = [markdown_text]

    return result

def is_python_code(code_str):
    try:
        compile(code_str, '<string>', 'exec')
        return True
    except SyntaxError:
        return False
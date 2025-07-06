import os
import re
from openai import OpenAI


MODELS = {
    "gpt-4": "openai/gpt-4",
    "qwen-plus": "qwen-plus",
    "qwen-max": "qwen-max",
}

_OPENAI_COMPATIBLIE_MODELS = [
    {
        "compatible_func": lambda x: x.startswith("qwen-"),
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.environ.get("DASHSCOPE_API_KEY"),
    },
]

class LLM:
    def __init__(self, model, systmem_prompt= None, **kwargs):
        self._client = None
        self._model = MODELS.get(model, model)
        self._api_key = kwargs.get('api_key')
        self._api_base = kwargs.get('api_base')
        self._compatible_openai_model()
        self.system_prompt = systmem_prompt
        self.reset()

    def reset(self):
        self.messages = []
        if self.system_prompt is not None:
            self.messages.append({ "content": self.system_prompt,"role": "system"})

    def _compatible_openai_model(self):
        for compatible in _OPENAI_COMPATIBLIE_MODELS:
            compatible_func = compatible['compatible_func']
            if compatible_func(self._model):
                self._api_base = compatible['api_base']
                self._api_key = self._api_key if self._api_key else compatible['api_key']
                self._client = OpenAI(api_key=self._api_key, base_url=self._api_base)

    def _completion(self, message_or_prompt, stream=False, delta=False):
        def simplify_iter(response):
            content = ''
            role = ''
            for item in response:
                delta_content = item.choices[0].delta.content
                delta_role = item.choices[0].delta.role
                if delta:
                    yield {'content': delta_content, 'role': delta_role}
                else:
                    if delta_content is not None:
                        content += delta_content
                    if delta_role is not None:
                        role = delta_role
                    yield {'content': content, 'role': role}

        if isinstance(message_or_prompt, str):
            message = { "content": message_or_prompt,"role": "user"}
            messages = [message]
        elif isinstance(message_or_prompt, dict):
            message = message_or_prompt
            messages = [message]
        elif isinstance(message_or_prompt, list):
            messages = message_or_prompt
        
        if self._client is not None:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=stream,
            )
        else:
            raise Exception("no compatible model")

        if stream:
            response = simplify_iter(response)
        else:
            response = {'content': response.choices[0].message.content, 'role': response.choices[0].message.role}

        return response

    def __call__(self, message_or_prompt):
        response = self._completion(message_or_prompt, False)
        return response

    def stream(self, message_or_prompt, delta=False):
        response = self._completion(message_or_prompt, True, delta)
        return response

    @staticmethod
    def content_filter(content):
        matches = re.findall(r'```(.*?)\n(.*?)\n```', content, re.DOTALL)
        if matches:
            results = []
            for match in matches:
                type = match[0].strip()
                content_ = match[1].strip()
                results.append({ 'type': type, 'content': content_})
            return results
        return None


if __name__ == '__main__':
    if False:
        llm = LLM("qwen-max")
        prompt = "请帮我生成一个python代码，匹配以下字符串：\n\n"
        prompt += "1. 2023-10-01\n"
        message = llm(prompt)
        print("message:")
        print(message)
        print('code:')
        print(llm.content_filter(message['content']))

        message = '''
    ```regex
    ^\d{4}-\d{2}-\d{2}$
    ```
    ```regex
    ^\d{4}-\d{2}-\d{2}$
    ```
    '''
        regexs = llm.content_filter(message)
        print('regexs:')
        print(regexs)
    else:
        llm = LLM("qwen-max")
        prompt = "请帮我生成一个python代码，匹配以下字符串：\n\n"
        prompt += "1. 2023-10-01\n"
        message = llm.stream(prompt)
        print("message:")
        for m in message:
            print(m)


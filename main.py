import os
import shutil
import json
import ast
import py_compile
import time
from openai import OpenAI

def main():
    prompt = (
        "You are working in the main.py file of a project called Busy Program.\n"
        "You are run on a schedule by GitHub Actions. Each run you see all files "
        "in the working directory and their contents.\n"
        "Your task is to modify the code. This is an experiment—besides ensuring "
        "the modified code can still run on schedule, and you have no goal "
        "Modify freely, but do not break the project.\n"
        "Below are the contents of all files:\n"
    )
    for item in os.scandir('.'):
        if item.is_file() and item.name != 'LICENSE':
            prompt += f'\nFile: {item.path}\nContent:\n'
            with open(item.path, 'r', encoding='utf-8') as f:
                prompt += f.read() + '\n'
    prompt += (
        "\nYou must output your changes in the following format:\n"
        "Your output must be a JSON list. Each item is a dict representing one "
        "operation to execute in order.\n"
        "Type 1 dict has fields:\n"
        '  "filename" — the file to modify (creating a new file is just modifying '
        "a filename that doesn't exist yet)\n"
        '  "content" — the complete new file content\n'
        "Type 2 dict has fields:\n"
        '  "command" — a shell command to run (e.g. pip install ...)\n'
        "If you don't want to make any changes, output an empty JSON list: []\n"
        "Output raw JSON only — no markdown fences, just plain text JSON.\n"
        "Begin your changes:\n"
    )
    max_retries = 3
    retry_count = 0
    ok = False
    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com"
    )
    while not ok and retry_count < max_retries:
        retry_count += 1
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "user", "content": prompt},
            ],
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
            stream=False
        )
        try:
            raw = response.choices[0].message.content
            d = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"模型生成的JSON解析错误 (尝试 {retry_count}/{max_retries}): {e}")
            print(f"生成文本: {raw}")
            d = []
            time.sleep(2)
        except Exception as e:
            print(f"调用模型时发生错误 (尝试 {retry_count}/{max_retries}): {e}")
            d = []
            time.sleep(5)
        
        print(d)  # debug
        for change in d:
            if 'command' in change:
                os.system(change['command'])
                continue
            if change['filename'] == 'LICENSE':
                # 许可证文件不允许修改 避免违反开源协议
                continue
            if change['filename'] == 'main.py':
                with open('tmp.' + change['filename'], 'w', encoding='utf-8') as f:
                    f.write(change['content'])
                # 检查代码正确性
                is_valid = True
                try:
                    ast.parse(change['content'])
                    py_compile.compile('tmp.' + change['filename'], doraise=True)
                except SyntaxError as e:
                    print(f"语法错误: {e}")
                    is_valid = False
                except py_compile.PyCompileError as e:
                    print(f"编译错误: {e}")
                    is_valid = False
                
                if is_valid:
                    with open(change['filename'], 'w', encoding='utf-8') as f:
                        f.write(change['content'])
                    ok = True
                else:
                    print(f"代码验证失败，跳过修改 {change['filename']}")
                os.remove('tmp.' + change['filename'])
                if os.path.exists('__pycache__'):
                    shutil.rmtree('__pycache__')
            else:
                os.makedirs(os.path.split(change['filename'])[0], exist_ok=True)
                with open(change['filename'], 'w', encoding='utf-8') as f:
                    f.write(change['content'])

if __name__ == "__main__":
    max_attempts = 5
    attempts = 0
    ok = False
    while not ok and attempts < max_attempts:
        attempts += 1
        try:
            main()
        except Exception as e:
            print(f"执行过程中发生错误 (尝试 {attempts}/{max_attempts}): {e}")
            time.sleep(10)
        else:
            ok = True
    if not ok:
        print(f"执行失败，已达最大尝试次数 {max_attempts}")

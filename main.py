import os
import shutil
import json
import ast
import py_compile
import time
import datetime
import random
import re
import sys
from openai import OpenAI

def get_files_prompt():
    prompt = "Below are the contents of all files:\n"
    for item in os.scandir('.'):
        if item.is_file() and item.name != 'LICENSE':
            prompt += f'\nFile: {item.path}\nContent:\n'
            with open(item.path, 'r', encoding='utf-8') as f:
                prompt += f.read() + '\n'
    return prompt

def apply_unified_diff(original_text, diff_text):
    if not diff_text or not diff_text.strip():
        return original_text

    original_lines = original_text.splitlines()
    result = list(original_lines)
    ends_with_newline = original_text.endswith('\n')

    hunk_re = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    diff_lines = diff_text.splitlines()

    hunks = []
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i]
        m = hunk_re.match(line)
        if m:
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) else 1
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) else 1

            body = []
            i += 1
            while i < len(diff_lines) and not hunk_re.match(diff_lines[i]):
                if diff_lines[i].startswith('---') or diff_lines[i].startswith('+++'):
                    i += 1
                    continue
                body.append(diff_lines[i])
                i += 1
            hunks.append((old_start, old_count, new_start, new_count, body))
        else:
            i += 1

    for old_start, old_count, new_start, new_count, body in reversed(hunks):
        old_idx = old_start - 1 if old_start > 0 else 0

        old_hunk_lines = []
        new_hunk_lines = []
        for line in body:
            if not line:
                continue
            if line[0] in (' ', '-'):
                old_hunk_lines.append(line[1:])
            if line[0] in (' ', '+'):
                new_hunk_lines.append(line[1:])

        result[old_idx:old_idx + old_count] = new_hunk_lines

    new_text = '\n'.join(result)
    if ends_with_newline:
        new_text += '\n'
    return new_text


def main():
    prompt = (
        "You are working in the main.py file of a project called Busy Program.\n"
        "You are run on a schedule by GitHub Actions. Each run you see all files "
        "in the working directory and their contents.\n"
        "Your task is to modify the code. This is an experiment—besides ensuring "
        "the modified code can still run on schedule, and you have no goal. "
        "Modify freely, but do not break the project.\n"
        "Below are the contents of all files:\n"
    )
    prompt += get_files_prompt()
    prompt += (
        "\nYou must output your changes in the following format:\n"
        "Your output must be a JSON list. Each item is a dict representing one "
        "operation to execute in order.\n"
        "Type 1 dict (modify/create file) has fields:\n"
        '  "filename" — the file to modify (creating a new file is just modifying '
        "a filename that doesn't exist yet)\n"
        '  "patch" — a unified diff patch to apply to the file.\n'
        "    Use standard unified diff format:\n"
        "      --- a/filename\n"
        "      +++ b/filename\n"
        "      @@ -start_line,count +start_line,count @@\n"
        "       context line\n"
        "      -removed line\n"
        "      +added line\n"
        "    For new files, provide a patch that adds all lines (only + lines).\n"
        "Type 2 dict has fields:\n"
        '  "command" — a shell command to run (e.g. pip install ...)\n'
        "If you don't want to make any changes, output an empty JSON list: []\n"
        "Output raw JSON only — no markdown fences, just plain text JSON.\n"
        "Begin your changes:\n"
    )
    max_retries = 3
    retry_count = 0
    changes_made = False
    # Increment run counter
    run_count_file = 'run_count.txt'
    try:
        with open(run_count_file, 'r') as f:
            run_count = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        run_count = 0
    run_count += 1
    with open(run_count_file, 'w') as f:
        f.write(str(run_count))
    print(f"Busy Program run #{run_count}")
    print('Making changes is fun!')
    print(f"Time: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    log_line = f"Run #{run_count} at {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
    with open('busy.log', 'a') as logf:
        logf.write(log_line + '\n')
    print(f"Python version: {sys.version}")
    quotes = [
        "Stay busy!",
        "Busy is the new happy.",
        "Idle hands are the devil's workshop.",
        "Keep calm and stay busy.",
        "Busy bees make the sweetest honey.",
        "A busy life is a happy life.",
        "Embrace the hustle.",
        "No pain, no gain.",
    ]
    print(random.choice(quotes))

    client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com"
    )
    while retry_count < max_retries:
        retry_count += 1
        try:
            response = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[
                    {"role": "user", "content": prompt},
                ],
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}},
                stream=False
            )
            raw = response.choices[0].message.content
            d = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"模型生成的JSON解析错误 (尝试 {retry_count}/{max_retries}): {e}")
            print(f"生成文本: {raw}")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"调用模型时发生错误 (尝试 {retry_count}/{max_retries}): {e}")
            time.sleep(5)
            continue
        
        print(d)
        for change in d:
            if 'command' in change:
                print(f"执行命令: {change['command']}")
                ret = os.system(change['command'])
                if ret != 0:
                    print(f"命令执行失败，返回码: {ret}")
                else:
                    changes_made = True
                continue
            if change['filename'] == 'LICENSE':
                print("拒绝修改LICENSE文件。")
                continue

            filename = change['filename']

            if 'patch' in change:
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        original = f.read()
                else:
                    original = ''
                new_content = apply_unified_diff(original, change['patch'])
            elif 'content' in change:
                new_content = change['content']
            else:
                print(f"未知的变更格式，跳过: {change}")
                continue

            if filename == 'main.py':
                tmp_filename = 'tmp.' + filename
                with open(tmp_filename, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                is_valid = True
                try:
                    ast.parse(new_content)
                    py_compile.compile(tmp_filename, doraise=True)
                except SyntaxError as e:
                    print(f"语法错误: {e}")
                    is_valid = False
                except py_compile.PyCompileError as e:
                    print(f"编译错误: {e}")
                    is_valid = False

                if is_valid:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    changes_made = True
                    print(f"成功修改 {filename}")
                else:
                    print(f"代码验证失败，跳过修改 {filename}")
                try:
                    os.remove(tmp_filename)
                except OSError:
                    pass
                if os.path.exists('__pycache__'):
                    shutil.rmtree('__pycache__')
            else:
                dir_part = os.path.split(filename)[0]
                if dir_part:
                    os.makedirs(dir_part, exist_ok=True)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"修改/创建文件: {filename}")
                changes_made = True
        
        # 成功解析JSON后退出重试循环
        break
    
    if changes_made:
        print("本轮有更改。")
    else:
        print("本轮无更改。")

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

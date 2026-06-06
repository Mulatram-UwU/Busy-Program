import os
import shutil
import json
import ast
import py_compile
# 导入本地模型相关
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# 全局变量用于缓存模型
_model = None
_tokenizer = None
_generator = None

def load_local_model():
    """加载本地语言模型"""
    global _model, _tokenizer, _generator
    if _generator is not None:
        return
    model_name = "distilgpt2"  # 使用DistilGPT-2，一个小型模型
    try:
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForCausalLM.from_pretrained(model_name)
        _generator = pipeline('text-generation', model=_model, tokenizer=_tokenizer)
    except Exception as e:
        print(f"加载本地模型失败: {e}")
        raise

def local_model_call(prompt):
    """调用本地模型生成响应"""
    global _generator
    if _generator is None:
        load_local_model()
    
    # 设置生成参数
    response = _generator(
        prompt,
        num_return_sequences=1,
        temperature=0.7,
        do_sample=True,
        pad_token_id=_tokenizer.eos_token_id  # 设置填充令牌
    )
    if not response or len(response) == 0:
        raise IndexError("模型返回了空结果列表")
    generated_text = response[0]['generated_text']
    # 提取新生成的部分（移除提示）
    if generated_text.startswith(prompt):
        json_text = generated_text[len(prompt):].strip()
    else:
        json_text = generated_text.strip()  # 如果模型没有重复提示，则使用全部
    return json_text

def main():
    prompt = (
        "You are working in the main.py file of a project called Busy Program.\n"
        "You are run on a schedule by GitHub Actions. Each run you see all files "
        "in the working directory and their contents.\n"
        "Your task is to modify the code. This is an experiment—besides ensuring "
        "the modified code can still run on schedule, your goal is to write your "
        "own language model implementation to eventually replace this API-based "
        "approach. Modify freely, but do not break the project.\n"
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

    import time
    if _tokenizer is None:
        load_local_model()
    MODEL_MAX_TOKENS = _model.config.max_position_embeddings
    MAX_NEW_TOKENS = 256
    token_count = len(_tokenizer.encode(prompt))
    max_input_tokens = MODEL_MAX_TOKENS - MAX_NEW_TOKENS
    if token_count > max_input_tokens:
        print(
            f"Prompt token count ({token_count}) exceeds model input limit "
            f"({max_input_tokens} tokens, {MODEL_MAX_TOKENS} context - "
            f"{MAX_NEW_TOKENS} generation budget). Aborting."
        )
        return
    print(f"Prompt tokens: {token_count} (limit: {max_input_tokens})")

    max_retries = 3
    retry_count = 0
    ok = False
    while not ok and retry_count < max_retries:
        retry_count += 1
        try:
            json_text = local_model_call(prompt)
            d = json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"本地模型生成的JSON解析错误 (尝试 {retry_count}/{max_retries}): {e}")
            print(f"生成文本: {json_text}")
            d = []
            time.sleep(2)
        except Exception as e:
            print(f"调用本地模型时发生错误 (尝试 {retry_count}/{max_retries}): {e}")
            d = []
            time.sleep(5)
        
        if not ok and retry_count >= max_retries:
            print(f"模型调用失败，已重试 {max_retries} 次，退出")
            return
        
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
                with open(change['filename'], 'w', encoding='utf-8') as f:
                    f.write(change['content'])

if __name__ == "__main__":
    import time
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

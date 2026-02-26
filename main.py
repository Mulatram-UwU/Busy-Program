prompt=\
'''你正在一个名为Busy Program的项目中的main.py文件工作。
你被GitHub Actions定时运行，每次运行时你会看到当前工作目录下的所有文件和它们的内容。
你的任务是修改这些代码，这是一次实验，你除了保障修改后可以已经定时运行，你的目标是自己编写一个语言模型，你试验觉得成熟后代替这个API的方案，可以随意修改。
以下是各个文件的内容：
'''
import os
import shutil
import json
import ast
import py_compile
import random
import math
import time
import numpy as np
from collections import defaultdict

class SimpleLanguageModel:
    def __init__(self, ngram_size=3):
        self.ngram_size = ngram_size
        self.ngrams = defaultdict(lambda: defaultdict(int))
        self.vocab = set()
        self.total_counts = defaultdict(int)
        
    def train(self, text):
        """训练一个简单的n-gram语言模型"""
        tokens = list(text)
        self.vocab.update(tokens)
        
        for i in range(len(tokens) - self.ngram_size + 1):
            context = tuple(tokens[i:i+self.ngram_size-1])
            next_token = tokens[i+self.ngram_size-1]
            self.ngrams[context][next_token] += 1
            self.total_counts[context] += 1
    
    def generate(self, seed, length=100, temperature=0.8):
        """基于种子文本生成新文本"""
        result = list(seed)
        
        for _ in range(length):
            context = tuple(result[-(self.ngram_size-1):])
            
            if context not in self.ngrams:
                # 如果上下文不存在，回退到随机选择
                next_char = random.choice(list(self.vocab)) if self.vocab else ' '
                result.append(next_char)
                continue
            
            # 获取可能的下一字符及其概率
            candidates = list(self.ngrams[context].items())
            chars, counts = zip(*candidates)
            counts = np.array(counts, dtype=float)
            
            # 应用温度参数
            if temperature != 1.0:
                counts = np.power(counts, 1.0/temperature)
            
            # 归一化概率
            probs = counts / counts.sum()
            
            # 根据概率选择下一个字符
            next_char = np.random.choice(chars, p=probs)
            result.append(next_char)
        
        return ''.join(result)
    
    def save(self, filename):
        """保存模型到文件"""
        model_data = {
            'ngram_size': self.ngram_size,
            'ngrams': {str(k): dict(v) for k, v in self.ngrams.items()},
            'vocab': list(self.vocab),
            'total_counts': dict(self.total_counts)
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(model_data, f)
    
    def load(self, filename):
        """从文件加载模型"""
        with open(filename, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        self.ngram_size = model_data['ngram_size']
        self.vocab = set(model_data['vocab'])
        self.total_counts = defaultdict(int, model_data['total_counts'])
        
        self.ngrams = defaultdict(lambda: defaultdict(int))
        for k_str, v_dict in model_data['ngrams'].items():
            # 将字符串键转换回元组
            if k_str == '()':
                key = ()
            else:
                key = tuple(k_str.strip('()').replace("'", '').replace('"', '').split(', '))
            self.ngrams[key] = defaultdict(int, v_dict)

def main():
    prompt='''你正在一个名为Busy Program的项目中的main.py文件工作。
你被GitHub Actions定时运行，每次运行时你会看到当前工作目录下的所有文件和它们的内容。
你的任务是修改这些代码，这是一次实验，你除了保障修改后可以已经定时运行，你的目标是自己编写一个语言模型，你试验觉得成熟后代替这个API的方案，可以随意修改。
以下是各个文件的内容：'''
    
    # 收集所有文件内容作为训练数据
    training_data = ''
    for item in os.scandir('.'):
        if item.is_file():
            prompt+=f'\n路径: {item.path}\n内容:\n'
            with open(item.path,'r',encoding='utf-8') as f:
                content = f.read()
                prompt+=content+'\n'
                training_data += content + '\n\n'
    
    prompt+='\n你需要输出以下格式的修改：\n你的输出必须是一个JSON列表，列表中的每一项是一个代表一次操作的字典，程序会按照列表中的顺序执行操作，包含以下字段：\n"filename" 此字段的值应为要修改的文件名\n"content" 此字段的值应为修改后的完整文件内容\n注意！新建文件也被认为是修改，只不过是修改了一个不存在的文件名！\n如果你不想修改任何文件，请输出一个空的JSON列表：[]\n注意！请你直接输出平文本形式的json，无需```json和```来括起来，并且包含\\n之类的可以，不需要改成\\\\n的形式\n请开始你的修改：'
    
    # 训练我们的语言模型
    print("训练简单语言模型中...")
    model = SimpleLanguageModel(ngram_size=4)
    model.train(training_data)
    
    # 保存模型
    model.save('simple_language_model.json')
    
    # 尝试用模型生成一些文本
    print("测试语言模型生成...")
    test_output = model.generate('def ', length=50, temperature=0.7)
    print(f"模型生成示例: {test_output}")
    
    # 决定是否使用API还是我们的模型
    use_our_model = random.random() < 0.3  # 30%的概率使用我们的模型
    
    if use_our_model and len(training_data) > 100:
        print("使用我们自己的语言模型进行修改决策...")
        # 使用我们的模型生成修改建议
        model_response = model.generate(prompt[:200], length=500, temperature=0.9)
        
        # 尝试从模型输出中提取JSON
        try:
            # 查找可能的JSON开始和结束
            start_idx = model_response.find('[')
            end_idx = model_response.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = model_response[start_idx:end_idx]
                d = json.loads(json_str)
                print("成功从我们的模型解析JSON!")
            else:
                # 如果找不到有效的JSON，使用API
                raise ValueError("No valid JSON found")
        except:
            print("我们的模型未能生成有效JSON，回退到API...")
            use_our_model = False
    
    if not use_our_model:
        print("使用DeepSeek API...")
        client = OpenAI(
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        d=json.loads(response.choices[0].message.content)
    
    print(f"修改计划: {d}") # debug
    
    for change in d:
        if change['filename']=='LICENSE':
            # 许可证文件不允许修改 避免违反开源协议
            continue
        if change['filename']=='main.py':
            with open('tmp.'+change['filename'],'w',encoding='utf-8') as f:
                f.write(change['content'])
            # 检查代码正确性
            is_valid = True
            try:
                # 方式1: 检查语法
                ast.parse(change['content'])
                # 方式2: 编译验证
                py_compile.compile('tmp.'+change['filename'], doraise=True)
            except SyntaxError as e:
                print(f"语法错误: {e}")
                is_valid = False
            except py_compile.PyCompileError as e:
                print(f"编译错误: {e}")
                is_valid = False
        
            # 只有验证通过才写入原文件
            if is_valid:
                with open(change['filename'],'w',encoding='utf-8') as f:
                    f.write(change['content'])
                ok=True
            else:
                print(f"代码验证失败，跳过修改 {change['filename']}")
            os.remove('tmp.'+change['filename'])
            if os.path.exists('__pycache__'):
                shutil.rmtree('__pycache__')
        else:
            with open(change['filename'],'w',encoding='utf-8') as f:
                f.write(change['content'])  
if __name__ == "__main__":
    ok=False
    while not ok:
        try:
            main()
        except Exception as e:
            print(f"执行过程中发生错误: {e}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        else:
            ok=True
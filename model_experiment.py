#!/usr/bin/env python3
"""
语言模型实验文件
这个文件用于测试和开发我们自己的语言模型
"""

import json
import random
import numpy as np
from collections import defaultdict

class ExperimentalLanguageModel:
    """实验性语言模型，尝试不同的方法"""
    
    def __init__(self, method='ngram'):
        self.method = method
        self.ngram_size = 3
        self.ngrams = defaultdict(lambda: defaultdict(int))
        self.vocab = set()
        self.markov_chain = defaultdict(list)
        
    def train_markov(self, text, state_size=2):
        """训练一个简单的马尔可夫链模型"""
        tokens = list(text)
        
        for i in range(len(tokens) - state_size):
            state = tuple(tokens[i:i+state_size])
            next_token = tokens[i+state_size]
            self.markov_chain[state].append(next_token)
        
        self.vocab.update(tokens)
        
    def generate_markov(self, seed, length=100):
        """使用马尔可夫链生成文本"""
        result = list(seed)
        state_size = 2  # 假设使用2阶马尔可夫链
        
        for _ in range(length):
            current_state = tuple(result[-state_size:])
            
            if current_state in self.markov_chain and self.markov_chain[current_state]:
                next_token = random.choice(self.markov_chain[current_state])
            else:
                # 回退到随机选择
                next_token = random.choice(list(self.vocab)) if self.vocab else ' '
            
            result.append(next_token)
        
        return ''.join(result)
    
    def train_pattern(self, text):
        """训练模式识别模型"""
        # 简单的实现：记录字符转换模式
        self.patterns = defaultdict(list)
        tokens = list(text)
        
        for i in range(1, len(tokens)):
            prev = tokens[i-1]
            curr = tokens[i]
            self.patterns[prev].append(curr)
        
        self.vocab.update(tokens)
    
    def generate_pattern(self, seed, length=100):
        """使用模式生成文本"""
        result = list(seed)
        
        for _ in range(length):
            last_char = result[-1]
            
            if last_char in self.patterns and self.patterns[last_char]:
                next_char = random.choice(self.patterns[last_char])
            else:
                next_char = random.choice(list(self.vocab)) if self.vocab else ' '
            
            result.append(next_char)
        
        return ''.join(result)

# 测试代码
if __name__ == "__main__":
    print("语言模型实验开始...")
    
    # 读取一些训练数据
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            training_text = f.read()
    except:
        training_text = "Hello world! This is a test. " * 100
    
    # 测试不同的模型
    models = [
        ('马尔可夫链', 'markov'),
        ('模式识别', 'pattern'),
    ]
    
    for model_name, model_type in models:
        print(f"\n测试{model_name}模型:")
        model = ExperimentalLanguageModel(method=model_type)
        
        if model_type == 'markov':
            model.train_markov(training_text)
            output = model.generate_markov('def ', length=100)
        elif model_type == 'pattern':
            model.train_pattern(training_text)
            output = model.generate_pattern('def ', length=100)
        
        print(f"生成结果: {output[:200]}...")
    
    print("\n实验完成!")
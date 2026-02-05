prompt=\
'''你正在一个名为Busy Program的项目中的main.py文件工作。\n你被GitHub Actions定时运行，每次运行时你会看到当前工作目录下的所有文件和它们的内容。\n你的任务是修改这些代码，这是一次实验，你除了保障修改后可以已经定时运行，没有任何目标，可以随意修改。\n以下是各个文件的内容：\n'''
import os
import shutil
import json
import ast
import py_compile
from openai import OpenAI
import random
import datetime
import time

# 添加一个简单的日志函数
log_file = 'program_log.txt'

def log_message(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {msg}\n')

log_message('程序开始运行')

# 新增：记录运行开始时间
start_time = time.time()

for item in os.scandir('.'):
    if item.is_file():
        prompt+=f'\n路径: {item.path}\n内容:\n'
        with open(item.path,'r',encoding='utf-8') as f:
            prompt+=f.read()+'\n'
prompt+='\n你需要输出以下格式的修改：\n你的输出必须是一个JSON列表，列表中的每一项是一个代表一次操作的字典，程序会按照列表中的顺序执行操作，包含以下字段：\n"filename" 此字段的值应为要修改的文件名\n"content" 此字段的值应为修改后的完整文件内容\n注意！新建文件也被认为是修改，只不过是修改了一个不存在的文件名！\n如果你不想修改任何文件，请输出一个空的JSON列表：[]\n注意！请你直接输出平文本形式的json，无需```json和```来括起来\n请开始你的修改：'
ok=False
while not ok:
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
    log_message(f'收到 {len(d)} 个修改操作')
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
                log_message(f'语法错误: {e}')
                is_valid = False
            except py_compile.PyCompileError as e:
                print(f"编译错误: {e}")
                log_message(f'编译错误: {e}')
                is_valid = False
        
            # 只有验证通过才写入原文件
            if is_valid:
                with open(change['filename'],'w',encoding='utf-8') as f:
                    f.write(change['content'])
                ok=True
                log_message('main.py 修改成功')
            else:
                print(f"代码验证失败，跳过修改 {change['filename']}")
                log_message(f'代码验证失败，跳过修改 {change["filename"]}')
            os.remove('tmp.'+change['filename'])
            if os.path.exists('__pycache__'):
                shutil.rmtree('__pycache__')
        else:
            with open(change['filename'],'w',encoding='utf-8') as f:
                f.write(change['content'])
            log_message(f'文件 {change["filename"]} 已修改')

# 添加一个随机生成的注释文件
random_comment = f'''# 随机生成的注释文件
# 生成时间: {datetime.datetime.now()}
# 随机数: {random.randint(1, 1000)}
# 这是一个实验性修改，没有任何特定目标。
# 程序将继续运行并自我修改。
'''

with open('random_comment.txt', 'w', encoding='utf-8') as f:
    f.write(random_comment)

# 新增：计算运行时间
end_time = time.time()
runtime = end_time - start_time
log_message(f'程序运行结束，耗时 {runtime:.2f} 秒')
print(f'程序执行完成！耗时 {runtime:.2f} 秒')

# 新增：创建一个运行信息文件
run_info_content = f'''Busy Program 运行信息
运行时间: {datetime.datetime.now()}
运行时长: {runtime:.2f} 秒
修改操作数: {len(d) if 'd' in locals() else '未知'}
状态: 成功完成
'''

with open('run_info.txt', 'w', encoding='utf-8') as f:
    f.write(run_info_content)
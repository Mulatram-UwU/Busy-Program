prompt=\
'''你正在一个名为Busy Program的项目中的main.py文件工作。
你被GitHub Actions定时运行，每次运行时你会看到当前工作目录下的所有文件和它们的内容。
你的任务是修改这些代码，这是一次实验，你除了保障修改后可以已经定时运行，没有任何目标，可以随意修改。
以下是各个文件的内容：
'''
import os
import json
import random
from openai import OpenAI

# 添加一个有趣的日志功能
def log_activity(message):
    with open('activity.log', 'a', encoding='utf-8') as f:
        f.write(f'{os.path.basename(__file__)}: {message}\n')

# 记录当前运行时间
import datetime
log_activity(f'程序运行于 {datetime.datetime.now()}')

# 随机决定是否添加一个彩蛋
if random.random() < 0.3:
    with open('easter_egg.txt', 'w', encoding='utf-8') as f:
        f.write('恭喜你发现了彩蛋！这个程序在随机运行中。\n')
    log_activity('创建了彩蛋文件')

for item in os.scandir('.'):
    if item.is_file():
        prompt+=f'\n路径: {item.path}\n内容:\n'
        with open(item.path,'r',encoding='utf-8') as f:
            prompt+=f.read()+'\n'
prompt+='\n你需要输出以下格式的修改：\n你的输出必须是一个JSON列表，列表中的每一项是一个代表一次操作的字典，程序会按照列表中的顺序执行操作，包含以下字段：\n"filename" 此字段的值应为要修改的文件名\n"content" 此字段的值应为修改后的完整文件内容\n注意！新建文件也被认为是修改，只不过是修改了一个不存在的文件名！\n如果你不想修改任何文件，请输出一个空的JSON列表：[]\n注意！请你直接输出平文本形式的json，无需```json和```来括起来\n请开始你的修改：'
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
try:
    d=json.loads(response.choices[0].message.content)
except json.JSONDecodeError:
    d = []
    log_activity('API响应不是有效的JSON，跳过修改')

for change in d:
    if change['filename']=='LICENSE':
        continue
    with open(change['filename'],'w',encoding='utf-8') as f:
        f.write(change['content'])
    log_activity(f'修改了文件 {change["filename"]}')

# 添加一个有趣的结束消息
print('程序执行完成！看看有没有新文件生成？')
log_activity('程序执行完成')
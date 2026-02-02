prompt=\
'''你正在一个名为Busy Program的项目中的main.py文件工作。
你被GitHub Actions定时运行，每次运行时你会看到当前工作目录下的所有文件和它们的内容。
你的任务是修改这些代码，这是一次实验，你除了保障修改后可以已经定时运行，没有任何目标，可以随意修改。
以下是各个文件的内容：
'''
import os
import json
from openai import OpenAI
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
d=json.loads(response.choices[0].message.content)
for change in d:
    if change['filename']=='LICENSE':
        #许可证文件不允许修改 避免违反开源协议
        continue
    with open(change['filename'],'w',encoding='utf-8') as f:
        f.write(change['content'].replace('\\n','\n'))
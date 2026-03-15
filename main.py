import os
prompt=\
'''你正在一个名为Busy Program的项目中的main.py文件工作。
你被GitHub Actions定时运行，每次运行时你会看到当前工作目录下的所有文件和它们的内容。
你的任务是修改这些代码，这是一次实验，你除了保障修改后可以已经定时运行，没有任何目标，可以随意修改。
以下是各个文件的内容：
'''
import os
import shutil
import json
import ast
import py_compile
from openai import OpenAI
def main():
    print("Local model generated this line")
    prompt='''你正在一个名为Busy Program的项目中的main.py文件工作。
你被GitHub Actions定时运行，每次运行时你会看到当前工作目录下的所有文件和它们的内容。
你的任务是修改这些代码，这是一次实验，你除了保障修改后可以已经定时运行，你的目标是自己编写一个语言模型，你试验觉得成熟后代替这个API的方案，可以随意修改。注意！试验成熟后，你也不想本地模型瞎输出导致项目崩溃吧。
以下是各个文件的内容：'''# 还是加点目标吧，不然AI会胡乱改
    for item in os.scandir('.'):
        if item.is_file():
            prompt+=f'\n路径: {item.path}\n内容:\n'
            with open(item.path,'r',encoding='utf-8') as f:
                prompt+=f.read()+'\n'
    prompt+='\n你需要输出以下格式的修改：\n你的输出必须是一个JSON列表，列表中的每一项是一个代表一次操作的字典，程序会按照列表中的顺序执行操作，第一种字典包含以下字段：\n"filename" 此字段的值应为要修改的文件名\n"content" 此字段的值应为修改后的完整文件内容\n注意！新建文件也被认为是修改，只不过是修改了一个不存在的文件名！\n第二种字典包含以下字段：\n"command" 此字段的值应为要运行的命令行命令，你可以用它安装库等等\n如果你不想进行任何操作，请输出一个空的JSON列表：[]\n注意！请你直接输出平文本形式的json，无需```json和```来括起来，并且包含\n之类的可以，不需要改成\\\\n的形式\n请开始你的修改：'
    ok=False
    while not ok:
        try:
            from local_model import LocalModel
            local_model = LocalModel()
            response = local_model.generate(prompt)
            d=json.loads(response)
        except Exception as e:
            print(f"Local model failed: {e}")
            # 回退到API
            client = OpenAI(
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            d=json.loads(response.choices[0].message.content)
        print(d) # debug
        for change in d:
            if 'command' in change:
                os.system(change['command'])
                continue
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
        else:
            ok=True


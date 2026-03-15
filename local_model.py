import json

class LocalModel:
    def generate(self, prompt):
        # 简单规则：如果提示中包含"自己编写一个语言模型"，则修改main.py添加一行打印
        if "自己编写一个语言模型" in prompt:
            # 从提示中提取main.py的内容
            # 提示格式固定，我们可以假设
            lines = prompt.split('\n')
            main_content = ''
            for i, line in enumerate(lines):
                if line.strip() == '路径: ./main.py':
                    # 找到内容开始
                    j = i + 1
                    while j < len(lines) and lines[j].strip() != '内容:':
                        j += 1
                    if j < len(lines):
                        # 从j+1开始直到下一个路径或结束
                        content_lines = []
                        k = j + 1
                        while k < len(lines) and not lines[k].startswith('路径:'):
                            content_lines.append(lines[k])
                            k += 1
                        main_content = '\n'.join(content_lines)
                        break
            if main_content:
                # 在main函数开头添加一行打印
                # 找到def main():的位置
                if 'def main():' in main_content:
                    # 替换为def main():后加一行
                    modified_content = main_content.replace('def main():', 'def main():\n    print("Local model generated this line")')
                else:
                    # 如果找不到，在文件末尾添加
                    modified_content = main_content + '\nprint("Local model added this line")'
            else:
                # 如果无法提取，返回空修改
                return json.dumps([])
            # 返回修改指令
            modification = [
                {
                    "filename": "main.py",
                    "content": modified_content
                }
            ]
            return json.dumps(modification)
        else:
            return json.dumps([])

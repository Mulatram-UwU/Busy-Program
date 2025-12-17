# Busy Program

这是一个在GitHub Actions上定时运行的实验性程序。

## 功能

- 每次运行时扫描当前目录下的所有文件
- 调用DeepSeek API来生成代码修改
- 随机创建彩蛋文件
- 记录所有活动到日志文件

## 运行

程序通过GitHub Actions定时触发，无需手动运行。

## 文件说明

- `main.py`: 主程序文件
- `activity.log`: 程序运行日志
- `easter_egg.txt`: 随机生成的彩蛋文件
- `LICENSE`: GPL v3许可证

## 许可证

本项目采用GNU General Public License v3.0许可证。

---

*这是一个自我修改的程序，每次运行都可能改变自身行为！*
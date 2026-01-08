既然你已经准备好了 `CodeMerger.spec` 和 `wrap.bat`，说明你支持通过 **PyInstaller** 打包成独立的 Windows 可执行文件（`.exe`）。

这对于那些不想配置 Python 环境的用户来说是一个巨大的加分项。我已经在 README 中新增了 **“下载与安装”** 以及 **“Windows 免安装版”** 的相关说明。

---

# CodeMerger: 让 AI 读懂你的整个工程 🚀

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**CodeMerger** 是一款专为开发者与大语言模型（LLM）交互设计的工程结构互转工具。它能够将复杂的项目目录一键转换为“易于 AI 理解”的 Markdown 格式，并支持将 AI 生成或修改后的内容完美还原回原始文件结构。

---

## 📢 宣传文案：开发者与 AI 对话的“任意门”

> **“还在手动一个一个文件复制给 ChatGPT 吗？”**
>
> 面对庞大的工程，如何让 Claude 或 GPT-4 瞬间掌握全局？你需要一个“上下文桥梁”。
>
> **CodeMerger** 将你的整个项目打包成一张“结构图 + 源码全集”。你可以直接把它丢给 AI，大声告诉它：“这是我的项目，帮我重构它！”。
>
> 当 AI 给出修改建议后，直接将对话中的 Markdown 粘贴回工具，一键**还原/覆盖**本地代码。整个过程丝滑顺畅，不再有遗漏，不再有格式混乱。**不仅支持 Python 源码，更支持打包好的 `.exe` 随开随用！**

---

## ✨ 核心亮点

### 1. 彻底解决“代码块嵌套”灾难
传统的代码合并脚本在遇到包含 Markdown 反引号（` ``` `）的文件时往往会发生解析截断。
**CodeMerger 采用动态栅栏技术**：自动探测内容中最长的反引号链并生成 `N+1` 长度的栅栏，确保嵌套结构在 AI 窗口中完美呈现。

### 2. 状态机精准还原
内置基于栈思想的状态机解析引擎。无论是多深的项目目录，只要符合协议格式，都能精准还原。

### 3. **Windows 独立运行 (EXE)**
提供打包好的 `.exe` 文件，无需安装 Python 环境，双击即用，极大地方便了非 Python 环境下的开发协作。

### 4. 双端覆盖
- **GUI 界面**：专为 Windows 用户设计，支持一键选择、复制、导入/导出。
- **CLI 工具**：专为 Linux/macOS 及自动化脚本设计，轻量级、零依赖。

---

## 🚀 快速开始

### 方式 A：Windows 免安装版 (推荐)
1. 前往 [Releases](https://github.com/truthstriver/Codemerger/releases) 页面下载 `CodeMerger.exe`。
2. 双击运行，即可开始提取或还原项目。
3. *注：如果你想自行打包，可以运行项目根目录下的 `wrap.bat`。*

### 方式 B：Python 脚本运行 (GUI)
1. 确保已安装 Python 3.x。
2. 在根目录执行：`python app.py`。
3. **提取**：选择文件夹 -> 点击“生成 Markdown” -> 点击“复制全部内容” -> 发送给 AI。
4. **还原**：将 AI 回复的内容粘贴到文本框 -> 选择目标路径 -> 点击“写入文件”。

### 方式 C：命令行工具 (CLI)
适用于 Linux 环境或自动化脚本。
```bash
# 导出项目
python code_merger.py -e -i ./my_project -o project_summary.md

# 还原项目
python code_merger.py -r -i project_summary.md -o ./restored_project
```

---

## 📖 适用场景

- **AI 全局代码审查**：将整个项目发给 AI，进行逻辑漏洞扫描。
- **项目重构**：让 AI 看到全貌，统筹规划类与方法之间的依赖关系。
- **跨机器传输**：通过简单的粘贴复制，在不同机器间转移整个小型工程。
- **代码归档**：将零散的代码文件快速打包成单个可读性极强的文本文件。

---

## 📝 Markdown 协议规范

为了保证还原成功，CodeMerger 遵循以下协议：
1. **路径声明**：代码块第一行必须是 `# path/to/file` 格式。
2. **防截断**：外层反引号数量必须多于内容中的反引号（工具已自动处理）。

**示例：**
````markdown
```python
# src/main.py
print("Hello World")
```

````python
# README.md
# My Project
Example: ```print('test')```
````
````

---

## 📦 项目结构

```text
项目分析工具/
    |-- CodeMerger.exe         # 打包好的 Windows 可执行文件 (Release版)
    |-- app.py                 # Tkinter GUI 主程序源码
    |-- CodeMerger.spec        # PyInstaller 打包配置文件
    |-- wrap.bat               # 一键打包脚本
    |-- prompt.md              # 推荐给 AI 的 Prompt (让 AI 按此格式回复)
    |-- 项目分析工具_cli/
        |-- code_merger.py     # 跨平台 CLI 核心脚本
```

## 🛠️ 如何自行打包 EXE

如果你修改了源码并想重新生成 `.exe`：
1. 安装 PyInstaller: `pip install pyinstaller`
2. 双击运行 `wrap.bat`。
3. 打包完成后，在 `dist/` 目录下即可找到 `CodeMerger.exe`。

---

**立即下载，开启你的 AI 增强开发之旅！**

# CodeMerger

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**CodeMerger** 是一个简单的工程结构互转工具。它可以将整个项目目录（包含文件结构和代码内容）合并为一个 Markdown 文件，方便发送给 ChatGPT、Claude 等大语言模型进行全局分析；也可以将 AI 修改后的 Markdown 内容一键还原回本地文件结构。

## ✨ 核心功能

*   **智能防截断**：采用动态栅栏技术（Dynamic Fencing），自动检测代码中连续反引号的数量并生成 `N+1` 层包裹，完美解决 Python/Markdown 文件中包含 ` ``` ` 导致 AI 解析截断的问题。
*   **双向转换**：
    *   **提取 (Extract)**：目录树 + 源码 -> 单个 Markdown 文件。
    *   **还原 (Restore)**：Markdown -> 自动创建目录并写入文件。
*   **Windows 免安装**：提供封装好的 `.exe`，无需 Python 环境即可在 Windows 上直接运行。
*   **双模式**：提供图形界面 (GUI) 和 命令行工具 (CLI)。

## 📥 下载与运行

### 1. Windows 免安装版 (推荐)
无需配置 Python 环境，直接下载使用：
1. 前往 [Releases](https://github.com/truthstriver/Codemerger/releases) 下载最新版的 `CodeMerger.exe`。
2. 双击即可运行。

### 2. Python 源码运行 (GUI)
如果你安装了 Python 环境：
```bash
# 安装依赖 (标准库无需安装，Tkinter 通常内置)
python app.py
```

### 3. 命令行模式 (CLI)
适合 Linux/macOS 用户或集成到自动化脚本中：
```bash
# 导出项目到 Markdown
python code_merger_cli.py -e -i ./my_project -o project.md

# 从 Markdown 还原项目
python code_merger_cli.py -r -i project.md -o ./restored_dir
```

## 📖 使用指南 (GUI)

### 提取 (发送给 AI)
1. 打开软件，左侧会自动加载当前目录树（支持复选框过滤）。
2. 在“目标路径”选择你要提取的项目根目录。
3. 在右侧勾选需要提取的文件类型（如 `.py`, `.md`, `.js` 等）。
4. 点击 **[提取: 生成 Markdown]**。
5. 点击 **[复制全部内容]**，将其粘贴给 AI。

### 还原 (应用 AI 修改)
1. 将 AI 回复的代码块（需符合下述格式）粘贴到软件的文本框中。
2. 确认“目标路径”是你想要写入的文件夹。
3. 点击 **[还原: 写入文件]**。

## 🛠️ 关于打包 (Build)

本项目包含完整的 PyInstaller 打包配置，如果你修改了源码，可以自行生成 `.exe` 文件。

**前提**：安装 PyInstaller (`pip install pyinstaller`)

**步骤**：
1. 在项目根目录双击运行 `wrap.bat`。
2. 等待脚本执行完毕。
3. 在生成的 `dist/` 目录下找到 `CodeMerger.exe`。

*(注：`wrap.bat` 实际上执行了 `pyinstaller CodeMerger.spec`)*

## 📝 格式协议

为了确保工具能正确还原文件，Markdown 内容需遵循以下简单规则（工具生成的内容默认符合此规则，**建议将 `prompt.md` 的内容发给 AI 以要求其遵循**）：

1.  代码块必须注明路径：第一行需为 `# path/filename` 注释。
2.  代码块包裹：使用 Markdown 代码块包裹内容。

**示例：**

````markdown
```python
# src/utils.py
def hello():
    print("Hello World")
```
````

## 📂 项目结构

*   `CodeMerger.exe`: Windows 可执行程序 (Release)
*   `app.py`: GUI 主程序源码 (Tkinter)
*   `code_merger_cli.py`: 命令行核心逻辑
*   `wrap.bat`: Windows 一键打包脚本
*   `CodeMerger.spec`: PyInstaller 配置文件
*   `prompt.md`: 推荐发给 AI 的提示词文件

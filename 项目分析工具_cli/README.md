
# linux_code_merger/README.md
# Code Merger (Linux CLI Version)

这是一个轻量级的 Python 脚本，用于将整个工程目录转换为单个 Markdown 文件，或将 Markdown 文件还原为工程目录。它特别针对包含代码块（如嵌套的反引号）的文件进行了优化。

## 功能特点

1.  **动态栅栏处理**：自动检测源文件内容中的反引号数量，生成 `N+1` 个反引号的代码块，防止 Markdown 渲染错误。
2.  **状态机解析**：还原时使用状态机逻辑，确保即使代码中包含 ```` ``` ```` 也能正确提取，不会被提前截断。
3.  **零依赖**：仅使用 Python 标准库，无需安装 `pip` 包。

## 使用方法

### 1. 导出 (Export)
将指定目录下的代码提取到一个 Markdown 文件中。

```bash
# 语法: python code_merger.py -e -i <源代码目录> -o <目标MD文件>
python code_merger.py -e -i ./my_project -o ./project_backup.md
```

### 2. 还原 (Restore)
读取 Markdown 文件，根据其中的路径注释将其还原为文件结构。

```bash
# 语法: python code_merger.py -r -i <源MD文件> -o <目标还原目录>
python code_merger.py -r -i ./project_backup.md -o ./restored_project
```

## Markdown 格式规范

工具生成的（以及还原时要求的）格式如下：

1.  **代码块包裹**：所有文件必须包含在 ```python (或更多反引号) 块中。
2.  **路径注释**：代码块的第一行**必须**是 `# path/to/file.ext` 格式的注释。
3.  **闭合匹配**：闭合的栅栏长度必须与开始的栅栏长度一致。

示例：

````text
```python
# src/main.py
print("Hello World")
```

````python
# src/utils_with_ticks.py
code = "```text\nInner Block\n```"
````
````

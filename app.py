import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.font as tkfont

class CodeMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python工程结构互转工具 (Stack Parser版 + 文件过滤)")
        self.root.geometry("1100x950")  # 稍微增加高度以容纳过滤面板
        
        # 忽略的目录和文件
        self.IGNORE_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'build', 'dist'}
        self.IGNORE_FILES = {'.DS_Store'}

        # 定义默认支持的文件类型选项 (标签名 -> 后缀列表字符串)
        self.TYPE_OPTIONS = {
            "Python": ".py;.pyw",
            "Markdown": ".md",
            "Text": ".txt",
            "JSON": ".json",
            "YAML": ".yaml;.yml",
            "Web": ".html;.css;.js;.ts",
            "C/C++": ".c;.cpp;.h;.hpp",
            "Java": ".java",
            "Go": ".go"
        }
        self.check_vars = {} # 存储复选框变量

        # 嵌入prompt.md内容作为字符串
        self.PROMPT_CONTENT = """为了让我的自动化工具能够读取并写入这些文件，请严格遵守以下输出格式要求：

### 格式要求（非常重要）：

1.  **目录结构**：
    首先请提供一个 ASCII 格式的项目目录树结构（根目录不要用 `.`，直接显示文件夹名）。
    该目录树不要用反引号包裹。
    
2.  **代码块格式（核心逻辑）**：
    *   所有的代码文件必须包含在 Markdown 的 `python` 代码块中。
    *   **防截断规则（关键）**：如果文件内容本身包含 **N 个连续的反引号**（例如 ` ``` `），请务必使用 **N+1 个反引号**（例如 ` ```` `）来包裹整个代码块，以确保工具能正确解析嵌套结构。
    *   **路径标识**：每个代码块的 **第一行必须是该文件的相对路径注释**（使用 `/` 作为分隔符）。

    **普通文件示例：**
    ```python
    # src/main.py
    import os
    print("Hello World")
    ```

    **包含反引号的文件示例（注意外层用了4个反引号）：**
    ````python
    # src/string_utils.py
    def get_markdown_snippet():
        return "```text\nSample\n```"
    ````

3.  **完整性**：
    请不要省略代码（不要只写 `pass` 或 `...`），确保代码是可以直接运行的完整版本。

4.  **范围**：
    包括所有必要的文件（如 `requirements.txt`, `README.md`, `__init__.py` 等）。如果是非 Python 文件（如 .txt, .json, .md），也请使用 `python` 代码块包裹，并在第一行保留 `# path/filename` 注释，以便工具识别路径。"""

        self.setup_ui()
        self.update_stats()

    def setup_ui(self):
        # 1. 顶部操作区
        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="目标路径:").pack(side=tk.LEFT)
        
        self.path_entry = tk.Entry(top_frame, width=40)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        btn_select = tk.Button(top_frame, text="选择文件夹", command=self.select_folder)
        btn_select.pack(side=tk.LEFT, padx=5)

        tk.Frame(top_frame, width=20).pack(side=tk.LEFT)

        btn_run = tk.Button(top_frame, text="提取: 生成 Markdown", command=self.generate_content, 
                            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_run.pack(side=tk.LEFT, padx=5)

        btn_restore = tk.Button(top_frame, text="还原: 写入文件", command=self.restore_project, 
                                bg="#FF5722", fg="white", font=("Arial", 10, "bold"))
        btn_restore.pack(side=tk.LEFT, padx=5)

        # ================= 新增：文件类型过滤面板 =================
        filter_frame = tk.LabelFrame(self.root, text="文件类型过滤", padx=10, pady=5)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        # 容器用于放置复选框，自动换行布局
        checkbox_frame = tk.Frame(filter_frame)
        checkbox_frame.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)

        col = 0
        row = 0
        for label, exts in self.TYPE_OPTIONS.items():
            var = tk.BooleanVar(value=True) # 默认全选
            # 如果不想默认全选某些不常用的，可以在这里加判断，例如: if label in ["Python", "Markdown"]: ...
            
            cb = tk.Checkbutton(checkbox_frame, text=label, variable=var, command=self.update_stats_hint)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10)
            self.check_vars[label] = var
            
            col += 1
            if col > 7: # 每行放8个
                col = 0
                row += 1

        # 自定义输入区域
        custom_frame = tk.Frame(filter_frame, pady=5)
        custom_frame.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)
        
        tk.Label(custom_frame, text="额外类型 (用分号 ; 分割，例如 .sh;.bat): ").pack(side=tk.LEFT)
        self.custom_ext_entry = tk.Entry(custom_frame, width=40)
        self.custom_ext_entry.pack(side=tk.LEFT, padx=5)
        self.custom_ext_entry.bind('<KeyRelease>', self.update_stats_hint) # 简单绑定提示刷新
        
        # ========================================================

        # 2. 底部功能区
        bottom_frame = tk.Frame(self.root, pady=5, padx=10)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        btn_clear = tk.Button(bottom_frame, text="清空文本框", command=self.clear_text)
        btn_clear.pack(side=tk.LEFT, padx=5)
        btn_import = tk.Button(bottom_frame, text="导入 MD 文件", command=self.import_md_file, bg="#e1f5fe")
        btn_import.pack(side=tk.LEFT, padx=5)

        btn_copy = tk.Button(bottom_frame, text="复制全部内容", command=self.copy_to_clipboard)
        btn_copy.pack(side=tk.RIGHT, padx=5)
        btn_export = tk.Button(bottom_frame, text="导出 MD 文件", command=self.export_md_file, bg="#e1f5fe")
        btn_export.pack(side=tk.RIGHT, padx=5)
        btn_copy_prompt = tk.Button(bottom_frame, text="复制AI prompt", command=self.copy_prompt_to_clipboard, bg="#FFC107", fg="black")
        btn_copy_prompt.pack(side=tk.RIGHT, padx=5)

        # 3. 状态栏
        self.status_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN, pady=2)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.stats_label = tk.Label(self.status_frame, text="Ready", anchor=tk.W, font=("Arial", 9))
        self.stats_label.pack(side=tk.LEFT, padx=10)

        # 4. 文本显示区
        text_frame = tk.Frame(self.root, padx=10, pady=5)
        text_frame.pack(fill=tk.BOTH, expand=True)

        code_font = tkfont.Font(family="Consolas", size=10)
        if "Consolas" not in tkfont.families():
             code_font = tkfont.Font(family="Courier", size=10)

        self.text_area = scrolledtext.ScrolledText(text_frame, font=code_font, undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.bind('<KeyRelease>', self.update_stats)

        # 默认说明
        welcome_msg = (
            "# 使用说明 (Stack解析版):\n"
            "# 1. 在上方设置【文件类型过滤】以决定提取哪些文件。\n"
            "# 2. [提取]: 自动扫描目录，生成包含文件路径和内容的 Markdown。\n"
            "# 3. [还原]: 将下方的 Markdown 内容还原回文件结构。\n\n"
        )
        self.text_area.insert(tk.END, welcome_msg)

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_selected)

    def update_stats(self, event=None):
        content = self.text_area.get(1.0, tk.END).rstrip()
        if not content:
            self.stats_label.config(text="Lines: 0 | Words: 0 | Chars: 0")
            return
        lines = len(content.split('\n'))
        chars = len(content)
        words = len(content.split())
        self.stats_label.config(text=f"Lines: {lines} | Words: {words} | Chars: {chars}")

    def update_stats_hint(self, event=None):
        """仅用于在调整过滤设置时，在状态栏简单提示，不进行繁重计算"""
        # 可以显示当前允许的后缀列表，或者保持静默
        pass

    def clear_text(self):
        self.text_area.delete(1.0, tk.END)
        self.update_stats()

    def import_md_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, f.read())
            self.update_stats()

    def export_md_file(self):
        content = self.text_area.get(1.0, tk.END).strip()
        if not content: return
        file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown Files", "*.md")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("成功", "导出完成")

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_area.get(1.0, tk.END))
        messagebox.showinfo("成功", "已复制到剪贴板")

    def copy_prompt_to_clipboard(self):
        """复制prompt.md文件内容到剪贴板"""
        try:
            # 使用嵌入的字符串内容
            self.root.clipboard_clear()
            self.root.clipboard_append(self.PROMPT_CONTENT)
            messagebox.showinfo("成功", "AI prompt已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")

    def get_allowed_extensions(self):
        """根据复选框和自定义输入，计算允许的后缀列表"""
        allowed = set()
        # 1. 复选框选中的类型
        for label, var in self.check_vars.items():
            if var.get():
                exts = self.TYPE_OPTIONS[label]
                for ext in exts.split(';'):
                    ext = ext.strip().lower()
                    if ext:
                        allowed.add(ext)
        
        # 2. 自定义输入
        custom_text = self.custom_ext_entry.get().strip()
        if custom_text:
            parts = custom_text.split(';')
            for p in parts:
                p = p.strip().lower()
                if p:
                    # 如果用户没加点，自动补上点 (例如 "sh" -> ".sh")
                    if not p.startswith('.'):
                        p = '.' + p
                    allowed.add(p)
        
        return tuple(allowed) # endswith 需要 tuple

    def get_directory_tree(self, root_path):
        output = []
        base_level = root_path.count(os.sep)
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            level = root.count(os.sep) - base_level
            indent = "    " * level
            folder_name = os.path.basename(root)
            if level == 0: output.append(f"{folder_name}/")
            else: output.append(f"{indent}|-- {folder_name}/")
            sub_indent = "    " * (level + 1)
            for f in files:
                if f not in self.IGNORE_FILES:
                    output.append(f"{sub_indent}|-- {f}")
        return "\n".join(output)
    def get_python_files_content(self, root_path):
        """生成内容时，动态计算反引号数量，并应用文件类型过滤，增加编码兼容性"""
        output = []
        allowed_extensions = self.get_allowed_extensions()
        
        if not allowed_extensions:
            return "## Warning: No file types selected for extraction.\n"

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for file in files:
                if file.lower().endswith(allowed_extensions):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")
                    
                    try:
                        content = ""
                        # === 修改开始：增强的编码读取逻辑 ===
                        try:
                            # 优先尝试 UTF-8
                            with open(full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            try:
                                # 失败则尝试 GB18030 (涵盖 GBK, GB2312)
                                with open(full_path, "r", encoding="gb18030") as f:
                                    content = f.read()
                            except Exception:
                                # 最后的手段：忽略无法识别的字符
                                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                    content = f.read()
                        # === 修改结束 ===
                        
                        # 检测内容中最长的连续反引号
                        max_backticks = 0
                        import re
                        ticks = re.findall(r'`+', content)
                        if ticks:
                            max_backticks = max(len(t) for t in ticks)
                        
                        # 栅栏长度
                        fence_len = max(3, max_backticks + 1)
                        fence = "`" * fence_len
                        
                        # 尝试推断语言类型
                        ext = os.path.splitext(file)[1].lower().replace('.', '')
                        lang = "python" if ext == "py" else ext
                        if not lang: lang = "text"

                        block = f"{fence}{lang}\n# {rel_path}\n{content}\n{fence}\n\n"
                        output.append(block)
                    except Exception as e:
                        output.append(f"```text\n# Skipped: {rel_path} (Read Error: {str(e)})\n```\n\n")
        
        if not output:
            return "## No files found matching the selected types.\n"
            
        return "".join(output)

    def restore_project(self):
        """使用状态机（类栈思想）逐行解析，解决嵌套截断问题"""
        target_root = self.path_entry.get().strip()
        full_text = self.text_area.get(1.0, tk.END)

        if not target_root:
            messagebox.showwarning("提示", "请选择目标文件夹")
            return

        if not os.path.exists(target_root):
            if messagebox.askyesno("创建目录", f"目录不存在，是否创建？\n{target_root}"):
                os.makedirs(target_root)
            else:
                return

        # 定义状态枚举
        STATE_OUTSIDE = 0      # 在代码块外部
        STATE_EXPECT_PATH = 1  # 刚进入代码块，等待路径注释
        STATE_INSIDE = 2       # 正在读取代码内容

        lines = full_text.split('\n')
        current_state = STATE_OUTSIDE
        
        current_fence = ""     # 记录当前块的栅栏（如 ``` 或 ````）
        current_path = ""
        code_buffer = []
        success_count = 0

        for line in lines:
            stripped = line.strip()

            # 1. 状态：在代码块外部，寻找开始标记
            if current_state == STATE_OUTSIDE:
                # 匹配任意长度的栅栏，例如 ```python 或 ````javascript
                # 只要以至少3个反引号开头即可
                if stripped.startswith("```"):
                    # 寻找语言标记的位置（如果有）
                    # 简单的逻辑：取反引号部分作为 fence
                    import re
                    match = re.match(r'^(`+)(.*)', stripped)
                    if match:
                        fence_part = match.group(1)
                        # 只要是纯反引号开头
                        current_fence = fence_part
                        current_state = STATE_EXPECT_PATH
                        code_buffer = []
            
            # 2. 状态：刚进入代码块，第一行必须是路径 # path/to/file
            elif current_state == STATE_EXPECT_PATH:
                if stripped.startswith("#"):
                    # 提取路径
                    current_path = stripped.lstrip("#").strip()
                    current_state = STATE_INSIDE
                else:
                    # 如果这一行是空的，忽略它继续找路径？
                    # 或者，如果是非注释内容，说明这可能不是我们要还原的格式块，而是普通Markdown代码块
                    # 为了严谨，这里如果不是路径注释，我们放弃这个块的还原，退回外部状态
                    if stripped == "":
                         continue 
                    current_state = STATE_OUTSIDE
                    current_fence = ""

            # 3. 状态：在代码块内部，收集代码，直到遇到闭合栅栏
            elif current_state == STATE_INSIDE:
                # 检查是否是闭合栅栏 (必须完全匹配开启栅栏，且这一行通常只包含栅栏)
                if stripped == current_fence:
                    # === 结束当前块，写入文件 ===
                    self.write_file(target_root, current_path, code_buffer)
                    success_count += 1
                    
                    # 重置状态
                    current_state = STATE_OUTSIDE
                    current_fence = ""
                    code_buffer = []
                    current_path = ""
                else:
                    # 属于代码内容
                    code_buffer.append(line)

        messagebox.showinfo("还原完成", f"已成功还原 {success_count} 个文件。")

    def write_file(self, root, rel_path, content_lines):
        """辅助写入方法"""
        try:
            full_path = os.path.join(root, rel_path)
            # 安全检查：防止路径回溯攻击 (../../)
            if not os.path.abspath(full_path).startswith(os.path.abspath(root)):
                print(f"Skipping unsafe path: {rel_path}")
                return

            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            content = "\n".join(content_lines)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing {rel_path}: {e}")

    def generate_content(self):
        target_path = self.path_entry.get().strip()
        if not target_path or not os.path.isdir(target_path):
            messagebox.showerror("错误", "无效的文件夹路径")
            return

        tree = "## Project Structure\n```text\n" + self.get_directory_tree(target_path) + "\n```\n\n"
        code = "## Code Contents\n\n" + self.get_python_files_content(target_path)
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, tree + code)
        self.update_stats()

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeMergerApp(root)
    root.mainloop()
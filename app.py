# main.py
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.font as tkfont

class CodeMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python工程结构互转工具 (Stack Parser版)")
        self.root.geometry("1100x900")
        
        # 忽略的目录和文件
        self.IGNORE_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'build', 'dist'}
        self.IGNORE_FILES = {'.DS_Store'}

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
            "# 本工具已优化，可正确处理包含 ``` 的代码文件。\n"
            "# 1. [提取]: 自动检测代码中的反引号，动态调整 Markdown 栅栏长度。\n"
            "# 2. [还原]: 使用状态机逐行解析，确保不被内嵌的反引号截断。\n"
            "# 3. 格式严格遵循：\n"
            "#    ```python\n"
            "#    # path/to/file.py\n"
            "#    <code_content>\n"
            "#    ```\n\n"
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

    # ================= 核心逻辑优化区 =================

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
        """生成内容时，动态计算反引号数量，防止代码被错误截断"""
        output = []
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for file in files:
                if file.endswith((".py", ".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css", ".js")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")
                    
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # 【优化点1】检测内容中最长的连续反引号
                        max_backticks = 0
                        import re
                        # 查找连续的反引号
                        ticks = re.findall(r'`+', content)
                        if ticks:
                            max_backticks = max(len(t) for t in ticks)
                        
                        # 栅栏长度 = 内容中最长反引号数 + 1 (至少3个)
                        fence_len = max(3, max_backticks + 1)
                        fence = "`" * fence_len
                        
                        block = f"{fence}python\n# {rel_path}\n{content}\n{fence}\n\n"
                        output.append(block)
                    except Exception as e:
                        output.append(f"```python\n# Error: {rel_path}\n# {str(e)}\n```\n\n")
        
        return "".join(output)

    def restore_project(self):
        """【优化点2】使用状态机（类栈思想）逐行解析，解决嵌套截断问题"""
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
                # 匹配任意长度的栅栏，例如 ```python 或 ````python
                if stripped.startswith("```") and stripped.endswith("python"):
                    # 提取栅栏部分（去掉 python 后缀）
                    fence_part = stripped[:-6].strip() # 假设紧挨着python
                    if not fence_part: # 处理可能存在的空格
                         idx = line.find("python")
                         fence_part = line[:idx].strip()
                    
                    # 确认是纯反引号
                    if all(c == '`' for c in fence_part):
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
                    # 如果第一行不是注释，说明不符合协议，回退状态
                    # 或者是空行？这里为了严格性，认为不符合格式则放弃该块
                    if stripped == "":
                         continue # 允许路径前有空行？通常不允许，这里严格处理
                    current_state = STATE_OUTSIDE
                    current_fence = ""

            # 3. 状态：在代码块内部，收集代码，直到遇到闭合栅栏
            elif current_state == STATE_INSIDE:
                # 检查是否是闭合栅栏
                # 闭合栅栏必须单独一行，且长度与开启栅栏一致
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
            
            # 处理末尾多余换行（可选）
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
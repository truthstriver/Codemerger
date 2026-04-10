import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import tkinter.font as tkfont

class CodeMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python工程结构互转工具 (增强版: 筛选+导入导出)")
        self.root.geometry("1300x950")
        
        # 忽略的目录和文件
        self.IGNORE_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'build', 'dist', 'target'}
        self.IGNORE_FILES = {'.DS_Store', 'Thumbs.db'}

        # 定义默认支持的文件类型选项
        self.TYPE_OPTIONS = {
            "Python": ".py;.pyw",
            "Markdown": ".md",
            "Text": ".txt",
            "JSON": ".json",
            "YAML": ".yaml;.yml",
            "Web": ".html;.css;.js;.ts;.jsx;.tsx",
            "C/C++": ".c;.cpp;.h;.hpp",
            "Java": ".java",
            "Go": ".go",
            "Shell": ".sh;.bat"
        }
        self.check_vars = {} 
        
        # 存储文件树的状态
        self.tree_selection = {}  # Path -> Boolean
        self.tree_item_map = {}   # Item ID -> Path
        
        self.setup_icons()

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
    包括所有必要的文件（如 `requirements.txt`, `README.md`, `__init__.py` 等）。如果是非 Python 文件（如 .txt, .json, .md），也请使用 `python` 代码块包裹，并在第一行保留 `# path/filename` 注释，以便工具识别路径。
"""

        self.setup_ui()
        self.update_stats()

    def setup_icons(self):
        size = 16
        # 未选中 (空框)
        self.img_unchecked = tk.PhotoImage(width=size, height=size)
        self.img_unchecked.put(("#888888",), to=(0, 0, size, 1)) 
        self.img_unchecked.put(("#888888",), to=(0, size-1, size, size))
        self.img_unchecked.put(("#888888",), to=(0, 0, 1, size))
        self.img_unchecked.put(("#888888",), to=(size-1, 0, size, size))
        self.img_unchecked.put(("#FFFFFF",), to=(1, 1, size-1, size-1))

        # 选中 (带勾)
        self.img_checked = tk.PhotoImage(width=size, height=size)
        self.img_checked.put(("#4CAF50",), to=(0, 0, size, size))
        for x, y in [(3,8), (4,9), (5,10), (6,9), (7,8), (8,7), (9,6), (10,5), (11,4)]:
             self.img_checked.put(("#FFFFFF",), to=(x, y, x+2, y+2))

    def setup_ui(self):
        # ================= Top Frame =================
        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="目标路径:").pack(side=tk.LEFT)
        self.path_entry = tk.Entry(top_frame, width=40)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 绑定回车自动加载
        self.path_entry.bind('<Return>', self.load_tree_from_entry)
        self.path_entry.bind('<FocusOut>', self.load_tree_from_entry)

        btn_select = tk.Button(top_frame, text="选择文件夹", command=self.select_folder)
        btn_select.pack(side=tk.LEFT, padx=5)

        tk.Frame(top_frame, width=20).pack(side=tk.LEFT)

        btn_run = tk.Button(top_frame, text="提取: 生成 Markdown", command=self.generate_content, 
                            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_run.pack(side=tk.LEFT, padx=5)

        btn_restore = tk.Button(top_frame, text="还原: 写入文件", command=self.restore_project, 
                                bg="#FF5722", fg="white", font=("Arial", 10, "bold"))
        btn_restore.pack(side=tk.LEFT, padx=5)

        # ================= Main Split Layout =================
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Left Side: File Tree ---
        left_frame = tk.Frame(self.paned_window)
        self.paned_window.add(left_frame, width=320)

        # Left Header
        left_top_box = tk.Frame(left_frame)
        left_top_box.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        tk.Label(left_top_box, text="文件选择树", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # --- 新增：树操作按钮 (全选/全不选) ---
        btn_box = tk.Frame(left_frame, pady=2)
        btn_box.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(btn_box, text="全选", command=lambda: self.batch_change_selection(True)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(btn_box, text="全不选", command=lambda: self.batch_change_selection(False)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Treeview
        self.tree = ttk.Treeview(left_frame, selectmode="none", show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ysb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=ysb.set)
        
        xsb = ttk.Scrollbar(left_frame, orient="horizontal", command=self.tree.xview)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=xsb.set)

        self.tree.bind("<Button-1>", self.on_tree_click)

        # --- Right Side: Content & Filters ---
        right_frame = tk.Frame(self.paned_window)
        self.paned_window.add(right_frame)

        # 1. Filter
        filter_frame = tk.LabelFrame(right_frame, text="后缀名过滤 (仅提取时生效)", padx=10, pady=5)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        checkbox_frame = tk.Frame(filter_frame)
        checkbox_frame.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)

        col = 0
        row = 0
        for label, exts in self.TYPE_OPTIONS.items():
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(checkbox_frame, text=label, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10)
            self.check_vars[label] = var
            col += 1
            if col > 5:
                col = 0
                row += 1
        
        custom_frame = tk.Frame(filter_frame, pady=5)
        custom_frame.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)
        tk.Label(custom_frame, text="额外后缀: ").pack(side=tk.LEFT)
        self.custom_ext_entry = tk.Entry(custom_frame, width=30)
        self.custom_ext_entry.pack(side=tk.LEFT, padx=5)

        # 2. Text Area
        text_frame = tk.Frame(right_frame, padx=5, pady=5)
        text_frame.pack(fill=tk.BOTH, expand=True)

        code_font = tkfont.Font(family="Consolas", size=10)
        if "Consolas" not in tkfont.families():
             code_font = tkfont.Font(family="Courier", size=10)

        self.text_area = scrolledtext.ScrolledText(text_frame, font=code_font, undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.bind('<KeyRelease>', self.update_stats)

        # 3. Bottom Buttons
        bottom_frame = tk.Frame(right_frame, pady=5)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 左侧按钮组
        btn_clear = tk.Button(bottom_frame, text="清空", command=self.clear_text)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        # --- 新增：导入导出按钮 ---
        btn_import = tk.Button(bottom_frame, text="导入 MD", command=self.import_md_file, bg="#e1f5fe")
        btn_import.pack(side=tk.LEFT, padx=5)
        
        btn_export = tk.Button(bottom_frame, text="导出 MD", command=self.export_md_file, bg="#e1f5fe")
        btn_export.pack(side=tk.LEFT, padx=5)
        # ------------------------

        # 右侧按钮组
        btn_prompt = tk.Button(bottom_frame, text="复制 Prompt", command=self.copy_prompt_to_clipboard, bg="#FFC107")
        btn_prompt.pack(side=tk.RIGHT, padx=5)
        
        btn_copy = tk.Button(bottom_frame, text="复制全部内容", command=self.copy_to_clipboard)
        btn_copy.pack(side=tk.RIGHT, padx=5)

        # 4. Status
        self.status_frame = tk.Frame(right_frame, bd=1, relief=tk.SUNKEN, pady=2)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.stats_label = tk.Label(self.status_frame, text="Ready", anchor=tk.W, font=("Arial", 9))
        self.stats_label.pack(side=tk.LEFT, padx=10)

        # Initial Text
        welcome_msg = """ # 使用说明:
 # 1. [选择文件夹]: 左侧会自动加载目录树，默认全部勾选。
 # 2. [筛选]: 在左侧树中勾选/取消勾选目录或文件，上方设置允许的后缀。
 #    (注意：最终提取的文件 = 左侧勾选的文件 AND 后缀名匹配的文件)
 # 3. [提取]: 生成 Markdown。
 # 4. [还原]: 将 Markdown 内容写回文件。"""
        self.text_area.insert(tk.END, welcome_msg)

    # ================= Tree Logic =================

    def load_tree_from_entry(self, event=None):
        path = self.path_entry.get().strip()
        if path and os.path.isdir(path):
            self.refresh_tree(path)

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_selected)
            self.refresh_tree(folder_selected)

    def refresh_tree(self, root_path):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_selection.clear()
        self.tree_item_map.clear()
        self._populate_node("", root_path)

    def _populate_node(self, parent_item, current_path):
        try:
            items = os.listdir(current_path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()))
        except PermissionError:
            return

        for name in items:
            if name in self.IGNORE_DIRS or name in self.IGNORE_FILES:
                continue
                
            full_path = os.path.join(current_path, name)
            is_dir = os.path.isdir(full_path)
            
            self.tree_selection[full_path] = True
            
            item_id = self.tree.insert(
                parent_item, "end", text=f" {name}", open=False, image=self.img_checked
            )
            self.tree_item_map[item_id] = full_path

            if is_dir:
                self._populate_node(item_id, full_path)

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        full_path = self.tree_item_map.get(item_id)
        if full_path:
            current_state = self.tree_selection.get(full_path, True)
            self.toggle_node(item_id, not current_state)

    def toggle_node(self, item_id, state):
        full_path = self.tree_item_map.get(item_id)
        if full_path:
            self.tree_selection[full_path] = state
        img = self.img_checked if state else self.img_unchecked
        self.tree.item(item_id, image=img)
        for child in self.tree.get_children(item_id):
            self.toggle_node(child, state)

    # --- 新增：批量修改选择状态 ---
    def batch_change_selection(self, state):
        """一次性修改所有节点的状态"""
        img = self.img_checked if state else self.img_unchecked
        
        # 更新数据
        for path in self.tree_selection.keys():
            self.tree_selection[path] = state
            
        # 更新视图 (直接遍历 item_map 最快)
        for item_id in self.tree_item_map.keys():
            self.tree.item(item_id, image=img)

    # ================= Import / Export =================

    def import_md_file(self):
        """导入 Markdown 文件"""
        file_path = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.END, f.read())
                self.update_stats()
            except Exception as e:
                messagebox.showerror("错误", f"无法读取文件: {e}")

    def export_md_file(self):
        """导出当前内容到 Markdown 文件"""
        content = self.text_area.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("提示", "内容为空，无法导出")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown Files", "*.md")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("成功", "导出完成")
            except Exception as e:
                messagebox.showerror("错误", f"写入文件失败: {e}")

    # ================= Generation Logic =================

    def get_allowed_extensions(self):
        allowed = set()
        for label, var in self.check_vars.items():
            if var.get():
                exts = self.TYPE_OPTIONS[label]
                for ext in exts.split(';'):
                    if ext.strip(): allowed.add(ext.strip().lower())
        custom_text = self.custom_ext_entry.get().strip()
        if custom_text:
            for p in custom_text.split(';'):
                p = p.strip().lower()
                if p:
                    if not p.startswith('.'): p = '.' + p
                    allowed.add(p)
        return tuple(allowed)

    def generate_content(self):
        target_path = self.path_entry.get().strip()
        if not target_path or not os.path.isdir(target_path):
            messagebox.showerror("错误", "无效的文件夹路径")
            return

        tree_text = "## Project Structure\n```text\n" + self.get_filtered_tree_text(target_path) + "\n```\n\n"
        code_text = "## Code Contents\n\n" + self.get_filtered_file_content(target_path)
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, tree_text + code_text)
        self.update_stats()

    def get_filtered_tree_text(self, root_path):
        output = []
        base_level = root_path.count(os.sep)
        for root, dirs, files in os.walk(root_path):
            # 修正点：只过滤忽略名单，不要因为父目录未选中就阻止遍历子目录
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            # 计算层级
            level = root.count(os.sep) - base_level
            indent = "    " * level
            folder_name = os.path.basename(root)
            
            # 显示逻辑：如果是根目录，或者该目录被显式选中，则打印目录行
            # (如果目录没选但子文件选了，目录行不显示，只显示缩进后的文件名，这样保持了逻辑一致性)
            if root == root_path or self.tree_selection.get(root, False):
                if level == 0: output.append(f"{folder_name}/")
                else: output.append(f"{indent}|-- {folder_name}/")
            
            sub_indent = "    " * (level + 1)
            for f in files:
                if f in self.IGNORE_FILES: continue
                # 只要文件被选中，就添加到树结构中
                if self.tree_selection.get(os.path.join(root, f), False):
                    output.append(f"{sub_indent}|-- {f}")
        return "\n".join(output)


    def get_filtered_file_content(self, root_path):
        output = []
        allowed_extensions = self.get_allowed_extensions()

        for root, dirs, files in os.walk(root_path):
            # 修正点1：只过滤系统忽略的文件夹 (如 .git)，不再过滤未选中的文件夹
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            # 修正点2：删除了原先 "如果 root 没选中则 continue" 的代码
            # 这样即使父目录没勾选，os.walk 依然会进入里面检查文件
                
            for file in files:
                full_path = os.path.join(root, file)
                
                # 核心判断：直接判断具体文件是否被勾选
                if not self.tree_selection.get(full_path, False): continue
                    
                if file.lower().endswith(allowed_extensions):
                    rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")
                    try:
                        content = ""
                        try:
                            with open(full_path, "r", encoding="utf-8") as f: content = f.read()
                        except UnicodeDecodeError:
                            try:
                                with open(full_path, "r", encoding="gb18030") as f: content = f.read()
                            except:
                                with open(full_path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()

                        max_backticks = 0
                        import re
                        ticks = re.findall(r'`+', content)
                        if ticks: max_backticks = max(len(t) for t in ticks)
                        fence = "`" * max(3, max_backticks + 1)
                        
                        ext = os.path.splitext(file)[1].lower().replace('.', '')
                        lang = "python" if ext == "py" else ext
                        if not lang: lang = "text"

                        output.append(f"{fence}{lang}\n# {rel_path}\n{content}\n{fence}\n\n")
                    except Exception as e:
                        output.append(f"```text\n# Error: {e}\n```\n\n")
        return "".join(output) if output else "## No files selected.\n"

    # ================= Restore & Utils =================

    def restore_project(self):
        target_root = self.path_entry.get().strip()
        full_text = self.text_area.get(1.0, tk.END)
        
        if not target_root:
            messagebox.showwarning("提示", "请选择目标文件夹")
            return
        
        if not os.path.exists(target_root):
            os.makedirs(target_root)

        lines = full_text.split('\n')
        STATE_OUTSIDE, STATE_EXPECT_PATH, STATE_INSIDE = 0, 1, 2
        current_state = STATE_OUTSIDE
        current_fence, current_path, code_buffer = "", "", []
        success_count = 0
        import re

        for line in lines:
            stripped = line.strip()
            if current_state == STATE_OUTSIDE:
                if stripped.startswith("```"):
                    match = re.match(r'^(`+)(.*)', stripped)
                    if match:
                        current_fence = match.group(1)
                        current_state = STATE_EXPECT_PATH
                        code_buffer = []
            elif current_state == STATE_EXPECT_PATH:
                if stripped.startswith("#"):
                    current_path = stripped.lstrip("#").strip()
                    current_state = STATE_INSIDE
                elif stripped == "": continue
                else: current_state = STATE_OUTSIDE
            elif current_state == STATE_INSIDE:
                if stripped == current_fence:
                    try:
                        full_path = os.path.join(target_root, current_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(code_buffer))
                        success_count += 1
                    except Exception: pass
                    current_state = STATE_OUTSIDE
                    code_buffer = []
                else:
                    code_buffer.append(line)
        messagebox.showinfo("还原完成", f"已还原 {success_count} 个文件")

    def clear_text(self):
        self.text_area.delete(1.0, tk.END)
        self.update_stats()

    def update_stats(self, event=None):
        content = self.text_area.get(1.0, tk.END).rstrip()
        lines = len(content.split('\n')) if content else 0
        self.stats_label.config(text=f"Lines: {lines} | Chars: {len(content)}")

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_area.get(1.0, tk.END))
        messagebox.showinfo("成功", "已复制到剪贴板")

    def copy_prompt_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.PROMPT_CONTENT)
        messagebox.showinfo("成功", "AI Prompt 已复制")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeMergerApp(root)
    root.mainloop()
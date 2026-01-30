import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import tkinter.font as tkfont

# ==========================================
# Base64 编码的图标数据 (用于模拟复选框)
# ==========================================
# 未选中 (空框)
ICON_UNCHECKED = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAALEwAACxMBAJqcGAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAA5SURBVDjLY/j//z8DJZhhmBuwW1EZGxuD4tH/qHg0DAajYTAaDkajYTAaDkajYTAaDkbD4LAwAAw/Y/qTv7z/AAAAAElFTkSuQmCC'
# 选中 (带勾)
ICON_CHECKED = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAALEwAACxMBAJqcGAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABQSURBVDjLY/j//z8DJZhhmBuwW1EZGxuD4tH/qHg0DAajYTAaDkajYTAaDkajYTAaDkbD4LAwAAw/Y/qTv7z/AAAAAElFTkSuQmCC'
# 实际带勾的更复杂的 Base64 数据太长，这里我们用代码动态生成简单的图形代替，或者使用上面的占位符。
# 为了代码整洁且无需外部文件，我们在类初始化时用 Python 绘图生成简单的图标。

class CodeMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python工程结构互转工具 (带文件树筛选版)")
        self.root.geometry("1300x950")  # 增加宽度以容纳侧边栏
        
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
        
        # 存储文件树的状态：Path -> Boolean (True=Selected)
        # 注意：这里存储的是绝对路径
        self.tree_selection = {} 
        self.tree_item_map = {} # Item ID -> Path
        
        # 生成图标
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
        """生成复选框图标，避免依赖外部图片文件"""
        size = 16
        # 未选中图标 (空框)
        self.img_unchecked = tk.PhotoImage(width=size, height=size)
        self.img_unchecked.put(("#888888",), to=(0, 0, size, 1)) # Top
        self.img_unchecked.put(("#888888",), to=(0, size-1, size, size)) # Bottom
        self.img_unchecked.put(("#888888",), to=(0, 0, 1, size)) # Left
        self.img_unchecked.put(("#888888",), to=(size-1, 0, size, size)) # Right
        self.img_unchecked.put(("#FFFFFF",), to=(1, 1, size-1, size-1)) # Fill

        # 选中图标 (带勾)
        self.img_checked = tk.PhotoImage(width=size, height=size)
        self.img_checked.put(("#4CAF50",), to=(0, 0, size, size)) # Green Fill
        # 简单的勾号 (白色像素点)
        for x, y in [(3,8), (4,9), (5,10), (6,9), (7,8), (8,7), (9,6), (10,5), (11,4)]:
             self.img_checked.put(("#FFFFFF",), to=(x, y, x+2, y+2))

        # 文件夹图标 (简单示意)
        self.img_folder = tk.PhotoImage(width=size, height=size)
        self.img_folder.put(("#FFC107",), to=(1, 2, size-1, size-2))

        # 文件图标
        self.img_file = tk.PhotoImage(width=size, height=size)
        self.img_file.put(("#E0E0E0",), to=(3, 1, size-3, size-1))

    def setup_ui(self):
        # ================= Top Frame (Path & Main Actions) =================
        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="目标路径:").pack(side=tk.LEFT)
        self.path_entry = tk.Entry(top_frame, width=40)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

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

        # ================= Main Split Layout (PanedWindow) =================
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- Left Side: File Tree ---
        left_frame = tk.Frame(self.paned_window)
        self.paned_window.add(left_frame, width=300) # 初始宽度

        left_header = tk.Label(left_frame, text="文件选择树", font=("Arial", 10, "bold"))
        left_header.pack(side=tk.TOP, anchor=tk.W, padx=5)

        # Treeview
        self.tree = ttk.Treeview(left_frame, selectmode="none", show="tree") # hide headings
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ysb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=ysb.set)
        
        xsb = ttk.Scrollbar(left_frame, orient="horizontal", command=self.tree.xview)
        xsb.pack(side=tk.BOTTOM, fill=tk.X) # Put at bottom inside left_frame if needed, or modify layout
        self.tree.configure(xscrollcommand=xsb.set)

        # Bind Click
        self.tree.bind("<Button-1>", self.on_tree_click)

        # --- Right Side: Content & Filters ---
        right_frame = tk.Frame(self.paned_window)
        self.paned_window.add(right_frame)

        # 1. Filter Panel
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
        
        # Custom Ext
        custom_frame = tk.Frame(filter_frame, pady=5)
        custom_frame.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)
        tk.Label(custom_frame, text="额外后缀 (分号分割): ").pack(side=tk.LEFT)
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

        # 3. Bottom Buttons (Right side)
        bottom_frame = tk.Frame(right_frame, pady=5)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        btn_clear = tk.Button(bottom_frame, text="清空", command=self.clear_text)
        btn_clear.pack(side=tk.LEFT, padx=5)
        btn_copy = tk.Button(bottom_frame, text="复制内容", command=self.copy_to_clipboard)
        btn_copy.pack(side=tk.RIGHT, padx=5)
        btn_prompt = tk.Button(bottom_frame, text="复制 Prompt", command=self.copy_prompt_to_clipboard, bg="#FFC107")
        btn_prompt.pack(side=tk.RIGHT, padx=5)

        # 4. Status (Right Side)
        self.status_frame = tk.Frame(right_frame, bd=1, relief=tk.SUNKEN, pady=2)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.stats_label = tk.Label(self.status_frame, text="Ready", anchor=tk.W, font=("Arial", 9))
        self.stats_label.pack(side=tk.LEFT, padx=10)

        # Initial Text
        welcome_msg = (
            "# 使用说明:\n"
            "# 1. [选择文件夹]: 左侧会自动加载目录树，默认全部勾选。\n"
            "# 2. [筛选]: 在左侧树中勾选/取消勾选目录或文件，上方设置允许的后缀。\n"
            "#    (注意：最终提取的文件 = 左侧勾选的文件 AND 后缀名匹配的文件)\n"
            "# 3. [提取]: 生成 Markdown。\n"
            "# 4. [还原]: 将 Markdown 内容写回文件。\n\n"
        )
        self.text_area.insert(tk.END, welcome_msg)

    # ================= Treeview Logic =================

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_selected)
            self.refresh_tree(folder_selected)

    def load_tree_from_entry(self, event=None):
        """当手动输入路径并回车/离开焦点时触发"""
        path = self.path_entry.get().strip()
        # 只有当路径有效且是目录时才刷新，防止报错
        if path and os.path.isdir(path):
            # 为了防止重复刷新，可以在这里判断一下是否跟上次路径一样（可选）
            self.refresh_tree(path)

    def refresh_tree(self, root_path):
        """重新填充树并默认全选"""
        # 清空
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_selection.clear()
        self.tree_item_map.clear()
        
        # 递归填充
        self._populate_node("", root_path)

    def _populate_node(self, parent_item, current_path):
        try:
            # 排序：文件夹在前，文件在后
            items = os.listdir(current_path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()))
        except PermissionError:
            return

        for name in items:
            if name in self.IGNORE_DIRS or name in self.IGNORE_FILES:
                continue
                
            full_path = os.path.join(current_path, name)
            is_dir = os.path.isdir(full_path)
            
            # 默认状态：选中
            self.tree_selection[full_path] = True
            
            # 插入节点
            # text后加一个空格是为了让文字离图标远一点点
            item_id = self.tree.insert(
                parent_item, 
                "end", 
                text=f" {name}", 
                open=False, 
                image=self.img_checked
            )
            self.tree_item_map[item_id] = full_path

            if is_dir:
                self._populate_node(item_id, full_path)

    def on_tree_click(self, event):
        """处理树节点的点击事件，实现复选框切换"""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
            
        # 切换当前节点状态
        full_path = self.tree_item_map.get(item_id)
        if full_path:
            current_state = self.tree_selection.get(full_path, True)
            new_state = not current_state
            self.toggle_node(item_id, new_state)

    def toggle_node(self, item_id, state):
        """递归切换节点及其子节点的状态"""
        full_path = self.tree_item_map.get(item_id)
        if full_path:
            self.tree_selection[full_path] = state
        
        # 更新图标
        img = self.img_checked if state else self.img_unchecked
        self.tree.item(item_id, image=img)
        
        # 递归处理所有子节点
        children = self.tree.get_children(item_id)
        for child in children:
            self.toggle_node(child, state)

    # ================= Core Logic =================

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

        # 1. 生成树结构文本 (仅包含选中的文件夹/文件)
        tree_text = "## Project Structure\n```text\n"
        tree_text += self.get_filtered_tree_text(target_path)
        tree_text += "\n```\n\n"

        # 2. 生成代码内容
        code_text = "## Code Contents\n\n" + self.get_filtered_file_content(target_path)
        
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, tree_text + code_text)
        self.update_stats()

    def get_filtered_tree_text(self, root_path):
        """生成目录树，仅显示 tree_selection 中为 True 的项"""
        output = []
        base_level = root_path.count(os.sep)
        
        # 使用 os.walk 但需要手动控制递归顺序以匹配显示，
        # 为了简单，再次递归遍历或使用 tree item。
        # 这里使用简单的 os.walk 并检查 selection
        
        for root, dirs, files in os.walk(root_path):
            # 过滤掉未选中的文件夹，阻止进入
            # 只有当文件夹本身被选中，才遍历它
            # 注意：os.walk 的 dirs 列表修改必须原地进行
            
            # 1. 过滤掉忽略目录
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            # 2. 过滤掉在 Treeview 中未勾选的目录
            # full_path check
            active_dirs = []
            for d in dirs:
                d_path = os.path.join(root, d)
                if self.tree_selection.get(d_path, False): # 默认为False防错，实际应该都在map里
                    active_dirs.append(d)
            dirs[:] = active_dirs
            
            # 检查当前 root 是否被勾选 (如果是根目录本身，通常视为勾选)
            if root != root_path and not self.tree_selection.get(root, False):
                continue

            level = root.count(os.sep) - base_level
            indent = "    " * level
            folder_name = os.path.basename(root)
            
            # 添加目录名
            if level == 0: 
                output.append(f"{folder_name}/")
            else: 
                output.append(f"{indent}|-- {folder_name}/")
            
            sub_indent = "    " * (level + 1)
            
            # 添加文件
            for f in files:
                if f in self.IGNORE_FILES: continue
                f_path = os.path.join(root, f)
                # 必须在树中被选中
                if self.tree_selection.get(f_path, False):
                    output.append(f"{sub_indent}|-- {f}")
                    
        return "\n".join(output)

    def get_filtered_file_content(self, root_path):
        output = []
        allowed_extensions = self.get_allowed_extensions()

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            # 如果当前文件夹在树中未选中，跳过其下所有文件
            # (虽然 os.walk 还会遍历子目录，但这里处理的是当前层的文件)
            if root != root_path and not self.tree_selection.get(root, False):
                continue
                
            for file in files:
                full_path = os.path.join(root, file)
                
                # 核心过滤逻辑：
                # 1. 必须在左侧树中被勾选
                # 2. 必须符合右侧后缀名过滤
                if not self.tree_selection.get(full_path, False):
                    continue
                    
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

                        # 处理反引号
                        max_backticks = 0
                        import re
                        ticks = re.findall(r'`+', content)
                        if ticks: max_backticks = max(len(t) for t in ticks)
                        fence = "`" * max(3, max_backticks + 1)
                        
                        ext = os.path.splitext(file)[1].lower().replace('.', '')
                        lang = "python" if ext == "py" else ext
                        if not lang: lang = "text"

                        block = f"{fence}{lang}\n# {rel_path}\n{content}\n{fence}\n\n"
                        output.append(block)
                    except Exception as e:
                        output.append(f"```text\n# Error reading {rel_path}: {e}\n```\n\n")
        
        return "".join(output) if output else "## No files selected or matched.\n"

    # ================= Utils & Restore =================
    
    def update_stats(self, event=None):
        content = self.text_area.get(1.0, tk.END).rstrip()
        if not content:
            self.stats_label.config(text="Lines: 0 | Words: 0 | Chars: 0")
            return
        lines = len(content.split('\n'))
        self.stats_label.config(text=f"Lines: {lines} | Chars: {len(content)}")

    def clear_text(self):
        self.text_area.delete(1.0, tk.END)
        self.update_stats()

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_area.get(1.0, tk.END))
        messagebox.showinfo("成功", "已复制到剪贴板")

    def copy_prompt_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.PROMPT_CONTENT)
        messagebox.showinfo("成功", "AI Prompt 已复制")

    def restore_project(self):
        target_root = self.path_entry.get().strip()
        full_text = self.text_area.get(1.0, tk.END)
        
        if not target_root:
            messagebox.showwarning("提示", "请选择目标文件夹")
            return
        
        if not os.path.exists(target_root):
            os.makedirs(target_root)

        lines = full_text.split('\n')
        
        STATE_OUTSIDE = 0
        STATE_EXPECT_PATH = 1
        STATE_INSIDE = 2
        
        current_state = STATE_OUTSIDE
        current_fence = ""
        current_path = ""
        code_buffer = []
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
                elif stripped == "":
                    continue
                else:
                    # 格式不符，不是我们要还原的块
                    current_state = STATE_OUTSIDE
            
            elif current_state == STATE_INSIDE:
                if stripped == current_fence:
                    # 写入文件
                    try:
                        full_path = os.path.join(target_root, current_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(code_buffer))
                        success_count += 1
                    except Exception as e:
                        print(f"Write error: {e}")
                    
                    current_state = STATE_OUTSIDE
                    code_buffer = []
                else:
                    code_buffer.append(line)

        messagebox.showinfo("还原完成", f"已还原 {success_count} 个文件到 {target_root}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeMergerApp(root)
    root.mainloop()
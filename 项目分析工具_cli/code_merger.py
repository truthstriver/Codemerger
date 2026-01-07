import os
import argparse
import re
import sys

# 忽略配置
IGNORE_DIRS = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'build', 'dist', '.mypy_cache'}
IGNORE_FILES = {'.DS_Store', 'Thumbs.db'}
# 允许处理的文件后缀
target_extensions = (".py", ".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css", ".js", ".sh", ".conf", ".ini")

def get_directory_tree(root_path):
    """生成目录树结构字符串"""
    output = []
    base_level = root_path.rstrip(os.sep).count(os.sep)
    
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        dirs.sort()
        files.sort()
        
        level = root.count(os.sep) - base_level
        indent = "    " * level
        folder_name = os.path.basename(root)
        
        if level == 0:
            output.append(f"{folder_name}/")
        else:
            output.append(f"{indent}|-- {folder_name}/")
            
        sub_indent = "    " * (level + 1)
        for f in files:
            if f not in IGNORE_FILES:
                output.append(f"{sub_indent}|-- {f}")
                
    return "\n".join(output)

def export_to_markdown(source_dir, output_file):
    """
    导出模式：遍历目录生成 Markdown
    核心逻辑：检测文件内容中的反引号数量，动态生成 N+1 长度的栅栏
    """
    if not os.path.exists(source_dir):
        print(f"错误: 目录不存在 {source_dir}")
        sys.exit(1)

    result_content = []
    
    # 1. 添加目录树
    print("正在生成目录树...")
    tree_str = get_directory_tree(source_dir)
    result_content.append("## Project Structure\n")
    result_content.append("```text")
    result_content.append(tree_str)
    result_content.append("```\n\n")
    
    # 2. 遍历文件内容
    print("正在提取文件内容...")
    result_content.append("## Code Contents\n\n")
    
    file_count = 0
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        dirs.sort()
        files.sort()
        
        for file in files:
            if file.endswith(target_extensions) and file not in IGNORE_FILES:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir).replace("\\", "/")
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # 动态栅栏长度计算
                    ticks = re.findall(r'`+', content)
                    max_ticks = max(len(t) for t in ticks) if ticks else 0
                    fence_len = max(3, max_ticks + 1)
                    fence = "`" * fence_len
                    
                    # 统一使用 python 标记以便高亮，第一行注释为路径
                    block = f"{fence}python\n# {rel_path}\n{content}\n{fence}\n\n"
                    result_content.append(block)
                    file_count += 1
                    print(f"已处理: {rel_path}")
                except Exception as e:
                    print(f"跳过文件 {rel_path}: {e}")

    # 写入最终文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("".join(result_content))
    
    print(f"\n导出完成! 共处理 {file_count} 个文件。")
    print(f"输出文件: {os.path.abspath(output_file)}")

def restore_from_markdown(md_file, target_dir):
    """
    还原模式：解析 Markdown 写入文件
    核心逻辑：状态机解析，严格匹配栅栏长度，防止嵌套截断
    """
    if not os.path.exists(md_file):
        print(f"错误: MD文件不存在 {md_file}")
        sys.exit(1)
        
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"创建目标目录: {target_dir}")

    with open(md_file, "r", encoding="utf-8") as f:
        full_text = f.read()

    lines = full_text.split('\n')
    
    # 状态枚举
    STATE_OUTSIDE = 0
    STATE_EXPECT_PATH = 1
    STATE_INSIDE = 2
    
    current_state = STATE_OUTSIDE
    current_fence = ""
    current_path = ""
    code_buffer = []
    success_count = 0
    
    print("开始解析还原...")

    for line in lines:
        stripped = line.strip()
        
        # 1. 等待代码块开始
        if current_state == STATE_OUTSIDE:
            # 匹配 ```python 或 ````text 等，提取纯反引号部分
            if stripped.startswith("```"):
                # 简单分离栅栏和语言标记
                # 找到第一个非 ` 字符的位置
                match = re.match(r'^(`+)', stripped)
                if match:
                    current_fence = match.group(1)
                    current_state = STATE_EXPECT_PATH
                    code_buffer = []
        
        # 2. 等待路径注释 (必须紧跟在栅栏下一行)
        elif current_state == STATE_EXPECT_PATH:
            if stripped.startswith("#"):
                current_path = stripped.lstrip("#").strip()
                # 简单验证路径合法性（不含绝对路径或非法字符）
                if ".." in current_path or current_path.startswith("/") or "\\" in current_path:
                     # 尝试标准化，或者如果不安全则跳过
                     pass 
                current_state = STATE_INSIDE
            else:
                # 第一行不是注释，说明不是我们要还原的代码块（可能是普通说明）
                # 回退到 OUTSIDE 状态，且不消耗当前行作为 buffer（简单处理：直接丢弃该块）
                current_state = STATE_OUTSIDE
                current_fence = ""
        
        # 3. 读取内容直到遇到闭合栅栏
        elif current_state == STATE_INSIDE:
            if line.rstrip() == current_fence:
                # 写入文件
                full_path = os.path.join(target_dir, current_path)
                dir_name = os.path.dirname(full_path)
                
                if dir_name and not os.path.exists(dir_name):
                    os.makedirs(dir_name, exist_ok=True)
                
                try:
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(code_buffer))
                    print(f"已还原: {current_path}")
                    success_count += 1
                except Exception as e:
                    print(f"写入失败 {current_path}: {e}")
                
                # 重置
                current_state = STATE_OUTSIDE
                current_fence = ""
                current_path = ""
                code_buffer = []
            else:
                code_buffer.append(line)

    print(f"\n还原完成! 共还原 {success_count} 个文件到 {target_dir}")

def main():
    parser = argparse.ArgumentParser(description="Python工程结构互转工具 (CLI版)")
    
    # 创建互斥参数组
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--export', action='store_true', help='导出模式: 目录 -> MD文件')
    group.add_argument('-r', '--restore', action='store_true', help='还原模式: MD文件 -> 目录')
    
    parser.add_argument('-i', '--input', required=True, help='输入路径 (文件夹 或 MD文件)')
    parser.add_argument('-o', '--output', required=True, help='输出路径 (MD文件 或 文件夹)')
    
    args = parser.parse_args()
    
    if args.export:
        # 导出: Input是目录, Output是文件
        export_to_markdown(args.input, args.output)
    elif args.restore:
        # 还原: Input是文件, Output是目录
        restore_from_markdown(args.input, args.output)

if __name__ == "__main__":
    main()
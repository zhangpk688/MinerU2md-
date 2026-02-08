import re
import sys
import os
from typing import Optional

HEADER_NUMBER_RE = re.compile(r'^(\d+(?:\.\d+)*\.?)\s+(.*)$')


def transform_line(line: str) -> str:
    """按规则转换单行内容。"""
    if not line.startswith('# '):
        return line

    content = line[2:].strip()
    number_match = HEADER_NUMBER_RE.match(content)

    if number_match:
        number_part = number_match.group(1)  # 例如 "1"、"1.1"、"1.1.2."
        normalized_number = number_part.rstrip('.')
        level = normalized_number.count('.') + 1
        header_prefix = '#' * min(level, 6)
        return f"{header_prefix} {content}\n"

    return f"**{content}**\n"


def adjust_markdown_headers(input_file: str, output_file: Optional[str] = None) -> None:
    """
    调整Markdown文件中的一级标题
    
    规则：
    1. 带编号的标题（如 # 1, # 1.1）根据编号层级调整标题级别
    2. 不带编号的标题（如 # preface）转为加粗文本
    
    参数：
        input_file: 输入文件路径
        output_file: 输出文件路径（如果为None，则自动生成为“输入文件名_head”）
    """
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    processed_lines = [transform_line(line) for line in lines]
    
    # 写入文件
    if output_file is None:
        input_dir = os.path.dirname(input_file)
        input_name = os.path.basename(input_file)
        stem, ext = os.path.splitext(input_name)
        output_file = os.path.join(input_dir, f"{stem}_head{ext}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    adjust_markdown_headers(input_file, output_file)

import re
import sys

def adjust_markdown_headers(input_file, output_file=None):
    """
    调整Markdown文件中的一级标题
    
    规则：
    1. 带编号的标题（如 # 1, # 1.1）根据编号层级调整标题级别
    2. 不带编号的标题（如 # preface）转为加粗文本
    
    参数：
        input_file: 输入文件路径
        output_file: 输出文件路径（如果为None，则覆盖原文件）
    """
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    processed_lines = []
    
    for line in lines:
        # 检查是否是一级标题
        if line.startswith('# '):
            # 提取标题内容（去掉"# "）
            content = line[2:].strip()
            
            # 检查是否以数字开头（带编号）
            # 匹配模式：数字.数字.数字... 或单独的数字，末尾可带点
            number_match = re.match(r'^(\d+(?:\.\d+)*\.?)\s+(.*)$', content)
            
            if number_match:
                # 带编号的标题
                number_part = number_match.group(1)  # 例如 "1" 或 "1.1" 或 "1.1.2" 或末尾带点
                title_text = number_match.group(2)   # 标题文本
                
                # 计算层级（根据点的数量）
                normalized_number = number_part.rstrip('.')
                level = normalized_number.count('.') + 1
                
                # 生成新的标题（最多6级）
                header_prefix = '#' * min(level, 6)
                new_line = f"{header_prefix} {content}\n"
                processed_lines.append(new_line)
            else:
                # 不带编号的标题，转为加粗文本
                new_line = f"**{content}**\n"
                processed_lines.append(new_line)
        else:
            # 非一级标题，保持原样
            processed_lines.append(line)
    
    # 写入文件
    if output_file is None:
        output_file = input_file
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
    
    print(f"处理完成！已保存到: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python adjust_headers.py <输入文件> [输出文件]")
        print("示例: python adjust_headers.py input.md")
        print("示例: python adjust_headers.py input.md output.md")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    adjust_markdown_headers(input_file, output_file)

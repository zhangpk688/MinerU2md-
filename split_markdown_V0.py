**禁止读取文件**，直接执行下面的python脚本：
```python
import os
import re

def get_file_size_kb(file_path):
    """获取文件大小（KB）"""
    return os.path.getsize(file_path) / 1024

def split_by_headers(content, header_level):
    """按指定级别的标题切分内容"""
    if header_level == 1:
        pattern = r'\n(# .+)'
    elif header_level == 2:
        pattern = r'\n(## .+)'
    else:
        return [content]
    
    # 分割内容
    parts = re.split(pattern, content)
    
    # 重组：将标题和内容配对
    chunks = []
    if parts[0].strip():  # 如果有前言部分
        chunks.append(parts[0])
    
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            chunks.append(parts[i] + '\n' + parts[i + 1])
        else:
            chunks.append(parts[i])
    
    return chunks

def save_chunks(chunks, output_dir, base_name):
    """保存切分后的文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    for i, chunk in enumerate(chunks, 1):
        # 修改文件名格式为：01_源文件名.md, 02_源文件名.md
        filename = f"{i:02d}_{base_name}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        size_kb = get_file_size_kb(filepath)
        saved_files.append((filepath, size_kb))
        print(f"已保存: {filename} ({size_kb:.2f} KB)")
    
    return saved_files

def split_markdown_document(file_path, source_language='en', max_size_kb=30):
    """
    主函数：切分 Markdown 文档
    
    参数:
        file_path: 源文件路径
        source_language: 源语言代码（默认 'en'）
        max_size_kb: 最大文件大小（KB，默认 30）
    """
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查文件大小
    file_size = get_file_size_kb(file_path)
    print(f"原始文件大小: {file_size:.2f} KB")
    
    if file_size <= max_size_kb:
        print(f"文件小于 {max_size_kb} KB，无需切分")
        return
    
    # 准备输出目录
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    work_dir = os.path.dirname(file_path) or '.'
    output_dir = os.path.join(work_dir, f"{base_name}_split_{source_language}")
    
    print(f"\n开始切分文档...")
    print(f"输出目录: {output_dir}")
    
    # 第一步：按一级标题切分
    print(f"\n步骤 1: 按一级标题 '#' 切分")
    chunks_level1 = split_by_headers(content, header_level=1)
    print(f"切分为 {len(chunks_level1)} 个部分")
    
    # 检查是否需要二次切分
    final_chunks = []
    need_further_split = False
    
    for i, chunk in enumerate(chunks_level1, 1):
        # 临时保存以检查大小
        temp_file = f"temp_chunk_{i}.md"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        chunk_size = get_file_size_kb(temp_file)
        os.remove(temp_file)
        
        if chunk_size > max_size_kb:
            print(f"  部分 {i} ({chunk_size:.2f} KB) 仍然过大，需要按二级标题切分")
            need_further_split = True
            # 按二级标题切分
            sub_chunks = split_by_headers(chunk, header_level=2)
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(chunk)
    
    if need_further_split:
        print(f"\n步骤 2: 部分内容按二级标题 '##' 进一步切分")
        print(f"最终切分为 {len(final_chunks)} 个部分")
    
    # 保存所有切分后的文件
    print(f"\n保存切分后的文件...")
    saved_files = save_chunks(final_chunks, output_dir, base_name)
    
    # 汇总报告
    print(f"\n{'='*60}")
    print(f"切分完成！")
    print(f"总计: {len(saved_files)} 个文件")
    print(f"输出目录: {output_dir}")
    
    # 检查是否还有超大文件
    oversized = [f for f, size in saved_files if size > max_size_kb]
    if oversized:
        print(f"\n⚠️ 警告: 以下 {len(oversized)} 个文件仍然超过 {max_size_kb} KB:")
        for filepath in oversized:
            size = get_file_size_kb(filepath)
            print(f"  - {os.path.basename(filepath)}: {size:.2f} KB")
        print("建议手动检查这些文件是否需要进一步处理")
    
    print(f"{'='*60}\n")
    
    return output_dir

# 使用示例
if __name__ == "__main__":
    # 示例：切分一个文件
    # split_markdown_document('路径', source_language='源语言', max_size_kb=30)
    pass
    ```
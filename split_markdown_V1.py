import argparse
import os
import re
from typing import List, Optional, Tuple

DEFAULT_MAX_CHUNK_KB = 30
DEFAULT_MIN_CHUNK_KB = 10
DEFAULT_MAX_HEADER_LEVEL = 6

_HEADING_RE = re.compile(r'^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$')
_FENCE_MARK_RE = re.compile(r'^[ \t]{0,3}([`~]{3,})[ \t]*.*$')
_OUTPUT_FILE_RE_TEMPLATE = r'^\d+_{base}\.md$'


def get_file_size_kb(file_path: str) -> float:
    """获取文件大小（KB）"""
    return os.path.getsize(file_path) / 1024


def get_text_size_kb(text: str) -> float:
    """计算文本大小（KB），避免临时文件"""
    return len(text.encode('utf-8')) / 1024


def _parse_fence_marker(line: str) -> Optional[Tuple[str, int]]:
    """解析围栏标记，返回(符号字符, 连续长度)。"""
    match = _FENCE_MARK_RE.match(line.rstrip('\n\r'))
    if not match:
        return None
    marker = match.group(1)
    return marker[0], len(marker)


def split_by_header_level(content: str, header_level: int) -> List[str]:
    """
    按指定标题级别切分。
    仅匹配严格 ATX 标题（行首 #，且 # 后至少一个空白），并忽略代码块内内容。
    """
    if not 1 <= header_level <= 6:
        return [content]

    lines = content.splitlines(keepends=True)
    heading_indexes: List[int] = []
    in_fence = False
    fence_char = ''
    fence_len = 0

    for idx, line in enumerate(lines):
        fence = _parse_fence_marker(line)
        if fence:
            mark_char, mark_len = fence
            if not in_fence:
                in_fence = True
                fence_char = mark_char
                fence_len = mark_len
                continue
            if mark_char == fence_char and mark_len >= fence_len:
                in_fence = False
                fence_char = ''
                fence_len = 0
                continue

        if in_fence:
            continue

        match = _HEADING_RE.match(line.rstrip('\n\r'))
        if not match:
            continue

        if len(match.group(1)) == header_level:
            heading_indexes.append(idx)

    if not heading_indexes:
        return [content]

    chunks: List[str] = []

    if heading_indexes[0] > 0:
        intro = ''.join(lines[: heading_indexes[0]])
        if intro.strip():
            chunks.append(intro)

    for i, start in enumerate(heading_indexes):
        end = heading_indexes[i + 1] if i + 1 < len(heading_indexes) else len(lines)
        chunk = ''.join(lines[start:end])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


def split_chunk_recursive(
    chunk: str,
    current_level: int,
    max_level: int,
    max_size_kb: float,
) -> List[str]:
    """递归按标题层级切分，直到达到大小限制或无更细粒度标题。"""
    if get_text_size_kb(chunk) <= max_size_kb:
        return [chunk]

    if current_level > max_level:
        return [chunk]

    parts = split_by_header_level(chunk, current_level)
    if len(parts) <= 1:
        return split_chunk_recursive(chunk, current_level + 1, max_level, max_size_kb)

    result: List[str] = []
    for part in parts:
        result.extend(split_chunk_recursive(part, current_level + 1, max_level, max_size_kb))
    return result


def merge_small_chunks(chunks: List[str], min_size_kb: float, max_size_kb: float) -> List[str]:
    """自动合并过小分块；若合并后超过上限则不合并。"""
    if not chunks:
        return []

    merged: List[str] = []
    current = chunks[0]

    for next_chunk in chunks[1:]:
        current_size = get_text_size_kb(current)
        next_size = get_text_size_kb(next_chunk)
        combined = current + ('\n' if not current.endswith('\n') else '') + next_chunk
        combined_size = get_text_size_kb(combined)

        should_try_merge = current_size < min_size_kb or next_size < min_size_kb
        if should_try_merge and combined_size <= max_size_kb:
            current = combined
        else:
            merged.append(current)
            current = next_chunk

    merged.append(current)
    return merged


def _cleanup_existing_chunk_files(output_dir: str, base_name: str) -> None:
    """清理旧分块文件，避免重复运行时残留。"""
    if not os.path.isdir(output_dir):
        return

    file_re = re.compile(_OUTPUT_FILE_RE_TEMPLATE.format(base=re.escape(base_name)))
    for name in os.listdir(output_dir):
        if file_re.match(name):
            path = os.path.join(output_dir, name)
            if os.path.isfile(path):
                os.remove(path)


def save_chunks(chunks: List[str], output_dir: str, base_name: str) -> List[str]:
    """保存切分后的文件"""
    os.makedirs(output_dir, exist_ok=True)
    _cleanup_existing_chunk_files(output_dir, base_name)

    saved_files: List[str] = []
    for i, chunk in enumerate(chunks, 1):
        filename = f"{i:02d}_{base_name}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chunk)
        saved_files.append(filepath)

    return saved_files


def _validate_params(max_size_kb: float, min_size_kb: float, max_header_level: int) -> None:
    if max_size_kb <= 0:
        raise ValueError('max_size_kb must be > 0')
    if min_size_kb < 0:
        raise ValueError('min_size_kb must be >= 0')
    if min_size_kb > max_size_kb:
        raise ValueError('min_size_kb must be <= max_size_kb')
    if not 1 <= max_header_level <= 6:
        raise ValueError('max_header_level must be between 1 and 6')


def split_markdown_document(
    file_path: str,
    max_size_kb: float = DEFAULT_MAX_CHUNK_KB,
    min_size_kb: float = DEFAULT_MIN_CHUNK_KB,
    max_header_level: int = DEFAULT_MAX_HEADER_LEVEL,
) -> str:
    """
    切分 Markdown 文档。

    参数:
        file_path: 源文件路径
        max_size_kb: 最大分块大小（KB，默认 30）
        min_size_kb: 最小分块大小（KB，默认 10）
        max_header_level: 递归切分的最大标题层级（默认 6）
    """
    _validate_params(max_size_kb=max_size_kb, min_size_kb=min_size_kb, max_header_level=max_header_level)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    work_dir = os.path.dirname(file_path) or '.'
    output_dir = os.path.join(work_dir, f"{base_name}_split")

    if get_file_size_kb(file_path) <= max_size_kb:
        save_chunks([content], output_dir, base_name)
        return output_dir

    initial_chunks = split_chunk_recursive(
        chunk=content,
        current_level=1,
        max_level=max_header_level,
        max_size_kb=max_size_kb,
    )

    final_chunks = merge_small_chunks(initial_chunks, min_size_kb=min_size_kb, max_size_kb=max_size_kb)
    save_chunks(final_chunks, output_dir, base_name)

    return output_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Split markdown by heading levels and chunk size.')
    parser.add_argument('file_path', help='Markdown 文件路径')
    parser.add_argument('--max-size-kb', type=float, default=DEFAULT_MAX_CHUNK_KB, help='最大分块大小（KB）')
    parser.add_argument('--min-size-kb', type=float, default=DEFAULT_MIN_CHUNK_KB, help='最小分块大小（KB）')
    parser.add_argument('--max-header-level', type=int, default=DEFAULT_MAX_HEADER_LEVEL, help='最大标题层级（1-6）')
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    split_markdown_document(
        file_path=args.file_path,
        max_size_kb=args.max_size_kb,
        min_size_kb=args.min_size_kb,
        max_header_level=args.max_header_level,
    )

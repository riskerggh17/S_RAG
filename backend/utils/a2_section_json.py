# a2_section_json.py
import re
import json
import time
import pandas as pd
import tiktoken
import hashlib
from tqdm import tqdm
from functools import lru_cache
from typing import List, Tuple, Dict, Any
import matplotlib.pyplot as plt
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter, Language
from pathlib import Path
path = Path().cwd()


# 配置区域
# JSON_PATH = path / 'cleaned_data'
JSON_PATH = path / 'test'

# 切片配置
CHUNK_SIZE = 512      # 目标 Token 数
MAX_CHUNK_SIZE = 1024  # 最大 Token 数
CHUNK_OVERLAP = 100     # 重叠 Token 数
CODE_CHUNK_OVERLAP = 200  # 代码重叠
MIN_CHUNK_SIZE = 100  # 超小块阈值
# 预编译正则表达式，提升匹配速度
CUSTOM_PATTERN = re.compile(r'(###CODE_BLOCK_START###.*?###CODE_BLOCK_END###)', flags=re.DOTALL)
LANG_PATTERN = re.compile(r'###CODE_BLOCK_START###\|lang=([^\n]+)')
# 代码语言枚举
LANGUAGE_MAP = {
    "python": Language.PYTHON,
    "c": Language.C,
    "cpp": Language.CPP,
    "java": Language.JAVA,
    "go": Language.GO,
    "rust": Language.RUST,
    "py": Language.PYTHON,
    "js": Language.JS,
    "typescript": Language.TS,
    "ts": Language.TS,
    "markdown": Language.MARKDOWN,
    "md": Language.MARKDOWN,
    "console": Language.MARKDOWN,
}
# 提前编译
try:
    encoding = tiktoken.encoding_for_model('gpt-4')
except:
    encoding = tiktoken.get_encoding("cl100k_base")

@lru_cache(maxsize=1000)
def count_tokens(text: str) -> int:
    """
    计算文本token
    """
    try:
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error encoding text: {e}")
        return len(text) // 4
    # return len(text) // 4
    


markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header_1"),
        ("##", "Header_2"),
        ("###", "Header_3"),
        ("####", "Header_4"),
        ("#####", "Header_5"),
        ("######", "Header_6")
    ],
    strip_headers=False  # 保留标题
)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=count_tokens,
    separators=["\n\n", "\n", ".", "。", "  ", ""]
)




def load_json(clean_data) -> list:
    """
    加载清洗后的json数据
    """
    raw_data = []
    print("📄 加载数据...")
    for t_json in clean_data.iterdir():
        if t_json.is_file():
            try:
                with open(t_json, 'r', encoding='utf-8') as f:
                    temp_data = json.load(f)
                    if isinstance(temp_data, list):
                        raw_data.extend(temp_data)
                    elif isinstance(temp_data, dict):
                        raw_data.append(temp_data)
                    else:
                        print(f"文件 {t_json} 格式错误")
            except Exception as e:
                print(f"文件 {t_json} 加载失败：{e}")
    # print(f"✅ 数据加载完成，共 {len(raw_data)} 条数据。")
    return raw_data


def parse_code_block(text: str) -> Tuple[str, Dict[str, str]]:
    """
    解析代码块
    """
    code_map = {}
    matches = CUSTOM_PATTERN.finditer(text)
    for i, code_content in enumerate(matches):
        code_content = code_content.group(1)
        placeholder = f"__CODE_BLOCK_{i}__"
        # # 提取语言标识
        lang_match = LANG_PATTERN.findall(code_content)
        lang = lang_match[0] if lang_match else "text"
        code_map[placeholder] = {
            "lang": lang,
            "tokens": count_tokens(code_content),
            "content": code_content
        }
        text = text.replace(code_content, placeholder, 1)
    # print(code_map)
    return text, code_map


def recover_code_block(text: str, code_map: Dict[str,str]):
    """
    恢复代码块
    """
    if not code_map:
        return text
    recovered_text = text
    # 遍历替换
    for placeholder, code_info in code_map.items():
        if placeholder in recovered_text:
            original_code = code_info.get('content')
            recovered_text = recovered_text.replace(placeholder, original_code, 1)
    return recovered_text


def restore_code_block(text: str) -> str:
    """
    修复代码块格式
    """
    # 1. 处理完整的代码块：有头有尾
    # 匹配 ###CODE_BLOCK_START###|lang=xxx\n内容###CODE_BLOCK_END###
    complete_pattern = re.compile(
        r'###CODE_BLOCK_START###\|lang=([^\n]+)\n([\s\S]*?)###CODE_BLOCK_END###',
        re.DOTALL
    )
    
    def replace_complete(match):
        lang = match.group(1).strip()
        code_content = match.group(2).strip()
        return f"```{lang}\n{code_content}\n```"
    
    # 先替换所有完整的代码块
    text = complete_pattern.sub(replace_complete, text)
    
    # 2. 处理被切断的“头部残块”：有开头，没结尾（后面被切走了）
    # 匹配 ###CODE_BLOCK_START###|lang=xxx\n内容(直到字符串末尾)
    head_pattern = re.compile(
        r'###CODE_BLOCK_START###\|lang=([^\n]+)\n([\s\S]*)$',
        re.DOTALL | re.MULTILINE
    )
    
    def replace_head(match):
        lang = match.group(1).strip()
        code_content = match.group(2).strip()
        # 提示用户代码被截断
        return f"```{lang}\n{code_content}\n[...代码块过长被截断...]"
    
    text = head_pattern.sub(replace_head, text)
    
    # 3. 处理被切断的“尾部残块”：没开头，有结尾（前面被切走了）
    # 匹配 (从字符串开头直到)###CODE_BLOCK_END###
    tail_pattern = re.compile(
        r'^([\s\S]*?)###CODE_BLOCK_END###',
        re.DOTALL | re.MULTILINE
    )
    
    def replace_tail(match):
        code_content = match.group(1).strip()
        # 由于丢失了语言标识，默认使用 text 格式
        return f"[...代码块过长被截断...]\n{code_content}\n```"
    
    text = tail_pattern.sub(replace_tail, text)
    
    return text


def section_code_block(code_info: dict, base_metadata: dict) -> list:
    """
    超大代码块切片
    """
    code_content = code_info.get('content')
    lang_str = code_info.get('lang').lower()
    # 获取语言枚举
    lang_enum = LANGUAGE_MAP.get(lang_str, Language.MARKDOWN)
    code_splitter = RecursiveCharacterTextSplitter.from_language(
        language=lang_enum,
        chunk_size=MAX_CHUNK_SIZE,
        chunk_overlap=CODE_CHUNK_OVERLAP,
        length_function=count_tokens
    )
    # 执行切分
    sub_code_docs = code_splitter.create_documents([code_content])
    final_docs = []
    for i, doc in enumerate(sub_code_docs):
        new_metadata = base_metadata.copy()
        new_metadata['token_count'] = count_tokens(doc.page_content)
        new_metadata['has_code_block'] = True
        new_metadata['is_code_block'] = True
        final_docs.append(Document(
            page_content=doc.page_content,
            metadata=new_metadata
        ))
    return final_docs


def merge_small_chunks(final_chunks: list) -> List[Dict[str, Any]]:
    """
    合并小块
    """
    if len(final_chunks) <= 1:
        return final_chunks.copy()
    # 滑动窗口初始化
    merged_chunks = [final_chunks[0].model_copy()]
    # 从第二块开始
    for i in range(1, len(final_chunks)):
        current_chunk = final_chunks[i]
        # 结果列表最后一块
        prev_chunk_in_result = merged_chunks[-1]
        current_meta = current_chunk.metadata
        prev_meta = prev_chunk_in_result.metadata
        
        current_tokens = current_meta.get("token_count")
        total_tokens = current_tokens + prev_meta['token_count']
        current_path = current_meta.get("path")
        prev_path = prev_meta.get("path")
        # 判断
        should_merge = (
            current_tokens < MIN_CHUNK_SIZE and
            total_tokens < MAX_CHUNK_SIZE and
            current_path == prev_path
        )
        if should_merge:
            # 合并
            prev_chunk_in_result.page_content += "\n" + current_chunk.page_content
            prev_chunk_in_result.metadata['token_count'] = total_tokens
        else:
            # 不合并
            merged_chunks.append(current_chunk.model_copy())
    return merged_chunks
    

def generate_stable_id(path: str, content: str, index: int) -> str:
    """
    生成稳定的 Chunk ID
    策略：md5(文件路径) + _ + md5(内容前100字符)
    这样即使文件其他部分变动，只要这个块内容没变，ID 就不变
    """
    # 1. 文件路径哈希 (确保不同文件的相同内容 ID 不同)
    path_hash = hashlib.md5(path.encode('utf-8')).hexdigest()[:8]
    
    # 2. 内容哈希 (确保内容不变 ID 就不变)
    # 取前 100 字符足以区分大部分块，避免长文本哈希开销
    content_sample = content[:100] if content else ""
    content_hash = hashlib.md5(content_sample.encode('utf-8')).hexdigest()[:8]
    
    return f"{path_hash}_{content_hash}"


def smart_section_json(raw_datas: list) -> list:
    """
    切片json数据
    """
    final_chunks = []
    for raw_data in raw_datas:
        content = raw_data.get('content')
        if not content:
            continue
        # 提取元数据
        id = raw_data.get('id')
        source = raw_data.get('source')
        category = raw_data.get('category')
        path = raw_data.get('path')

        # 1 提取代码块
        content_withot_code, code_map = parse_code_block(content)
        # 2 按标题切片
        header_chunks = markdown_splitter.split_text(content_withot_code)
        # print(f"✅ 切片完成，共 {len(header_chunks)} 个切片。")
        # for i in header_chunks:
        #     print('--' * 50)
        #     print(i)
        # 3 递归深度处理
        for i, chunk in enumerate(header_chunks):
            # 提取元数据
            chunk.metadata = {
                'id': id,
                'source': source,
                'category': category,
                'path': path,
            }
            # 提取标识符
            placeholder_in_chunk = [p for p in code_map.keys() if p in chunk.page_content]
            # 计算代码块token数
            code_tokens_in_chunk = sum(code_map[p]['tokens'] for p in placeholder_in_chunk)
            # 文本token数
            text_tokens = count_tokens(chunk.page_content)
            # 动态计算
            total_tokens = text_tokens + code_tokens_in_chunk
            # 情况1 总token未超限
            if total_tokens <= MAX_CHUNK_SIZE:
                chunk.metadata['token_count'] = total_tokens
                chunk.metadata['has_code_blocks'] = bool(placeholder_in_chunk)
                # 恢复代码块
                chunk.page_content = recover_code_block(chunk.page_content, code_map)
                final_chunks.append(chunk)
            else:
                # 情况2 超限，
                sub_chunks = text_splitter.split_text(chunk.page_content)
                for sub_chunk in sub_chunks:
                    # 找出子块中包含的代码块占位符
                    sub_placeholders = [p for p in code_map.keys() if p in sub_chunk]
                    sub_code_tokens = sum(code_map[p]['tokens'] for p in sub_placeholders)
                    # 重新计算子块的总token
                    sub_text_tokens = count_tokens(sub_chunk)
                    sub_total_tokens = sub_text_tokens + sub_code_tokens
                    # 如果子块超大，且包含超大代码块，触发代码切片逻辑
                    if sub_total_tokens > MAX_CHUNK_SIZE and sub_placeholders:
                        processed_docs = []
                        # 记录已处理占位符
                        handled_placeholders = set()
                        # 提取超大代码块
                        for p in sub_placeholders:
                            code_info = code_map[p]
                            if code_info['tokens'] > CHUNK_SIZE:
                                # 代码块专用处理逻辑
                                temp_metadata = {**chunk.metadata}
                                code_docs = section_code_block(code_info, temp_metadata)
                                processed_docs.extend(code_docs)
                                handled_placeholders.add(p)
                        # 处理剩余的非超大代码文本内容
                        # 将已经作为独立代码块提取出去的占位符从文本中剔除
                        remaining_text = sub_chunk
                        for p in handled_placeholders:
                            remaining_text = remaining_text.replace(p, "")

                        # 处理剩余内容
                        if remaining_text.strip():
                            remaining_tokens = count_tokens(remaining_text)
                            if remaining_tokens > 0:
                                final_text_chunk = Document(
                                    page_content=remaining_text,
                                    metadata={**chunk.metadata, "has_code_blocks": False}
                                )
                                final_text_chunk.metadata['token_count'] = remaining_tokens
                                processed_docs.append(final_text_chunk)
                        final_chunks.extend(processed_docs)
                    else:
                        # 正常保存
                        new_chunk = Document(
                            page_content=sub_chunk,
                            metadata={**chunk.metadata}
                        )
                        new_chunk.metadata['token_count'] = sub_total_tokens
                        new_chunk.metadata['has_code_blocks'] = bool(sub_placeholders)
                        final_chunks.append(new_chunk)
    final_chunks =  merge_small_chunks(final_chunks)
    # print("✅ 小chunk合并完成。")
    # 修复代码块格式
    repaired_chunks = []
    for chunk in final_chunks:
        # 1 修复内容
        repaired_content = restore_code_block(chunk.page_content)
        # 2 重新构建Document
        stable_id = generate_stable_id(
            path=chunk.metadata.get('path', ''), 
            content=repaired_content
        )
        chunk.metadata['chunk_id'] = stable_id
        repaired_chunk = Document(
            page_content=repaired_content,
            metadata=chunk.metadata
        )
        repaired_chunks.append(repaired_chunk)
    # print("✅ 代码块格式修复完成。")
    return repaired_chunks


def show_chunk_tokens(tokens_list: list):
    plt.figure(figsize=(10, 5))
    plt.plot(tokens_list, linewidth=1)
    plt.grid(True, alpha=0.3)
    plt.savefig("chunk_tokens.png")


def save_to_json(chunks, output_path="processed_chunks.json"):
    """
    将切片后的 Document 对象列表保存为包含元数据的 JSON 文件
    """
    json_data = []
    
    print(f"📝 正在序列化 {len(chunks)} 个切片...")
    
    for i, chunk in tqdm(enumerate(chunks), desc="处理中", total=len(chunks)):
        content = chunk.page_content
        # 构建数据结构
        item = {
            # 1. 核心文本内容
            "text": content,
            # 2. 元数据信息 (完全保留你指定的字段)
            "metadata": {
                "id": chunk.metadata.get('id'),
                "source": chunk.metadata.get('source'),
                "token_count":chunk.metadata.get('token_count'),
                "chunk_id": chunk.metadata.get('chunk_id'),
                "category": chunk.metadata.get('category'),
                "path": chunk.metadata.get('path')
            },
            # 3. 全局唯一ID (用于向量库去重或索引)
            "chunk_id": chunk.metadata.get('chunk_id')
        }
        json_data.append(item)
    
    # 写入文件
    # ensure_ascii=False 保证中文正常显示，而不是 \u 编码
    # indent=2 让 JSON 格式化缩进，方便人工查看
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 保存成功！文件路径: {output_path}")
    print(f"📊 总切片数: {len(json_data)}")


def inspet_chunks(chunks: list):
    data = []
    for chunk in chunks:
        data.append({
            "Metadata_ID": chunk.metadata.get('id', ''),
            "Source": chunk.metadata.get('source', ''),
            "Token_Count": chunk.metadata.get('token_count', 0), # 👈 新增列
            "Content_Length": len(chunk.page_content),
            "Content_Preview": chunk.page_content[:100] + "..." # 预览前100字符
        })
    return pd.DataFrame(data)



def section_json(clean_path, section_path):
    # 加载数据
    all_data = load_json(clean_path)
    # 切片
    section_data = smart_section_json(all_data)
    # 检查
    # tokens_list = [chunk.metadata.get('token_count') for chunk in section_data]
    # print(len(tokens_list))
    # show_chunk_tokens(tokens_list)
    save_to_json(section_data, section_path)


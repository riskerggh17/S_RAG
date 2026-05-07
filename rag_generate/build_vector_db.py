# build_vector_db.py
import os
import re
import json
import torch
from tqdm import tqdm
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from pathlib import Path
path = Path().cwd()
print(path)

# 配置区域
MODEL_PATH = r'E:\py_obj\S_RAG\models\bge-m3-unsupervised'
JSON_PATH = path / 'cleaned_data'
PERSIST_DIR = path / 'chroma_db'

# 切片配置
CHUNK_SIZE = 400       # 目标 Token 数
CHUNK_OVERLAP = 50     # 重叠 Token 数


def load_json() -> list:
    raw_data = []
    print("📄 加载数据...")
    for t_json in JSON_PATH.iterdir():
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
    print(f"✅ 数据加载完成，共 {len(raw_data)} 条数据。")
    return raw_data


def parse_front_matter(content):
    """
    解析 Front Matter，提取 title, keywords 等元数据，并返回清洗后的正文
    """
    # 匹配 --- 开头和结尾的块
    match = re.search(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    metadata = {}
    clean_content = content
    
    if match:
        front_matter_text = match.group(1)
        clean_content = content[match.end():] # 移除 front matter 后的正文
        
        # 简单解析 key: value
        for line in front_matter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
    
    return metadata, clean_content


def smart_split_with_metadata(documents, chunk_size=400, chunk_overlap=50):
    """
    核心切片逻辑：
    1. 提取元数据
    2. 标题前置
    3. 代码块保护
    4. Token 限制
    """
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    
    final_chunks = []
    code_block_pattern = re.compile(r'(###CODE_BLOCK_START###.*?###CODE_BLOCK_END###)', re.DOTALL)
    
    for doc in tqdm(documents, desc="切片处理"):
        # 1. 解析元数据
        front_matter, clean_content = parse_front_matter(doc.page_content)
        
        title = front_matter.get('title', 'Unknown')
        keywords = front_matter.get('keywords', '')
        category = doc.metadata.get('category', 'general')
        source_id = doc.metadata.get('id', '')
        
        # 2. 准备切片上下文：标题 + 正文
        # 注意：我们将标题加在每一段的前面，这对向量检索至关重要
        text_to_split = f"# {title}\n\n{clean_content}"
        
        # 3. 分割代码块和普通文本
        parts = code_block_pattern.split(text_to_split)
        
        current_chunk_text = ""
        current_chunk_tokens = 0
        chunk_idx = 0
        
        for part in parts:
            is_code_block = part.startswith("###CODE_BLOCK_START###")
            # 计算 token，去掉特殊标记
            part_tokens = len(tokenizer.encode(part, add_special_tokens=False))
            
            # 策略：如果当前块是代码块，且当前累积文本不为空
            # 且 累积+代码 > 限制，则先保存累积文本，代码块单独起一个块
            # 这样可以保证代码块尽可能独立，或者紧跟在少量文本后，且不被切碎
            
            if is_code_block:
                # 代码块逻辑
                if part_tokens > chunk_size:
                    # 极罕见情况：代码块本身超长，强制切分（虽然需求说强制不切，但物理限制必须处理）
                    # 这里简单处理：直接作为独立块，超过部分截断或警告
                    print(f"⚠️ 警告: 发现超长代码块 ({part_tokens} tokens)")
                    final_chunks.append(Document(
                        page_content=part,
                        metadata={**doc.metadata, "title": title, "keywords": keywords, "chunk_id": chunk_idx}
                    ))
                    chunk_idx += 1
                else:
                    # 代码块不超长
                    if current_chunk_tokens + part_tokens > chunk_size and current_chunk_text.strip():
                        # 塞不下，先存前面的
                        final_chunks.append(Document(
                            page_content=current_chunk_text,
                            metadata={**doc.metadata, "title": title, "keywords": keywords, "chunk_id": chunk_idx}
                        ))
                        chunk_idx += 1
                        current_chunk_text = ""
                        current_chunk_tokens = 0
                    
                    # 代码块单独作为一个块（或者尝试拼接到空块中）
                    # 为了检索效果，代码块最好带一点上下文，但这里为了简单，如果前面有残留则拼接，否则独立
                    final_chunks.append(Document(
                        page_content=part,
                        metadata={**doc.metadata, "title": title, "keywords": keywords, "chunk_id": chunk_idx}
                    ))
                    chunk_idx += 1
            else:
                # 普通文本逻辑
                if current_chunk_tokens + part_tokens > chunk_size:
                    # 满了，存盘
                    if current_chunk_text.strip():
                        final_chunks.append(Document(
                            page_content=current_chunk_text,
                            metadata={**doc.metadata, "title": title, "keywords": keywords, "chunk_id": chunk_idx}
                        ))
                        chunk_idx += 1
                    
                    # 开启新块
                    current_chunk_text = part
                    current_chunk_tokens = part_tokens
                else:
                    # 拼接
                    if current_chunk_text:
                        current_chunk_text += "\n" + part
                    else:
                        current_chunk_text = part
                    current_chunk_tokens += part_tokens
        
        # 处理剩余
        if current_chunk_text.strip():
            final_chunks.append(Document(
                page_content=current_chunk_text,
                metadata={**doc.metadata, "title": title, "keywords": keywords, "chunk_id": chunk_idx}
            ))
            
    return final_chunks



def main():
    # 1. 加载原始数据
    raw_data = load_json()

    print("🔄 正在转换为 Document 对象...")
    docs = []
    for item in raw_data:
        docs.append(Document(page_content=item['content'], metadata={"id": item['id'], "category": item.get('category', '')}))
        
    # 2. 智能切片与元数据增强
    split_docs = smart_split_with_metadata(docs, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"✅ 切片完成，共 {len(split_docs)} 个块")
    
    # 打印一个示例看看元数据构造效果
    print(f"示例元数据: {split_docs[0].metadata}")
    print(f"示例内容预览: {split_docs[0].page_content[:100]}...")
    



    
    print("🎉 完成！")



if __name__ == '__main__':
    main()


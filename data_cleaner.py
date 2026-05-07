"""
Docker文档数据清洗与RAG准备脚本

针对四类Docker文档的差异化处理：
1. get-started: 入门教程 - 概念解释、基础操作
2. guides: 实践指南 - 代码示例、最佳实践
3. manuals: 产品手册 - 配置参数、运维指导
4. reference: API参考 - 技术规格、命令定义
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import yaml


@dataclass
class DocumentChunk:
    """文档分块数据结构"""
    content: str
    metadata: Dict[str, Any]
    doc_type: str  # get-started, guides, manuals, reference
    chunk_id: str
    source_file: str


class DockerDocCleaner:
    """Docker文档清洗器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.content_dir = self.base_dir / "docker" / "content"
        self.output_dir = self.base_dir / "processed_data"
        self.output_dir.mkdir(exist_ok=True)
        
        # 四类文档目录
        self.doc_types = {
            'get-started': self.content_dir / 'get-started',
            'guides': self.content_dir / 'guides',
            'manuals': self.content_dir / 'manuals',
            'reference': self.content_dir / 'reference'
        }
        
    def extract_front_matter(self, content: str) -> tuple[str, Dict]:
        """提取YAML front matter元数据"""
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            yaml_content = match.group(1)
            main_content = match.group(2)
            try:
                metadata = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                metadata = {}
            return main_content, metadata
        return content, {}
    
    def clean_markdown(self, text: str, preserve_code: bool = True) -> str:
        """清理Markdown格式，可选择保留代码块"""
        # 移除图片引用但保留alt文本
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        
        # 移除链接但保留文本
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # 清理多余的空行（保留最多2个连续空行）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 清理行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def extract_sections(self, content: str, doc_type: str) -> List[Dict]:
        """根据文档类型提取逻辑段落"""
        sections = []
        
        # 按二级标题分割
        parts = re.split(r'\n## ', content)
        
        for i, part in enumerate(parts):
            if i == 0 and not part.startswith('#'):
                # 第一部分可能是引言
                if part.strip():
                    sections.append({
                        'title': 'Introduction',
                        'content': part.strip(),
                        'level': 0
                    })
            else:
                # 提取标题和内容
                lines = part.split('\n', 1)
                title = lines[0].strip()
                body = lines[1].strip() if len(lines) > 1 else ''
                
                if body:
                    sections.append({
                        'title': title,
                        'content': body,
                        'level': 2
                    })
        
        return sections
    
    def create_metadata(self, front_matter: Dict, doc_type: str, file_path: Path, 
                       section_title: str = None) -> Dict:
        """创建增强的元数据"""
        metadata = {
            'doc_type': doc_type,
            'source_file': str(file_path.relative_to(self.content_dir)),
            'title': front_matter.get('title', ''),
            'description': front_matter.get('description', ''),
            'keywords': front_matter.get('keywords', ''),
        }
        
        if section_title:
            metadata['section'] = section_title
            
        # 根据不同类型添加特定元数据
        if doc_type == 'guides':
            metadata['time_estimate'] = front_matter.get('params', {}).get('time', '')
            metadata['tags'] = front_matter.get('tags', [])
        elif doc_type == 'reference':
            metadata['api_version'] = front_matter.get('version', '')
            
        return metadata
    
    def chunk_document(self, content: str, doc_type: str, max_chunk_size: int = 1000) -> List[str]:
        """智能分块策略（根据文档类型调整）"""
        
        # 不同类型使用不同的分块大小
        chunk_sizes = {
            'get-started': 800,   # 入门教程：较小块，便于理解
            'guides': 1200,       # 实践指南：中等块，保留完整步骤
            'manuals': 1000,      # 产品手册：标准块
            'reference': 600      # API参考：小块，精确检索
        }
        
        target_size = chunk_sizes.get(doc_type, max_chunk_size)
        
        # 按段落分块
        paragraphs = re.split(r'\n\n+', content)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > target_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def process_file(self, file_path: Path, doc_type: str) -> List[DocumentChunk]:
        """处理单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
        
        # 提取front matter
        content, front_matter = self.extract_front_matter(raw_content)
        
        # 清理Markdown
        cleaned_content = self.clean_markdown(content)
        
        # 提取章节
        sections = self.extract_sections(cleaned_content, doc_type)
        
        chunks = []
        chunk_counter = 0
        
        for section in sections:
            # 对每个章节进行分块
            section_chunks = self.chunk_document(
                section['content'], 
                doc_type
            )
            
            for chunk_content in section_chunks:
                metadata = self.create_metadata(
                    front_matter, 
                    doc_type, 
                    file_path,
                    section['title']
                )
                
                chunk = DocumentChunk(
                    content=chunk_content,
                    metadata=metadata,
                    doc_type=doc_type,
                    chunk_id=f"{doc_type}_{file_path.stem}_{chunk_counter}",
                    source_file=str(file_path)
                )
                chunks.append(chunk)
                chunk_counter += 1
        
        return chunks
    
    def process_all_documents(self) -> Dict[str, List[DocumentChunk]]:
        """处理所有文档"""
        all_chunks = {doc_type: [] for doc_type in self.doc_types.keys()}
        
        for doc_type, dir_path in self.doc_types.items():
            if not dir_path.exists():
                print(f"Warning: Directory {dir_path} does not exist")
                continue
                
            print(f"\nProcessing {doc_type} documents...")
            
            # 递归查找所有.md文件
            md_files = list(dir_path.rglob('*.md'))
            print(f"Found {len(md_files)} markdown files")
            
            for file_path in md_files:
                # 跳过索引文件和隐藏文件
                if file_path.name.startswith('_') or file_path.name.startswith('.'):
                    continue
                    
                chunks = self.process_file(file_path, doc_type)
                all_chunks[doc_type].extend(chunks)
                
            print(f"Generated {len(all_chunks[doc_type])} chunks for {doc_type}")
        
        return all_chunks
    
    def save_to_json(self, all_chunks: Dict[str, List[DocumentChunk]]):
        """保存为JSON格式（适合LangChain加载）"""
        output_file = self.output_dir / "docker_docs.json"
        
        data = []
        for doc_type, chunks in all_chunks.items():
            for chunk in chunks:
                data.append({
                    'page_content': chunk.content,
                    'metadata': chunk.metadata
                })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\nSaved {len(data)} chunks to {output_file}")
        return output_file
    
    def save_statistics(self, all_chunks: Dict[str, List[DocumentChunk]]):
        """保存统计信息"""
        stats = {
            'total_chunks': sum(len(chunks) for chunks in all_chunks.values()),
            'by_type': {
                doc_type: {
                    'chunk_count': len(chunks),
                    'avg_chunk_size': sum(len(c.content) for c in chunks) / max(len(chunks), 1),
                    'total_characters': sum(len(c.content) for c in chunks)
                }
                for doc_type, chunks in all_chunks.items()
            }
        }
        
        stats_file = self.output_dir / "statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\nStatistics saved to {stats_file}")
        print(f"\nSummary:")
        print(f"Total chunks: {stats['total_chunks']}")
        for doc_type, info in stats['by_type'].items():
            print(f"  {doc_type}: {info['chunk_count']} chunks, "
                  f"avg size: {info['avg_chunk_size']:.0f} chars")


def main():
    """主函数"""
    # 项目根目录
    base_dir = Path(__file__).parent
    
    print("=" * 60)
    print("Docker文档数据清洗工具")
    print("=" * 60)
    
    # 初始化清洗器
    cleaner = DockerDocCleaner(str(base_dir))
    
    # 处理所有文档
    print("\nStarting document processing...")
    all_chunks = cleaner.process_all_documents()
    
    # 保存结果
    print("\nSaving results...")
    cleaner.save_to_json(all_chunks)
    cleaner.save_statistics(all_chunks)
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

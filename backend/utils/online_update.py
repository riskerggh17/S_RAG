# online_update.py
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
# 把根目录加入系统路径
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import re
import tqdm
import pathlib
import asyncio
from app.config import UPLOAD_DATA, DEALED_DATA
from a2_section_json import smart_section_json


def trans_pdf_to_md(file_path: pathlib.Path):
    """
    pdf文件转换为md文件
    """
    return None

def trans_txt_to_md(file_path: pathlib.Path):
    """
    txt文件转换为md文件
    """
    return None


class MDcleaner:
    def __init__(self, source: str, category: str = 'all'):
        self.source = source  # 数据来源标识
        self.category = category  # 分类标识
        # 正则规则保持不变
        self.image_pattern = re.compile(r'!\[[^\]]*\]\([^\)]+\)')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\([^\)]+\)')
        self.html_pattern = re.compile(r'<[^>]+>')
        self.code_block_pattern = re.compile(r'```(\w*)\n([\s\S]*?)\n```')
    def process_content(self, content: str) -> str:
        """执行核心清洗逻辑"""
        # 1. 清洗阶段
        content = self.image_pattern.sub('', content)
        content = self.link_pattern.sub(r'[\1]', content)
        content = self.html_pattern.sub('', content)
        
        # 2. 代码块保护阶段
        def replace_code_block(match):
            lang = match.group(1) or "text"
            code = match.group(2).strip()
            wrapper = (
                f"\n###CODE_BLOCK_START###|lang={lang}\n"
                f"{code}\n"
                f"###CODE_BLOCK_END###\n"
            )
            return wrapper
            
        content = self.code_block_pattern.sub(replace_code_block, content)
        # 3. 格式化收尾
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    def process_file(self, file_path: Path, base_dir: Path = None) -> dict:
        """
        处理单个文件，返回清洗后的字典数据
        :param file_path: 当前文件的 Path 对象
        :param base_dir: 用于计算相对路径的基准目录（可选）
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # 执行清洗
            final_content = self.process_content(raw_content)
            
            # 构造元数据
            # 如果提供了基准目录，则计算相对路径；否则直接使用文件名
            if base_dir:
                relative_path = file_path.relative_to(base_dir).as_posix()
            else:
                relative_path = file_path.name

            doc = {
                "id": relative_path,
                "source": self.source,
                "category": self.category,
                "path": relative_path,
                "content": final_content
            }
            return doc
        except Exception as e:
            return None



async def onlien_deal_chain():
    """
    全自动批量处理暂存的文件
    """
    # 获取外层文件夹
    file_categorys = [folder.name for folder in UPLOAD_DATA.glob("*/")]
    for file_category in file_categorys:
        # 在输出文件夹创建同名文件夹
        (DEALED_DATA / file_category).mkdir(parents=True, exist_ok=True)
        # 处理内文件夹
        current_cate = UPLOAD_DATA / file_category
        # 类别实例化
        cleaner = MDcleaner(source=file_category, category=file_category)
        # 获取各自的数据
        md_files = [f for f in current_cate.iterdir() if f.is_file() and f.suffix == '.md']
        pdf_files = [f for f in current_cate.iterdir() if f.is_file() and f.suffix == '.pdf']
        txt_files = [f for f in current_cate.iterdir() if f.is_file() and f.suffix == '.txt']

        for pdf_file in pdf_files:
            temp_file = trans_pdf_to_md(pdf_file)
            md_files.append(temp_file)
        
        for txt_file in txt_files:
            temp_file = trans_txt_to_md(txt_file)
            md_files.append(temp_file)
        # 完整chain
        for md_file in tqdm.tqdm(md_files, desc=f"清洗{file_category}中"):
            # 清洗
            cleaned_doc = cleaner.process_file(md_file, base_dir=current_cate)
            if cleaned_doc is None:
                continue
            # 切片
            chunks = smart_section_json([cleaned_doc])
            if chunks is None:
                continue
            # print(len(chunks))
            # print(chunks)
            # 向量化





if __name__ == "__main__":
    asyncio.run(onlien_deal_chain())

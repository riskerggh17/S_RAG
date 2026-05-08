# md_to_vector.py
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
# 把根目录加入系统路径
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入
from a1_clean_markdown import MDCleaner
from a2_section_json import section_json
from a3_use_model_vectorization import vectorization
# 导入配置
from app.config import RAW_DATA, CLEANED_DATA, SECTIONED_DATA, CHROMADB_PATH
from app.config import BGE_M3_MODEL


def clean_chain(source: str='docker'):
    # 1 清洗
    folder_names = [folder.name for folder in RAW_DATA.glob("*/")]
    for folder_name in folder_names:
        folder_ = RAW_DATA / folder_name
        folder_n = [folder.name for folder in folder_.glob("*/")]
        for f in folder_n:
            cleaner = MDCleaner(source_dir=RAW_DATA / folder_name /f, output_file=CLEANED_DATA / f"docker_{f}.json", source=source, category="docker")
            # 执行清洗
            cleaner.clean()
    # 2 切片
    section_json(CLEANED_DATA, SECTIONED_DATA)
    # 3 向量化
    vectorization(model_path=BGE_M3_MODEL, json_file=SECTIONED_DATA, db_path=CHROMADB_PATH)

if __name__ == "__main__":
    clean_chain()

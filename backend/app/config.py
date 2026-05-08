# config.py
# 后端配置文件
from pathlib import Path

# 使用当前文件所在目录作为基准路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 配置地址
# 1 data
# 原始数据
RAW_DATA = BASE_DIR / "raw_data" / "docker"
# 清洗后数据
CLEANED_DATA = BASE_DIR / "data" / "cleaned_data"
# 切片数据
SECTIONED_DATA = BASE_DIR / "data" / "sectioned_data" / "sectioned_data.json"
# chromadb
CHROMADB_PATH = BASE_DIR / "data" / "cdb"

# 2 文档
# 上传数据
UPLOAD_DATA = BASE_DIR / "data" / "upload_data"
# 限制
FILE_MAX_SIZE = 1024 * 1024 * 10  # 限制10M
# 文件头
ALLOWED_FILE_TYPES = [".md", ".txt", ".pdf"]

# 3 model
BGE_M3_MODEL = BASE_DIR / "models" / "bge-m3"
BGE_M3_UNS_MODEL = BASE_DIR / "models" / "bge-m3-unsupervised"

# database.py
# 初始化向量数据库客户端
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
# 把根目录加入系统路径
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
import chromadb
import sqlite3

from app.config import CHROMADB_PATH

client = chromadb.PersistentClient(path=str(CHROMADB_PATH))
collection = client.get_or_create_collection(name="raw_md")

# 向量数据库概览





# database.py
# 初始化向量数据库客户端
import chromadb
from config import CHROMADB_PATH

client = chromadb.PersistentClient(path=str(CHROMADB_PATH))
collection = client.get_or_create_collection(name="raw_md")

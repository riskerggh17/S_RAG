import sys
import json
# from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from pathlib import Path
import transformers
import accelerate
print(f"Transformers 版本: {transformers.__version__}")
print(f"Accelerate 版本: {accelerate.__version__}")

# print('hello')
# pt = Path(r'E:\py_obj\S_RAG\cleaned_data')
# print(pt.iterdir())
# all_data = []
# for item in pt.iterdir():
#     if item.is_file():
#         with open(item, 'r', encoding='utf-8') as f:
#             temp_data = json.load(f)
#             all_data.extend(temp_data)
#         print(f"文件: {item.name}")
#         print(f"数据量: {len(temp_data)}")
# print(f"数据量: {len(all_data)}")
    
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
MODEL_PATH = path / 'models/bga-m3-unsupervised'
JSON_PATH = path / 'cleaned_data'
PERSIST_DIR = path / 'chroma_db'


all_data = []
for item in JSON_PATH.iterdir():
    if item.is_file():
        print(item)
        with open(item, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
            all_data.extend(temp_data)
        print(f"文件: {item.name}")
        print(f"数据量: {len(temp_data)}")
print(f"数据量: {len(all_data)}")


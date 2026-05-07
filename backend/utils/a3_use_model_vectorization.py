# a3_use_model_vectorization.py
import json
from tqdm import tqdm
import torch
import chromadb
import numpy as np
from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig


def load_model_and_tokenizer(local_model_dir):
    """
    加载量化模型和分词器
    """
    print("🔄 正在加载模型组件...")
    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    # 2 分词器
    tokenizer = AutoTokenizer.from_pretrained(
        local_model_dir,
        trust_remote_code=True
    )
    # 3 模型
    model = AutoModel.from_pretrained(
        local_model_dir, 
        trust_remote_code=True, 
        device_map="auto",     
        quantization_config=quantization_config
    )
    print("✅ 模型与分词器加载成功！")
    return model, tokenizer


def load_json_file(json_file):
    """
    加载切片后的json数据，提取文本和元数据
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        # 提取文本
        texts = [item['text'] for item in data_list]
        # 提取元数据 (用于溯源，不需要转为向量)
        metadata = [item['metadata'] for item in data_list]
        print(f"📄 成功读取 {len(texts)} 个文本切片")
        return texts, metadata
    
    except FileNotFoundError:
        print(f"❌ 错误：未找到文件 {json_file}")
        return None, None
    

# ==========================================
# 2. 嵌入函数 (Embedding Function)
# ==========================================
def get_embeddings(text_list, model, tokenizer, batch_size=16):
    """
    将文本列表批量转换为向量
    """
    print("🧠 正在进行分批次向量化编码...")
    # 批处理参数：padding=True 补齐长度，truncation=True 截断超长文本
    # max_length=512 是常用设置，bge-m3 支持更长，但测试用 512 足够
    all_embeddings = []
    for i in tqdm(range(0,len(text_list), batch_size), desc="processing batches"):
        # 获取当前批次的文本
        batch_text = text_list[i:i+batch_size]
        inputs = tokenizer(
            batch_text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=1024
        ).to(model.device)

        with torch.no_grad():
            # 获取模型输出
            outputs = model(**inputs)
            # 提取 [CLS] 向量作为句向量
            # outputs.last_hidden_state shape: [batch_size, seq_len, hidden_dim]
            embeddings = outputs.last_hidden_state[:, 0, :]
            # 归一化 (L2 Normalization) - 这对余弦相似度至关重要
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        all_embeddings.append(embeddings.cpu().numpy())
        # 每批完成清理缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    final_embeddings = np.concatenate(all_embeddings, axis=0)
    print("✅ 向量化完成")
    return final_embeddings



def vectorization(model_path, json_file, db_path):
    try:
        # 1 加载模型和分词器
        model, tokenizer = load_model_and_tokenizer(model_path)
        # 2 加载json文件
        texts, metadata = load_json_file(json_file)
        if texts is None or len(texts) == 0:
            return 
        # 3 批量向量化
        text_embeddings = get_embeddings(texts, model, tokenizer)
        # 4 入库
        # 初始化
        client = chromadb.PersistentClient(path=db_path)
        # 创建或获取集合
        collection = client.get_or_create_collection(name="raw_md")
        # 批量写入
        ids = [f"id_{i}" for i in range(len(texts))]
        collection.add(
            ids=ids,
            embeddings=text_embeddings.tolist(),
            documents=texts,
            metadatas=metadata
        )
        print("✅ 数据入库完成")
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")






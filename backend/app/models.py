# model.py
# 加载模型
import torch
import numpy as np
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig


def load_model_and_tokenizer(model_path):
    """
    加载量化模型和分词器
    """
    print("🔄 正在加载模型组件...")
    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    # 2 分词器
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True
    )
    # 3 模型
    model = AutoModel.from_pretrained(
        model_path, 
        trust_remote_code=True, 
        device_map="auto",     
        quantization_config=quantization_config
    )
    print("✅ 模型与分词器加载成功！")
    return model, tokenizer


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
    return final_embeddings











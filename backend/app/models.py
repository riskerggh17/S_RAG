# model.py
# 加载模型
import torch
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


def get_embeddings(text_list, model, tokenizer):
    print("🧠 正在将你的提问向量化...")
    inputs = tokenizer(
        text_list, 
        return_tensors="pt", 
        padding=True, 
        truncation=True, 
        max_length=1024
    ).to(model.device)

    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0, :]
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    return embeddings.cpu().numpy()











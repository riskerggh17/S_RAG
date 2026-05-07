# search_llm.py
import torch
import chromadb
from transformers import AutoModel, AutoTokenizer, BitsAndBytesConfig

# 基础配置
local_model_dir = r'e:\py_obj\S_RAG\models\bge-m3'
db_path = r"E:\py_obj\S_RAG\db"

def load_model_and_tokenizer(local_model_dir):
    print("🔄 正在加载模型组件...")
    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
    tokenizer = AutoTokenizer.from_pretrained(local_model_dir, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        local_model_dir, 
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



if __name__ == "__main__":
    try:
        # 1. 加载模型（仅用于处理用户的提问）
        model, tokenizer = load_model_and_tokenizer(local_model_dir)
        
        # 2. 连接已有的 Chroma 数据库
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection(name="raw_md")
        print(f"💾 已连接数据库，当前库中共有 {collection.count()} 条数据。")

        # 3. 循环提问环节
        print("\n🤖 RAG 问答系统已就绪，输入 'quit' 或 'exit' 退出。")
        while True:
            query = input("\n❓ 请输入你的问题: ")
            if query.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            # 元数据过滤
            filter_dict = {"source": "docker"}
            # 4. 将提问向量化并检索
            query_embedding = get_embeddings([query], model, tokenizer)
            
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=3,  # 这里可以控制返回前几条
                where=filter_dict
            )
            
            # 5. 打印结果
            print(f"\n🔍 针对问题: \"{query}\" 的检索结果：")
            print("-" * 60)
            for i in range(len(results['ids'][0])):
                print(f"【Top {i+1}】距离: {results['distances'][0][i]:.4f}")
                # 截取前100个字符预览，避免刷屏
                doc_preview = results['documents'][0][i].replace('\n', ' ')[:100] + "..."
                print(f"📄 内容: {doc_preview}")
                print(f"🏷️ 来源: {results['metadatas'][0][i].get('path', 'Unknown')}")
                print("-" * 60)

    except Exception as e:
        print(f"❌ 程序执行出错: {e}")

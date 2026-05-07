# diagnose_db.py
# 诊断向量数据库脚本
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import collection, client
from config import CHROMADB_PATH

def diagnose():
    print("=" * 60)
    print("🔍 RAG 向量数据库诊断工具")
    print("=" * 60)
    
    # 1. 检查数据库路径
    print(f"\n📂 数据库路径: {CHROMADB_PATH}")
    print(f"   路径存在: {os.path.exists(str(CHROMADB_PATH))}")
    
    # 2. 检查 Collection 信息
    print(f"\n📊 Collection 名称: raw_md")
    try:
        count = collection.count()
        print(f"   数据总量: {count} 条")
    except Exception as e:
        print(f"   ❌ 获取数据量失败: {e}")
        return
    
    if count == 0:
        print("\n⚠️  警告: 数据库为空！请先运行向量化脚本入库数据。")
        print("   建议执行: python rag_generate/use_model_vectorization.py")
        return
    
    # 3. 查看示例数据
    print(f"\n📄 示例数据 (前3条):")
    try:
        sample = collection.peek()
        for i, doc in enumerate(sample['documents'][:3]):
            print(f"\n   [{i+1}] 文档预览:")
            print(f"       内容: {doc[:100]}...")
            if sample['metadatas'] and sample['metadatas'][i]:
                print(f"       元数据: {sample['metadatas'][i]}")
            if sample['ids']:
                print(f"       ID: {sample['ids'][i]}")
    except Exception as e:
        print(f"   ❌ 获取示例数据失败: {e}")
    
    # 4. 检查元数据结构
    print(f"\n🏷️  元数据分析:")
    try:
        sample = collection.peek()
        if sample['metadatas'] and sample['metadatas'][0]:
            metadata_keys = list(sample['metadatas'][0].keys())
            print(f"   可用字段: {metadata_keys}")
            
            # 检查是否有 'source' 字段（检索代码中使用的过滤字段）
            if 'source' not in metadata_keys:
                print(f"   ⚠️  警告: 未找到 'source' 字段！")
                print(f"   当前检索代码使用 filter_dict = {{'source': source}}")
                print(f"   但数据库中实际字段为: {metadata_keys}")
                print(f"   这会导致检索时过滤条件失效，返回空结果。")
        else:
            print(f"   ⚠️  警告: 数据没有元数据")
    except Exception as e:
        print(f"   ❌ 分析元数据失败: {e}")
    
    # 5. 测试检索功能
    print(f"\n🧪 测试检索 (使用随机查询):")
    try:
        # BGE-M3 模型的向量维度是 1024
        test_embedding = [[0.0] * 1024]
        
        # 先尝试不加过滤条件
        print(f"   [测试1] 不加过滤条件:")
        results = collection.query(
            query_embeddings=test_embedding,
            n_results=3
        )
        print(f"       返回文档数: {len(results['documents'][0]) if results['documents'] else 0}")
        
        # 再尝试加过滤条件
        print(f"   [测试2] 加过滤条件 source='docker':")
        results_filtered = collection.query(
            query_embeddings=test_embedding,
            n_results=3,
            where={"source": "docker"}
        )
        print(f"       返回文档数: {len(results_filtered['documents'][0]) if results_filtered['documents'] else 0}")
        
        if len(results['documents'][0]) > 0 and len(results_filtered['documents'][0]) == 0:
            print(f"   ⚠️  确认问题: 过滤条件导致检索结果为空！")
            print(f"   原因: metadata 中可能没有 'source' 字段或值不匹配")
            
    except Exception as e:
        print(f"   ❌ 检索测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    diagnose()

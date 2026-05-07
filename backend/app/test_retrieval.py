# test_retrieval.py
# 测试检索功能
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from rag_service import retrieve_context

async def test():
    print("=" * 60)
    print("🧪 RAG 检索功能测试")
    print("=" * 60)
    
    # 测试1：不加过滤条件
    print("\n[测试1] 不加过滤条件 (source='all')")
    result = await retrieve_context("Docker是什么？", source='all', n_results=3)
    print(f"   检索到 {len(result['sources'])} 条结果")
    if result['sources']:
        print(f"   第一条预览: {result['sources'][0].text[:80]}...")
        print(f"   元数据: {result['sources'][0].metadata}")
    
    # 测试2：使用正确的过滤值
    print("\n[测试2] 使用正确的过滤值 (source='get-started')")
    result = await retrieve_context("Docker是什么？", source='get-started', n_results=3)
    print(f"   检索到 {len(result['sources'])} 条结果")
    if result['sources']:
        print(f"   第一条预览: {result['sources'][0].text[:80]}...")
    
    # 测试3：使用错误的过滤值（模拟之前的问题）
    print("\n[测试3] 使用错误的过滤值 (source='docker') - 应该返回0条")
    result = await retrieve_context("Docker是什么？", source='docker', n_results=3)
    print(f"   检索到 {len(result['sources'])} 条结果")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print("\n💡 提示:")
    print("   数据库中 source 字段的可用值为:")
    print("   - 'get-started'")
    print("   - 'guides'")
    print("   - 'manuals'")
    print("   - 'reference'")
    print("   前端应传入这些值之一，或传入 'all' 表示不过滤")

if __name__ == "__main__":
    asyncio.run(test())

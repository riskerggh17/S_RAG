# rag_service.py
# rag集成服务
import asyncio
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from llm import HybridLLMClient
from models import load_model_and_tokenizer, get_embeddings
from database import collection
from config import BGE_M3_MODEL
from schemas import SourceItem
import threading

# 全局变量，避免重复加载模型
_embedding_model = None
_embedding_tokenizer = None
_model_lock = threading.Lock()
# llm客户端
_llm_client = None


def _get_embedding_model_and_tokenizer():
    """
    线程安全的懒加载 Embedding 模型和分词器
    """
    global _embedding_model, _embedding_tokenizer
    # 双重检查锁定 (Double-Checked Locking)
    if _embedding_model is None or _embedding_tokenizer is None:
        with _model_lock:
            if _embedding_model is None or _embedding_tokenizer is None:
                print("🔄 [Cache] 正在首次加载 Embedding 模型...")
                _embedding_model, _embedding_tokenizer = load_model_and_tokenizer(BGE_M3_MODEL)
                print("✅ [Cache] Embedding 模型加载完成并缓存")
    return _embedding_model, _embedding_tokenizer


def _get_llm_client():
    """
    获取 LLM 客户端单例
    """
    global _llm_client
    if _llm_client is None:
        print("🔄 [Cache] 正在初始化 LLM 客户端...")
        _llm_client = HybridLLMClient(local_model='qwen3:4b', fallback_model='qwen-turbo')
        print("✅ [Cache] LLM 客户端初始化完成")
    return _llm_client


async def retrieve_context(question: str, source: str = 'all', n_results: int = 3) -> Dict[str, Any]:
    """
    独立检索模块：负责向量化和数据库查询
    Returns:
        {
            "context_texts": List[str],
            "sources": List[SourceItem],
            "has_content": bool
        }
    """
    try:
        # 1. 获取缓存的模型
        model, tokenizer = _get_embedding_model_and_tokenizer()
        
        # 2. 向量化
        print(f"🔍 [Retrieve] 正在向量化问题: {question[:20]}...")
        embeddings = get_embeddings([question], model, tokenizer)
        
        # 3. 构建过滤条件
        filter_dict = None
        if source and source != 'all':
            # 注意：数据库中 source 字段的值是 'get-started', 'guides', 'manuals', 'reference'
            # 如果前端传入的值与这些不匹配，将检索不到结果
            filter_dict = {"source": source}
            print(f"🔍 [Retrieve] 使用过滤条件: {filter_dict}")
        if source == 'all':
            filter_dict = None
        # 4. 向量检索
        results = collection.query(
            query_embeddings=embeddings.tolist(),
            n_results=n_results,
            where=filter_dict
        )
        
        # 5. 解析结果
        sources = []
        context_texts = []
        
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0.0
                
                sources.append(SourceItem(
                    text=doc,
                    metadata=metadata,
                    score=distance
                ))
                context_texts.append(doc)
                
        print(f"📚 [Retrieve] 检索到 {len(sources)} 条相关文档")
        return {
            "context_texts": context_texts,
            "sources": sources,
            "has_content": len(context_texts) > 0
        }
        
    except Exception as e:
        print(f"❌ [Retrieve] 检索出错: {e}")
        import traceback
        traceback.print_exc()
        return {
            "context_texts": [],
            "sources": [],
            "has_content": False,
            "error": str(e)
        }


def build_system_prompt(context_texts: List[str], has_content: bool) -> str:
    """
    根据检索结果构建 System Prompt
    """
    if has_content and context_texts:
        context = "\n\n".join(context_texts)
        return f"""你是一个RAG系统助手，请严格根据以下【检索到的相关信息】回答问题。
【检索到的相关信息】：
{context}
【要求】：
1. 请基于以上信息用中文回答问题。
2. 如果检索到的信息不足以回答问题，请如实告知“根据现有资料无法回答”，不要编造事实。
3. 保持回答简洁、专业。"""
    else:
        return """你是一个RAG系统助手。
目前未检索到相关的背景信息。
请用中文回答用户的问题。如果问题超出你的知识范围，请如实告知。"""


async def generate_answer(question: str, system_prompt: str, stream: bool = False) -> Any:
    """
    独立生成模块：负责调用 LLM
    Args:
        stream: True 返回 AsyncGenerator, False 返回 str
    """
    llm_client = _get_llm_client()
    
    if stream:
        # 返回异步生成器
        return llm_client.generate_stream(question, system_prompt)
    else:
        # 返回完整字符串
        answer = await llm_client.invoke(
            question=question,
            system_prompt=system_prompt,
            stream=False
        )
        return answer



async def rag_service(question: str, source: str = 'all') -> Dict[str, Any]:
    """
    RAG服务：非流式入口
    """
    print("\n--- 开始处理非流式请求 ---")
    
    # 1. 检索
    retrieval_result = await retrieve_context(question, source)
    
    # 2. 构建 Prompt
    system_prompt = build_system_prompt(
        retrieval_result['context_texts'], 
        retrieval_result['has_content']
    )
    
    # 3. 生成
    print("🤖 [Generate] 正在调用 LLM 生成回答...")
    answer = await generate_answer(question, system_prompt, stream=False)
    print("✅ [Generate] 回答生成完毕")
    
    return {
        "answer": answer,
        "sources": retrieval_result['sources']
    }


async def rag_service_stream(question: str, source: str = 'all') -> AsyncGenerator[str, None]:
    """
    RAG服务：流式入口
    返回 SSE 格式数据
    """
    print("\n--- 开始处理流式请求 ---")
    
    try:
        # 1. 检索 (这一步通常很快，可以同步等待)
        retrieval_result = await retrieve_context(question, source)
        
        # 2. 先发送 Sources 给前端 (让前端先展示引用)
        sources_data = json.dumps({
            "type": "sources",
            "content": [s.dict() for s in retrieval_result['sources']]
        }, ensure_ascii=False)
        yield f"data: {sources_data}\n\n"
        
        # 3. 构建 Prompt
        system_prompt = build_system_prompt(
            retrieval_result['context_texts'], 
            retrieval_result['has_content']
        )
        
        # 4. 流式生成
        print("🤖 [Generate] 正在流式生成回答...")
        stream_generator = await generate_answer(question, system_prompt, stream=True)
        
        async for chunk in stream_generator:
            # 包装成 SSE 格式
            chunk_data = json.dumps({
                "type": "content",
                "content": chunk
            }, ensure_ascii=False)
            yield f"data: {chunk_data}\n\n"
            
        # 5. 发送结束标记
        yield "data: [DONE]\n\n"
        print("✅ [Generate] 流式传输结束")
        
    except Exception as e:
        print(f"❌ [Stream] 流式服务出错: {e}")
        error_data = json.dumps({"type": "error", "content": str(e)})
        yield f"data: {error_data}\n\n"



# 上传文件










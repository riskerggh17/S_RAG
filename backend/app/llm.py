# llm.py
import os
import asyncio
from typing import AsyncGenerator

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
load_dotenv()


class HybridLLMClient:
    def __init__(self, local_model='qwen3:4b', fallback_model='qwen-turbo'):
        """
        初始化混合客户端
        """
        # 1. 初始化本地模型 (优先)
        self.local_llm = ChatOllama(
            model=local_model,
            temperature=0,
            request_timeout=30  # 设置 timeout，防止本地模型卡死
        )
        # 2. 初始化云端备用模型
        self.fallback_llm = ChatOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=fallback_model,
            temperature=0,
        )
        print(f"✅ 混合客户端已启动 (本地: {local_model}, 云端: {fallback_model})")
    
    async def generate_stream(self, question: str, system_prompt: str=None) -> AsyncGenerator[str, None]:
        """
        异步流式生成器
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]
        print("\n🚀 正在尝试使用本地模型...")
        try:
            # 本地模型
            async for chunk in self.local_llm.astream(messages):
                yield chunk.content
        except Exception as local_error:
            print(f"❌ 离线客户端调用失败: {local_error}")
            try:
                # 云端模型
                async for chunk in self.fallback_llm.astream(messages):
                    yield chunk.content
            except Exception as fallbac_error:
                print(f"❌ 在线客户端调用失败: {fallbac_error}")
                yield "本地和云端服务目前均不可用，请稍后重试。"
    
    async def invoke(self, question: str, system_prompt: str=None, stream: bool=False):
        """
        统一调用接口
        """
        if stream:
            return StreamingResponse(
                self.generate_stream(question, system_prompt),
                media_type="text/event-stream"
            )
        else:
            # 同步调用
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=question),
            ]
            try:
                # 离线
                response = await self.local_llm.ainvoke(messages)
                return response.content
            except Exception:
                # 在线
                response = await self.fallback_llm.ainvoke(messages)
                return response.content

async def main():
    load_dotenv()
    client = HybridLLMClient(local_model='qwen3:4b', fallback_model='qwen-turbo')
    
    # 注意这行代码的缩进，它必须在 main 函数内部
    result = await client.invoke(
        question="你好，请介绍一下你自己。",
        system_prompt="你是一个RAG系统助手，根据检索到的信息进行回答，回答使用中文",
        stream=True
    )
    
    print("\n--- 最终回答 ---")
    print(result)

if __name__ == "__main__":
    # 最外层通过 asyncio.run() 来启动这个异步的 main 函数
    asyncio.run(main())
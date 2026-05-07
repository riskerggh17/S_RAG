# main.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from schemas import QueryRequest, QueryResponse
from rag_service import rag_service, rag_service_stream
import warnings
warnings.filterwarnings("ignore", message=".*MatMul8bitLt.*")

# 实例化
app = FastAPI(title='RAG-API')


@app.post("/api/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    RAG问答接口（非流式）
    """
    # 调用RAG服务
    result = await rag_service(
        question=request.question,
        source=request.source
    )
    # 构建响应
    return QueryResponse(
        answer=result['answer'],
        sources=result['sources']
    )

@app.post("/api/ask_stream")
async def ask_question_stream(request: QueryRequest):
    """
    RAG问答接口（流式）
    """
    return StreamingResponse(
        rag_service_stream(request.question, request.source),
        media_type="text/event-stream"
    )


if __name__ == '__main__':
    uvicorn.run(
        app="main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

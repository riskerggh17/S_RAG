# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import uvicorn
from schemas import QueryRequest, QueryResponse, UploadResponse, RefreshRequest
from rag_service import rag_service, rag_service_stream
from file_service import save_local_file

from loguru import logger
import sys

# --- Loguru 基础配置 ---
# 移除默认的日志处理器
logger.remove()
# 添加控制台输出（带颜色，适合开发调试）
logger.add(sys.stdout, level="INFO", colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
# 添加文件输出（自动按天轮转，保留7天，enqueue=True 保证异步安全）
logger.add("logs/app_{time:YYYY-MM-DD}.log", rotation="00:00", retention="7 days", level="INFO", encoding="utf-8", enqueue=True)

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


@app.post("/api/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    文件上传接口
    """
    try:
        save_file_name = await save_local_file(file)
        return UploadResponse(
            filename=save_file_name,
            message="上传成功",
            success=True
        )
    except HTTPException as http_e:
        return UploadResponse(
            filename=file.filename,
            message=http_e.detail,
            success=False
        )
    except Exception as e:
        return UploadResponse(
            filename=file.filename,
            message=str(e),
            success=False
        )
    

@app.post("/api/refresh-cdb/")
async def refresh_cdb_endpoint(req: RefreshRequest):
    """
    刷新向量数据库接口
    """
    logger.info(f"🚀 收到来自 {req.requester} 的刷新请求，开始执行增量计算...")
    return {"message": f"刷新完成，请求者：{req.requester}"}



if __name__ == '__main__':
    uvicorn.run(
        app="main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

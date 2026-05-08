# schemas.py
# 定义请求格式
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# 定义单条参考来源的格式
class SourceItem(BaseModel):
    text: str = Field(..., description="检索到的文档原文片段")
    metadata: Dict[str, Any] = Field(..., description="元数据")
    score: float = Field(..., description="检索相似度距离分数")


# 定义前端请求数据格式
class QueryRequest(BaseModel):
    question: str = Field(..., description="用户检索的问题")
    source: Optional[str] = Field(None, description="可选元数据过滤条件")

# 返回给前端的数格式
class QueryResponse(BaseModel):
    answer: str = Field(..., description="大模型生成的回答")
    sources: List[SourceItem] = Field(default_factory=list, description="支撑该回答的参考文档列表")


# 上传文件
# 文件上传模型
class UploadResponse(BaseModel):
    success: bool = Field(..., description="上传是否成功")
    filename: str = Field(..., description="保存的文件名")
    message: str = Field(..., description="处理结果信息")

# 刷新cdb数据库
class RefreshRequest(BaseModel):
    requester: str = Field(..., description="标识是谁发起请求")

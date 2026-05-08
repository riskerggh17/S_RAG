# file_service.py
import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from config import UPLOAD_DATA, FILE_MAX_SIZE, ALLOWED_FILE_TYPES


def validate_file_extension(filename: str) -> bool:
    """
    校验文件后缀是否在允许的白名单中
    """
    # 获取文件后缀并转为小写，防止大小写绕过
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_FILE_TYPES




async def save_local_file(file: UploadFile) -> str:
    """
    保存文件
    """
    # 1 校验后缀
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型: {file.filename}。只允许上传 {'、'.join(ALLOWED_FILE_TYPES)} 格式。"
        )
    # 2 生成安全文件名
    ext = os.path.splitext(file.filename)[1].lower()
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DATA / safe_filename
    # 3 分块异步保存
    try:
        total_size = 0
        async with aiofiles.open(file_path, 'wb') as out_file:
            while chunk := await file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > FILE_MAX_SIZE:
                    await out_file.close()
                    os.remove(file_path)
                    raise HTTPException(status_code=413, detail="文件过大")
                await out_file.write(chunk)
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文件上传失败：{str(e)}")
    return safe_filename






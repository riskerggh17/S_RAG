# ad_users.py
# 管理用户表
from datetime import datetime, timezone, timedelta
import databases
from sqlalchemy import create_engine, MetaData, Table, Column, text
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

# id生成
from ulid import ULID

import os
import sys
# 获取当前
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根
root_dir = os.path.dirname(os.path.dirname(current_dir))
# 添加根目录到sys.path
if root_dir not in sys.path:
    sys.path.append(root_dir)
# 数据库地址
from backend.app.config import SQLITE_DB
from backend.utils.encrypt_all import encrypt_password

# 数据库配置
database = databases.Database(SQLITE_DB)
engine = create_engine(SQLITE_DB.replace("sqlite+aiosqlite", "sqlite"))
# SQLAlchemy 的元数据和表定义（用于创建表结构）
metadata = MetaData()

# 定义表结构 (注意：这里不再继承 Base，而是直接定义 Table)
users_table = Table(
    "users",
    metadata,
    Column("user_id", String(50), primary_key=True, index=True),  # 用户唯一id
    Column("user_name", String(50), unique=True, nullable=False, index=True),  # 用户名
    Column('user_password', String(255), nullable=False),  # 加密后密码
    Column("user_email", String(100), unique=True, nullable=False, index=True),  # 邮箱
    Column("is_active", Boolean, default=True),  # 账号状态，自动
    Column("created_at", DateTime)  # 账号创建时间，自动
)

# 获取北京时间
def get_now_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))

ulid_gen = ULID()
# 生成user_id
def get_random_id():
    user_id = str(ulid_gen)
    return user_id

# --- 2. Pydantic 模型 (数据验证) ---
# 通用配置
class BaseUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# 创建用户时的验证模型
class UserCreate(BaseModel):
    user_name: str = Field(..., min_length=3, max_length=49, description="用户名，3-50字符")
    user_email: EmailStr = Field(..., description="用户邮箱")
    user_password: str = Field(..., min_length=6, description='密码至少六位')


# 输出，返回给前端的模型，隐藏信息
class UserResponse(BaseUser):
    user_id: str
    user_name: str
    user_email: str
    is_active: bool
    created_at: datetime

# 内部数据库模型，用于更新操作
class UserInDB(BaseUser):
    user_id: str
    user_password: str # 只有内部逻辑需要访问密码哈希
    is_active: bool
    created_at: datetime


class UserRepository:
    """
    用户数据表封装
    异步
    """
    # 创建用户
    async def user_create(user: UserCreate, password_hashed: str) -> str:
        """
        创建新用户
        """
        new_user_id = get_random_id()
        insert_values = {
            "user_id": new_user_id,
            "user_name": user.user_name,
            "user_password": password_hashed,
            "user_email": user.user_email,
            "is_active": True,
            "created_at": get_now_beijing_time()
        }
        query = users_table.insert().values(**insert_values)
        try:
            # 执行插入
            await database.execute(query)
            select_query = users_table.select().where(users_table.c.user_id == new_user_id)
            row = await database.fetch_one(select_query)
            if row:
                return UserInDB.model_validate(row)
            return None
        except Exception as e:
            return None

    # 更新用户信息
    async def user_update(user_id: str, **kwargs) -> bool:
        """
        更新用户信息
        """
        if not kwargs:
            return True
        query = users_table.update().where(users_table.c.user_id == user_id).values(**kwargs)
        try:
            # 执行更新
            await database.execute(query)
            return True
        except Exception as e:
            return False

    # 根据用户名查找用户信息
    async def get_user_by_name(user_name: str) -> Optional[UserInDB]:
        """
        根据用户名查找用户信息
        """
        try:
            # 构建查询语句
            query = users_table.select().where(users_table.c.user_name == user_name)
            # 执行查询
            row = await database.fetch_one(query)
            if row:
                return UserInDB.model_validate(row)
            return None
        except Exception as e:
            return None


async def main():
    pass


if __name__ == "__main__":
    print("开始测试")
    main()

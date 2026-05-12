# database.py
# 初始化向量数据库客户端
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
# 把根目录加入系统路径
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
import chromadb

from app.config import CHROMADB_PATH

# client = chromadb.PersistentClient(path=str(CHROMADB_PATH))
# collection = client.get_or_create_collection(name="raw_md")

# 向量数据库概览



# sqlite数据库
from config import SQLITE_DB
import databases
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Optional
from pydantic import BaseModel

# --- 1. 配置数据库连接 ---
DATABASE_URL = SQLITE_DB

# databases.Database 用于执行异步查询
database = databases.Database(DATABASE_URL)
engine = create_engine(DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"))
# SQLAlchemy 的元数据和表定义（用于创建表结构）
metadata = MetaData()

# 定义表结构 (注意：这里不再继承 Base，而是直接定义 Table)
users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("email", String, unique=True),
)

# --- 2. Pydantic 模型 (数据验证) ---
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        orm_mode = True

# --- 3. 数据库封装类 ---
class UserRepository:
    """
    用户数据库操作仓库类
    所有方法都是异步的 (async def)
    """

    async def get_all(self) -> List[UserResponse]:
        """获取所有用户"""
        # database.fetch_all 是异步操作
        query = users_table.select()
        rows = await database.fetch_all(query)
        # 将数据库行转换为 Pydantic 模型列表
        return [UserResponse(id=row['id'], name=row['name'], email=row['email']) for row in rows]

    async def get_by_id(self, user_id: int) -> Optional[UserResponse]:
        """根据 ID 获取单个用户"""
        query = users_table.select().where(users_table.c.id == user_id)
        row = await database.fetch_one(query)
        if row:
            return UserResponse(id=row['id'], name=row['name'], email=row['email'])
        return None

    async def create(self, user: UserCreate) -> UserResponse:
        """创建新用户"""
        # database.execute 是异步操作，返回新插入的 ID
        query = users_table.insert().values(name=user.name, email=user.email)
        user_id = await database.execute(query)
        
        # 返回创建好的用户对象
        return UserResponse(id=user_id, name=user.name, email=user.email)

    async def delete(self, user_id: int) -> bool:
        """删除用户"""
        query = users_table.delete().where(users_table.c.id == user_id)
        # execute 返回受影响的行数
        rows_deleted = await database.execute(query)
        return rows_deleted > 0


import asyncio

async def main():
    print("🚀 开始测试数据库连接和操作...")
    
    # 1. 必须显式连接数据库
    await database.connect()
    print("✅ 数据库已连接")

    try:
        # 创建表
        metadata.create_all(engine)
        # 实例化仓库类
        repo = UserRepository()

        # --- 测试 1: 创建用户 ---
        print("\n--- 测试创建用户 ---")
        new_user_data = UserCreate(name="测试用户", email="test@example.com")
        created_user = await repo.create(new_user_data)
        print(f"✨ 创建成功: ID={created_user.id}, 姓名={created_user.name}")

        # --- 测试 2: 获取所有用户 ---
        print("\n--- 测试获取所有用户 ---")
        all_users = await repo.get_all()
        for u in all_users:
            print(f"   👤 {u.id}: {u.name} ({u.email})")

        # --- 测试 3: 根据ID获取用户 ---
        if all_users:
            print(f"\n--- 测试获取ID为 {all_users[0].id} 的用户 ---")
            user = await repo.get_by_id(all_users[0].id)
            if user:
                print(f"   👤 找到用户: {user.name}")
        
        # --- 测试 4: 删除用户 (可选) ---
        # print("\n--- 测试删除用户 ---")
        # is_deleted = await repo.delete(created_user.id)
        # print(f"   🗑️ 删除结果: {is_deleted}")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        # 无论成功失败，最后都要断开连接
        await database.disconnect()
        print("\n🛑 数据库连接已关闭")

# 使用 asyncio.run() 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())




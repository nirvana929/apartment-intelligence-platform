"""
SQLAlchemy 异步数据库引擎 —— 管理数据库连接。

这个文件的作用：
  创建和管理与 MySQL 数据库的连接。
  其他模块需要操作数据库时，从这里获取"会话"（Session）。

核心概念 —— 为什么用异步（async）？
  同步版本：代码执行到数据库查询时，整个程序会"卡住"等待结果返回。
  异步版本：代码执行到数据库查询时，程序可以去做别的事（比如处理其他请求），
            等查询结果返回了再继续处理。

  对于 Web 服务来说，异步意味着：
    用户 A 的查询在等数据库时，程序可以同时处理用户 B 的请求。
    同样的服务器能同时处理更多用户。

核心概念 —— 连接池（Connection Pool）：
  每次查数据库都要"建连接 → 执行SQL → 关闭连接"，太慢了。
  连接池的做法：提前创建好一批连接放着，需要时直接拿来用，用完还回去。

  类比理解：
    没有连接池 = 每次去银行都要取号排队
    有连接池   = 有 VIP 通道，直接去柜台

  pool_size=5 表示池子里保持 5 个连接。
  max_overflow=5 表示忙的时候最多再临时多开 5 个（总共 10 个）。

实际使用场景：
  # 方式 1：FastAPI 依赖注入（推荐）
  @app.get("/api/data")
  async def get_data(session: AsyncSession = Depends(get_session)):
      result = await session.execute(text("SELECT * FROM apartment_info"))

  # 方式 2：直接用 async_session_factory（在 executor.py 里用）
  async with async_session_factory() as session:
      result = await session.execute(text("SELECT 1"))
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from aptinsight.core.config import settings


# [框架] SQLAlchemy 的三层结构：
# Engine（引擎）→ SessionFactory（会话工厂）→ Session（会话）
# Engine 管连接池，SessionFactory 创建 Session，Session 执行 SQL

# [框架] create_async_engine 创建异步引擎
# "async" 意味着所有数据库操作都是 await 的，不会阻塞其他请求
engine = create_async_engine(
    settings.mysql_url,
    # [框架] 连接池参数：
    pool_size=5,        # 常驻 5 个连接
    max_overflow=5,     # 高峰时最多再开 5 个（总共 10 个）
    pool_recycle=3600,  # 1 小时回收旧连接，防止 MySQL 超时断开
    pool_pre_ping=True, # 取连接时先 ping，避免用到已断开的连接
    echo=False,
)


# [框架] async_sessionmaker 是会话工厂
# 调用 async_session_factory() 就能创建一个新的 AsyncSession
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # [框架] commit 后不重新查库，只读场景更高效
)


# ============================================================================
# 获取会话的依赖函数
# ============================================================================

# [框架] FastAPI 依赖注入 + 异步生成器的配合：
# FastAPI 看到 Depends(get_session) 会自动：
#   1. 进入 with 块 → 创建 session → 注入到函数参数
#   2. 函数执行完 → 离开 with 块 → 自动关闭 session
# 即使函数抛异常，session 也会被正确关闭
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

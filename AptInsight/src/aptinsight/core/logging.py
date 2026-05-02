"""
JSON 结构化日志 —— 让日志机器可读。

这个文件的作用：
  把 Python 的日志输出格式改成 JSON，方便后续用 ELK、Grafana 等工具收集和分析。

为什么不用默认的文本日志？
  文本日志：`2024-01-01 INFO: 用户查询了预约数据`
  JSON 日志：`{"level":"INFO","logger":"agent","message":"用户查询了预约数据","trace_id":"abc123"}`

  JSON 格式的好处：
    1. 机器可以直接解析，不需要正则表达式
    2. 可以按字段过滤（比如"只看 ERROR 级别"）
    3. 可以附带结构化数据（trace_id、session_id、SQL 语句等）

核心概念 —— ContextVar（上下文变量）：
  ContextVar 是 Python 提供的"协程安全"的全局变量。
  普通的全局变量在多个请求并发时会串数据（请求 A 的 trace_id 混入请求 B）。
  ContextVar 保证每个协程（每个请求）有自己独立的值，互不干扰。

  类比理解：
    全局变量 = 办公室里的公共白板，谁都能改，容易乱
    ContextVar = 每人一张便签纸，只写自己的内容

实际使用场景：
  # 1. 应用启动时初始化日志
  setup_logging("INFO")

  # 2. 请求进来时设置 trace_id（在中间件里做）
  set_trace_id("req-abc-123")

  # 3. 代码里打日志
  logger = get_logger("agent")
  logger.info("开始处理用户问题", extra={"question": "本月预约量"})

  # 4. 输出的 JSON 自动包含 trace_id：
  # {"level":"INFO","logger":"agent","message":"开始处理用户问题","trace_id":"req-abc-123","session_id":""}
"""

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any


# ============================================================================
# ContextVar 定义
# ============================================================================
# [框架] ContextVar 是 Python 3.7+ 的协程安全变量
# 普通全局变量在多个请求并发时会串数据（请求A的trace_id混入请求B）
# ContextVar 保证每个协程有自己独立的值，类似 ThreadLocal 但用于 async

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_session_id: ContextVar[str] = ContextVar("session_id", default="")


# ============================================================================
# 读写 ContextVar 的便捷函数
# ============================================================================

def set_trace_id(trace_id: str) -> None:
    """
    设置当前协程的 trace_id。

    通常在 FastAPI 中间件里调用：每个请求进来时生成一个 UUID 作为 trace_id。
    """
    _trace_id.set(trace_id)


def get_trace_id() -> str:
    """获取当前协程的 trace_id。"""
    return _trace_id.get()


def set_session_id(session_id: str) -> None:
    """设置当前协程的 session_id。"""
    _session_id.set(session_id)


def get_session_id() -> str:
    """获取当前协程的 session_id。"""
    return _session_id.get()


# ============================================================================
# JSON 格式化器
# ============================================================================

# [框架] Python logging 模块的架构：
# Logger（记录日志）→ Handler（输出到哪）→ Formatter（格式化成什么样子）
# 这里自定义 Formatter，把文本日志变成 JSON
class JsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        """
        把一条日志记录格式化成 JSON 字符串。

        参数 record 是 Python logging 模块自动创建的，包含：
          - record.levelname: 日志级别（"INFO"、"ERROR" 等）
          - record.name: 日志器名称（通常用模块名，如 "aptinsight.db.executor"）
          - record.getMessage(): 日志消息文本
          - record.exc_info: 异常信息（如果有）

        返回值示例：
          {"level":"INFO","logger":"db","message":"查询完成","trace_id":"abc","session_id":""}
        """
        # 构建日志字典
        log_data: dict[str, Any] = {
            "level": record.levelname,         # 日志级别
            "logger": record.name,             # 日志器名称
            "message": record.getMessage(),    # 日志消息
            "trace_id": get_trace_id(),        # 从 ContextVar 获取，每个请求不同
            "session_id": get_session_id(),    # 从 ContextVar 获取
        }

        # 如果有异常信息（比如 logger.error("出错了", exc_info=True)），也加进去
        # formatException 会把异常转成多行字符串，如 "Traceback ...\nValueError: xxx"
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = self.formatException(record.exc_info)

        # ensure_ascii=False 让中文直接显示，不转义成 中文
        return json.dumps(log_data, ensure_ascii=False)


# ============================================================================
# 初始化函数
# ============================================================================

# [设计] 在应用启动时调用一次，把全局日志器换成 JSON 格式
# 接管 uvicorn 的日志器，让整个应用的日志格式统一
def setup_logging(level: str = "INFO") -> None:
    """
    初始化全局日志配置。

    做了三件事：
      1. 创建一个输出到控制台（stdout）的 handler
      2. 给 handler 挂上我们的 JsonFormatter
      3. 把 uvicorn 的日志也接管过来，统一用 JSON 格式

    为什么接管 uvicorn 的日志：
      uvicorn（ASGI 服务器）有自己的日志 handler，输出格式和我们不一样。
      如果不接管，控制台里会混杂两种格式的日志，很乱。
      接管后，所有日志都是统一的 JSON 格式。

    在 main.py 的 create_app() 里调用：setup_logging(settings.log_level)
    """
    # 创建 handler：输出到标准输出（stdout）
    # 为什么用 stdout 而不是 stderr：大多数日志收集器（如 Docker）默认收集 stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # 获取根日志器，清空默认 handler，换成我们的
    root = logging.getLogger()
    root.handlers.clear()       # 移除 Python 默认的 handler（文本格式）
    root.addHandler(handler)    # 加上我们的 JSON handler
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # getattr 的作用：把字符串 "INFO" 转成 logging.INFO 常量
    # 如果 level 是无效值，fallback 到 INFO

    # 接管 uvicorn 的日志器，让它们也用我们的 handler
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """
    获取一个命名日志器。

    用法：
      logger = get_logger(__name__)   # 用模块名作为日志器名
      logger.info("查询完成")

    为什么不用 logging.getLogger(__name__) 直接调用：
      其实可以，这个函数只是个快捷方式。
      好处是如果以后想换日志库（比如换成 loguru），只改这一个地方就行。
    """
    return logging.getLogger(name)

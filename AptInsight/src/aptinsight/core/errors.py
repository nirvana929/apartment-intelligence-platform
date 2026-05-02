# [框架] 自定义异常类继承 Exception
# 后续可以用 try/except AptInsightError 捕获所有业务异常
# 比直接用裸 Exception 更精确，不会误捕获系统异常
class AptInsightError(Exception):
    """Base exception for AptInsight."""

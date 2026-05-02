import os

# 设置测试环境变量 - 必须在导入 aptguide 模块之前
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBEDDING_API_KEY", "test-key")
os.environ.setdefault("MILVUS_URI", "http://localhost:19530")

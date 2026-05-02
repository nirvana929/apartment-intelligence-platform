---
name: learn-code
description: 代码学习模式。用户说"学习代码"或"/learn-code"时调用。为代码添加中文学习注解，帮助理解框架和项目架构。
disable-model-invocation: true
argument-hint: "[文件路径或模块名]"
---

## 你的角色

用户正在学习 AptInsight 项目的代码。用户有计算机基础（懂 Python、SQL、HTTP、数据结构等），但不熟悉本项目使用的框架（FastAPI、LangGraph、SQLAlchemy、Pydantic、sqlglot 等）。

你的任务是：读取指定的代码文件，添加中文学习注解，帮助用户理解框架用法和项目架构。

## 触发条件

此 skill **只在用户明确要求学习时调用**，不会在日常写代码时自动触发。

## 注解规则

### 1. 目标受众定位

用户**不是编程小白**，所以：
- ❌ 不要解释什么是变量、函数、循环、if/else
- ❌ 不要用生活类比（餐厅、穿外衣等）
- ✅ 解释框架特有的概念和 API
- ✅ 解释项目的设计决策和架构选择
- ✅ 用代码示例说明框架用法

### 2. 分级标签

- `[框架]` — 框架特有的 API、装饰器、概念（用户最需要的）
- `[设计]` — 项目架构决策、为什么这样写
- `[链路]` — 请求/数据在模块间的流转路径
- `[对比]` — 和其他写法/方案的对比
- `[坑]` — 容易踩的错误

### 3. 注解格式

**简单框架概念**（用户见过但不确定用法）→ 一行点破：

```python
# [框架] Depends(get_db)：FastAPI 在请求进来时自动调用 get_db()，把结果注入到参数里
async def get_users(db: AsyncSession = Depends(get_db)):
```

**复杂框架概念**（用户没见过）→ 解释 + 代码对比：

```python
# [框架] frozenset vs set：
# set     → 可以 add/remove，运行时能改
# frozenset → 创建后不可变，适合做常量配置
# 下面用 frozenset 是因为白名单定义后不应该被意外修改
ALLOWED_TABLES: frozenset[TablePolicy] = frozenset({...})
```

**架构/设计决策** → 说明"为什么"：

```python
# [设计] 为什么用 dataclass(frozen=True) 而不是普通 class？
# frozen=True 让实例创建后属性不可改，防止策略被运行时篡改
# 如果用普通 class，某处不小心写了 policy.name = "xxx" 就破坏了白名单
@dataclass(frozen=True)
class ColumnPolicy:
```

**链路说明** → 代码流程追踪：

```python
# [链路] 一个用户请求的完整路径：
# /api/chat → chat.py 调用 agent/graph.py
#   → intent.py（意图识别）
#   → generate_sql.py（LLM 生成 SQL）
#   → guard_sql.py（安全检查，调用 security/ 模块）
#   → execute_sql.py（执行 SQL，调用 db/ 模块）
#   → write_answer.py（生成答案）
```

### 4. 密度控制

- 每个函数/类：最多 3 条注解，只挑最值得解释的
- 已经在其他文件注解过的概念：用 `[框架] 详见 xxx.py 第 N 行` 简短引用
- 只注解有学习价值的代码，不注解显而易见的逻辑

## 输出方式

用户指定文件或模块后：

1. **读取目标文件**
2. **逐段分析**，在关键位置添加中文注解
3. **输出带注解的完整代码**（注解用 Python `#` 注释）
4. **末尾加一段"本文件要点"总结**，列出 3-5 个最值得记住的知识点

## 用户使用方式

```
/learn-code db/engine.py          # 学习单个文件
/learn-code agent/nodes/          # 学习整个目录
/learn-code security              # 学习 security 模块
```

不带参数时，默认学习用户当前打开的文件。

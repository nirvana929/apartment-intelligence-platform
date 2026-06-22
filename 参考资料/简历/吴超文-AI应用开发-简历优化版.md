# 吴超文

+86 15922799340 ｜ 1751679308@qq.com  
求职意向：AI 应用开发 / Java 后端开发  
现居：广州

## 教育经历

**中山大学 - 计算机科学与技术 - 硕士** ｜ 2024.09 - 至今  
- 研究方向：嵌入式实时系统 / 操作系统 / 任务调度
- 主修课程：操作系统、计算机网络、数据库原理、数据结构与算法、软件工程、编译原理、Java 程序设计

**重庆邮电大学 - 计算机科学与技术 - 本科** ｜ 2020.09 - 2024.06  
- GPA：3.57/4.0（专业前 2%）
- 学业一等奖学金

## 项目经历

### AptGuide 3.0 - 租客端智能找房助手（AI Agent 项目 ｜ 独立开发）

- 技术栈：Python、FastAPI、RAG、Milvus、Redis、MySQL、SQLAlchemy、Vue3、Playwright
- 面向租客找房、规则咨询、预约看房和租约查询等场景，构建智能找房助手；通过租赁业务后端获取房源、预约、租约等业务事实，避免 AI 直接操作核心业务数据。
- 设计 LLM-first 结构化理解方案，将用户输入解析为任务类型、硬性条件、软偏好、检索查询和风险等级；低置信度、字段矛盾或解析失败时进入澄清流程，避免关键词路由误判。
- 设计 7 类业务流程，覆盖找房、知识库问答、预约、租约、记忆、人工转接和澄清；预约创建/取消、偏好写入等写操作均通过待确认动作二次确认后执行。
- 实现 RAG 检索与推荐链路，支持多查询向量召回、lease 房源校验、五维加权排序、知识库重排和置信度门控；阶段性验证覆盖 207 项核心单测、Live RAG 集成和前端 E2E。

### AptInsight - 公寓运营智能分析助手（AI 后端项目 ｜ 独立开发）

- 技术栈：Python、FastAPI、LangGraph、Text-to-SQL、SQLAlchemy、asyncmy、sqlglot、Pydantic、Qwen
- 面向公寓后台运营人员的临时数据分析需求，支持用自然语言查询预约、租约、房源、租金、浏览热度等业务数据，并返回 SQL、表格、图表和运营总结。
- 使用 LangGraph 编排 Text-to-SQL 链路，通过 AgentState 记录意图、SQL、Guard 结果、查询结果、图表和答案等中间状态，配合 trace_id 日志定位各节点问题。
- 基于 sqlglot 实现 AST 级 SQL Guard，通过 `parse/parse_one` 校验单条 SELECT、表/字段白名单和敏感字段，拦截多语句、系统库、危险操作和隐私字段访问。
- 构建 Agent Eval Harness，覆盖 40 个业务分析、安全测试和边界拒答场景；最终评测通过率 87.5%，安全用例通过率 100%，预约量、有效租约、合同月租金等核心指标口径通过率 100%。

### SmartLease - 租赁业务管理平台（Spring Boot 后端项目 ｜ 独立开发）

- 技术栈：Spring Boot、MyBatis-Plus、MySQL、Redis、JWT、MinIO、Nginx
- 面向公寓运营场景，设计公寓、房间、预约、租约、用户等核心业务模型，提供后台管理端与租客端接口，支撑房源管理、预约看房、签约、续约、退租等流程。
- 负责核心业务建模与落库设计，覆盖公寓-房间-付款方式-租期-标签-设施-图片等关联关系，支持多条件分页查询、详情聚合和发布状态管理。
- 设计预约与租约状态流转并在接口层做状态约束，使用 Redis 管理验证码、登录态和热点房源缓存，集成 MinIO、JWT、Nginx 并完成 Linux 环境部署。
- 补充 AI 内部工具接口，支持房源搜索/同步、预约创建、我的预约和我的租约查询，使租赁系统作为 AptGuide 的业务事实源。

## 专业技能

- 编程语言与基础：Java、Python、数据结构与算法、操作系统、计算机网络、数据库原理
- AI 应用开发：LLM 应用、RAG、Embedding、AI Agent、Text-to-SQL、Prompt 优化、Agent Eval
- 后端技术：Spring Boot、FastAPI、MyBatis-Plus、RESTful API、JWT、SQLAlchemy、Pydantic
- 数据库与工程工具：MySQL、Redis、Milvus、MinIO、Nginx、Git、Linux、Playwright、Ruff

## 自我评价

- 具备 AI 应用开发与后端工程落地能力，能够完成从业务建模、Agent 流程设计、接口集成、状态持久化到测试评测的闭环；持续沉淀 LLM、RAG、Agent 与后端工程实践。

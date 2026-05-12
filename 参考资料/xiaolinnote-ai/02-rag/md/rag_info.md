<!-- source: https://xiaolinnote.com/ai/rag/rag_info.html -->

# RAG 面试题介绍

大家好，我是小林。

RAG 现在基本上是 AI 应用里的标配了，不管你做的是智能客服、知识问答还是企业内部搜索，底下大概率都有一套 RAG 系统在跑。所以只要你面的是 AI 工程方向的岗位，RAG 几乎是必问的，而且面试官问起来特别喜欢一路往深了追，从「RAG 是什么」一直追到「你线上遇到过什么坑」，很多同学前面几个问题答得还行，越往后越接不住。

所以我从网上各种真实面经里收集了 20 道 RAG 方向的高频面试题，都是真实面试里被问过的，帮大家把 RAG 从原理到工程落地这条线完整地过一遍。涵盖 RAG 原理、文档切割、Embedding 选型、向量数据库、检索优化、Query 改写、多路召回、幻觉规避等面试题。

每道题的写法跟 Agent 专题一样，开头先来一段「面试翻车现场」，模拟真实对话让你看看这道题答不好会怎么被怼，然后我再把知识点从根上讲透。目的不是让你背一套标准答案，而是让你真正理解了，不管面试官怎么换着花样问，你都能自己推出来。

## 题目目录

下面简单说一下这 20 道题大概覆盖了哪些内容，你可以挑自己不熟的先看。

前三道聊的是**基础概念**，RAG 到底是什么、完整的工作流程长什么样、它主要解决了大模型的哪些问题、跟微调比各自适合什么场景，这几道是面试开场必问的，得答出层次来，不能只说一句「RAG 就是检索增强生成」就完了。

第 4 到第 9 题聊的是**索引构建**，也就是 RAG 系统搭起来之前你必须搞定的那些事：文档怎么切、切多大合适、语义被切断了怎么办、Embedding 是什么怎么选、有哪些 Embedding 算法、向量数据库怎么选型怎么用。这块的问题看着简单，但面试官一深挖就会发现你有没有真正动手做过，每道题背后都有坑。

第 10 到第 16 题聊的是**检索优化**，这是最容易在面试里拉开差距的部分。大部分人能说出「用向量检索」，但再往下问 Query Rewrite 是什么、为什么要做、多路召回具体怎么设计、有哪些更高级的 RAG 范式（比如 Self-RAG、Corrective RAG）、图数据库什么场景下能派上用场，很多人就答不上来了。偏偏这些恰恰是面试官最爱深挖的地方，因为这些才是区分「用过 RAG」和「真正优化过 RAG」的分水岭。

最后第 17 到第 20 题聊的是**生产落地**，幻觉怎么规避、效果怎么量化评估、知识库怎么做动态更新，还有一道开放题「你觉得 RAG 落地最难的地方在哪」。最后这道题没有标准答案，但能答好的人，面试官基本就认可你是真正在线上跑过 RAG 系统的，不是只停留在 demo 阶段。

- 1. 什么是 RAG？详细描述一个完整 RAG 系统的详细工作流程？(https://xiaolinnote.com/ai/rag/1_whatisrag.html)
- 2. 大模型的 RAG 主要用来解决什么问题？(https://xiaolinnote.com/ai/rag/2_rag_problems.html)
- 3. 相比直接微调 LLM，RAG 解决了什么问题？微调和 RAG 各自的优劣势是什么？(https://xiaolinnote.com/ai/rag/3_rag_vs_finetune.html)
- 4. RAG 中的文档是怎么存的？粒度是多大？详细说说文档切割（Chunking）策略？(https://xiaolinnote.com/ai/rag/4_chunking.html)
- 5. 怎么规避语义被切割掉的问题？(https://xiaolinnote.com/ai/rag/5_semantic_cuts.html)
- 6. 在 RAG 中 Embedding 究竟是什么？如何选择和评估一个 Embedding 模型？(https://xiaolinnote.com/ai/rag/6_embedding.html)
- 7. Embedding 有哪几种算法你了解过吗？(https://xiaolinnote.com/ai/rag/7_embedding_algos.html)
- 8. 什么是向量数据库？有没有做过向量数据库的对比选型？(https://xiaolinnote.com/ai/rag/8_vectordb.html)
- 9. 讲讲你用的向量数据库？数据量级是多大？性能如何？遇到过性能瓶颈吗？(https://xiaolinnote.com/ai/rag/9_vectordb_practice.html)
- 10. 你使用 RAG 给大模型一个输入，系统是怎样的工作流程？(https://xiaolinnote.com/ai/rag/10_online_workflow.html)
- 11. 请你介绍一下向量检索和关键词检索的区别？(https://xiaolinnote.com/ai/rag/11_retrieval_types.html)
- 12. 如何润色用户的 Query（Query Rewrite）？目的是什么？(https://xiaolinnote.com/ai/rag/12_query_rewrite.html)
- 13. 什么是多路召回？具体怎么做？(https://xiaolinnote.com/ai/rag/13_multi_retrieval.html)
- 14. RAG 检索优化策略有哪些？(https://xiaolinnote.com/ai/rag/14_retrieval_opt.html)
- 15. 了解哪些更复杂的 RAG 范式？(https://xiaolinnote.com/ai/rag/15_advanced_paradigms.html)
- 16. 在什么场景下，你会选择使用图数据库来增强传统的向量检索？(https://xiaolinnote.com/ai/rag/16_graph_db.html)
- 17. 如何规避 RAG 系统中大模型的幻觉？(https://xiaolinnote.com/ai/rag/17_hallucination.html)
- 18. 怎么量化你的 RAG 效果？(https://xiaolinnote.com/ai/rag/18_evaluation.html)
- 19. RAG 知识库如何实现动态与持续更新？(https://xiaolinnote.com/ai/rag/19_dynamic_update.html)
- 20. 在实际落地中，你觉得 RAG 最难的地方是哪里？(https://xiaolinnote.com/ai/rag/20_hardest_parts.html)

对了，AI RAG的面试题会在「**公众号@小林面试笔记题**」持续更新，林友们赶紧关注起来，别错过最新干货哦！

![](../assets/fe39bd49c2a0.png)

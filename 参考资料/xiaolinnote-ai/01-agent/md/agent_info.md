<!-- source: https://xiaolinnote.com/ai/agent/agent_info.html -->

# Agent 面试题介绍

大家好，我是小林。

Agent 这个方向现在有多火不用我多说了吧，基本上只要面的是 AI 工程相关的岗位，Agent 就是绕不过去的必考题。但说实话，我看了不少同学的面经分享，发现很多人答 Agent 的题目都有一个通病：听起来好像说得都对，但面试官一追问就露馅了，因为只记住了概念，没有真的搞懂背后的原理和工程取舍。

所以我专门花时间从网上各种真实面经里收集了 16 道 Agent 方向的高频面试题，都是真实面试里问过的，帮大家把 Agent 从概念到落地这条线彻底捋清楚。涵盖 Agent 概念与架构、Workflow 与 Agent 区别、ReAct/Plan-and-Execute/Reflection 设计范式、任务拆分、记忆机制、Multi-Agent 协作等面试题。

每道题我都用「面试翻车现场」的方式来写，开头先模拟一段真实的面试对话，让你感受一下这道题答得不好会怎么被怼，踩了什么雷自己可能还不知道，然后我再一步步把知识点从根上讲透。不是让你背答案哈，而是让你真的理解了，面试官换个角度问你也不慌。

## 题目目录

下面简单说一下这 16 道题大概聊了些什么，你可以挑自己薄弱的地方先看。

前面三道聊的是**基础概念**，Agent 到底是什么、跟直接调 LLM 有什么本质区别、核心组件有哪些、Workflow 和 Agent 和 Tools 三者怎么分清楚，这几个概念是后面所有问题的地基，建议先过一遍。

第 4 到第 7 题聊的是**设计范式**，这块是面试高频考点。ReAct、Plan-and-Execute、Reflection 这三种范式到底有什么区别，各自适合什么场景，复杂任务该怎么拆分，这几道题面试官特别喜欢追问，很多人就是在这里答得半对不对被刷掉的。

第 8、9、12 到 15 题聊的是**工程实践**，记忆模块怎么设计、长短期记忆怎么存、记忆太长了怎么压缩、怎么给 LLM 加上规划能力、反思机制具体怎么跑，还有一道「为什么有时候宁愿手搓 Agent 也不用现成框架」，这些都是真正做过项目才会碰到的问题，能聊明白的话面试官对你的印象会完全不一样。

最后第 10、11、16 题聊的是**多 Agent**，什么时候该用多 Agent、单 Agent 和多 Agent 怎么选、多个 Agent 之间怎么协作和切换，这块属于进阶内容，如果你做过稍微复杂一点的系统，这几道题答好了是很大的加分项。

- 1. 什么是 Agent？与大模型有什么本质不同？(https://xiaolinnote.com/ai/agent/1_whatisagent.html)
- 2. Agent 的基本架构由哪些核心组件构成？(https://xiaolinnote.com/ai/agent/2_components.html)
- 3. Workflow，Agent，Tools 这三个的概念和区别介绍一下？(https://xiaolinnote.com/ai/agent/3_workflow_tools.html)
- 4. 了解哪些其他的 Agent 设计范式？Agent 和 Workflow 的区别是什么？(https://xiaolinnote.com/ai/agent/4_patterns.html)
- 5. Agent 推理模式有哪些？ReAct 是啥？具体是怎么实现的？(https://xiaolinnote.com/ai/agent/5_react.html)
- 6. ReAct、Plan-and-Execute、Reflection 三种范式有什么核心区别？实际项目中该如何选型？(https://xiaolinnote.com/ai/agent/6_three_patterns.html)
- 7. 复杂任务怎么做的任务拆分？为什么要拆分？效果如何提升？(https://xiaolinnote.com/ai/agent/7_tasksplit.html)
- 8. 请你介绍一下 AI Agent 的记忆机制，并说明在实际开发中应该如何设计记忆模块？(https://xiaolinnote.com/ai/agent/8_memory.html)
- 9. Agent 的长短期记忆系统怎么做的？记忆是怎么存的？粒度是多少？怎么用的？(https://xiaolinnote.com/ai/agent/9_memory_storage.html)
- 10. 什么是 Multi-Agent？(https://xiaolinnote.com/ai/agent/10_multiagent.html)
- 11. 说说 Single-Agent 和 Multi-Agent 的设计方案？(https://xiaolinnote.com/ai/agent/11_single_multi.html)
- 12. Agent 记忆压缩通常有哪些方法？(https://xiaolinnote.com/ai/agent/12_memcompress.html)
- 13. 在工程实践中，为什么有时候选择「手搓」Agent，而不是直接用成熟框架？(https://xiaolinnote.com/ai/agent/13_handcode.html)
- 14. 如何赋予 LLM 规划能力？(https://xiaolinnote.com/ai/agent/14_planning.html)
- 15. 讲讲 Agent 的反思机制？为什么要用反思？具体怎么实现？(https://xiaolinnote.com/ai/agent/15_reflection.html)
- 16. 如何设计多 Agent 的协作与动态切换机制？(https://xiaolinnote.com/ai/agent/16_collab.html)

对了，AI Agent的面试题会在「**公众号@小林面试笔记题**」持续更新，林友们赶紧关注起来，别错过最新干货哦！

![](../assets/fe39bd49c2a0.png)

# AI Agent 智能体模拟子系统

## 概述

本模块为论坛系统提供 **AI Agent 舆情模拟能力**。通过 MBTI 人格矩阵驱动的智能体，模拟真实用户在论坛中的发帖、评论、点赞、关注等行为，用于舆情推演与模拟。

核心思路：**不是面向真实用户，而是由 AI Agent 模拟不同人格的用户，按真实人口比例抽样，生成与人格一致的论坛内容。**

## 架构总览

```
┌─────────────────────────────────────────────────────┐
│                   Manager 编排层                      │
│            AgentOrchestrator (总调度入口)              │
└────┬──────────┬──────────┬──────────┬────────────────┘
     │          │          │          │
┌────▼───┐ ┌───▼────┐ ┌──▼────┐ ┌──▼─────────────────┐
│Personas│ │Population││Scheduler││     LLM            │
│人格定义 │ │人群采样  ││行为调度 ││  内容生成引擎       │
│·16型矩阵│ │·比例抽样 ││·计划器 ││  ·Client           │
│·写作风格│ │·批量生成 ││·时间线 ││  ·Templates        │
│·社交参数│ │         ││       ││                    │
└────┬───┘ └───┬────┘ └──┬────┘ └──┬─────────────────┘
     │          │          │          │
┌────▼──────────▼──────────▼──────────▼─────────────────┐
│                   Actions 行为执行层                    │
│  PostAction · CommentAction · LikeAction · FollowAction │
│        (调用现有 Service 层，复用业务逻辑)              │
└──────────────────────┬─────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────┐
│               现有 Forum 后端 Service 层                 │
│     UserSvc · PostSvc · CommentSvc · LikeSvc · FollowSvc │
└─────────────────────────────────────────────────────────┘
```

## 模块说明

### personas/ — 人格定义层

定义 16 种 MBTI 人格的完整画像，包括：

- **matrix.py** — 16 型人格矩阵，四维得分（E/I, N/S, F/T, P/J），认知功能栈
- **traits.py** — 各人格的写作风格、话题兴趣权重、社交行为参数
- **prompts.py** — 各人格对应的 LLM System Prompt 模板，用于引导 LLM 生成符合人格的内容

### population/ — 人群采样层

- **sampler.py** — 按真实世界 MBTI 人口比例进行确定性采样
- **generator.py** — 批量创建 Agent User（调用 UserSvc 注册 + 写入 AgentProfile）

### scheduler/ — 行为调度层

- **planner.py** — 给定选题，为每个 Agent 生成行为序列（何时发帖、评论谁等）
- **timeline.py** — 时间线引擎，控制行为的时间分布（早高峰/晚高峰/周末模式）

### llm/ — LLM 集成层

- **client.py** — LLM API 客户端（兼容 OpenAI API 格式）
- **templates.py** — 提示词模板仓库，根据 persona + topic + action type 拼接请求

### actions/ — 行为执行层

- **base.py** — 动作抽象基类
- **poster.py** — 发帖执行器，调 PostSvc
- **commenter.py** — 评论执行器，调 CommentSvc
- **liker.py** — 点赞执行器，调 LikeSvc
- **follower.py** — 关注执行器，调 FollowSvc

### models/ — 数据模型

- **profile.py** — Agent 档案模型（MBTI 类型、背景故事、账号引用）
- **mbti.py** — MBTI 类型枚举、维度定义、人口分布数据
- **action.py** — 行为记录模型
- **topic.py** — 选题模型

### manager.py — 编排入口

AgentOrchestrator 总调度器，编排全流程：选题 → 采样 → 计划 → 生成 → 执行

### config.py — 系统配置

LLM 模型参数、API 地址、速率限制、随机种子等

## MBTI 人格矩阵

基于 Jung 心理学理论的四维八极人格分类：

| 维度                  | 两极                                            | 含义        |
| --------------------- | ----------------------------------------------- | ----------- |
| 能量指向 (Energy)     | **E**xtraversion / **I**ntroversion | 外向 / 内向 |
| 信息获取 (Perception) | **S**ensing / I**N**tuition         | 实感 / 直觉 |
| 决策方式 (Judgment)   | **T**hinking / **F**eeling          | 理性 / 情感 |
| 生活态度 (Lifestyle)  | **J**udging / **P**erceiving        | 计划 / 灵活 |

16 种人格类型各有其认知功能栈、写作风格、话题偏好和社交行为模式，确保模拟出的内容具有多样性和真实性。

## 人口比例抽样

Agent 创建时按照以下真实人口比例进行采样：

| 类型 | 比例  | 类型 | 比例  |
| ---- | ----- | ---- | ----- |
| ISTJ | 13.8% | ESTJ | 8.7%  |
| ISFJ | 13.8% | ESFJ | 12.3% |
| INFJ | 1.5%  | ENFJ | 2.5%  |
| INTJ | 2.1%  | ENTJ | 1.8%  |
| ISTP | 5.4%  | ESTP | 4.3%  |
| ISFP | 8.8%  | ESFP | 8.5%  |
| INFP | 4.4%  | ENFP | 8.1%  |
| INTP | 3.3%  | ENTP | 3.2%  |

## 选题驱动流程

1. 运营/管理员创建 **选题 (Topic)**
2. Sampler 根据 MBTI 比例从 Agent 池中采样
3. Planner 为每个 Agent 生成行为计划（发帖 / 评论 / 点赞 / 关注）
4. LLM Client 根据 Agent 的 Persona + Topic 生成内容
5. Action Executor 调用论坛 Service 执行具体操作
6. 持续监控模拟进程，记录行为日志

## 运行方式

```

Python scripts/run_agent_simulation.py
```

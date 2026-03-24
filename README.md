# learn-claude-code

一个围绕“如何从零实现一个可用 coding agent”展开的学习型仓库。

这个仓库现在分成两条主线：

- `learn/`：按阶段演进的教学脚本，从最小 agent loop 一步步长成更复杂的 agent 系统
- `agents/`：把学习过程中沉淀下来的能力收敛成一个统一版本的可运行 agent

如果你想理解 agent 是怎么长出来的，看 `learn/`。
如果你想直接看当前最完整的实现，看 `agents/`。

其中，`learn/` 这条学习路线明确来自 `https://learn.shareai.run/zh/` 对应的项目内容，本仓库是在本地按阶段练习、实现和整理这条路线。

## 项目结构

### `learn/`

`learn/` 里是 `s01.py` 到 `s12.py` 的分阶段实现，每个脚本都强调一个核心概念。

这部分内容对应的是 `https://learn.shareai.run/zh/` 的学习路线，仓库中的脚本命名和阶段划分也与这条路线保持一致。

- `s01`：最小可用的 agent loop
- `s02-s03`：文件/命令工具与任务规划的雏形
- `s04`：子代理 `task` 模式
- `s05-s07`：日志、上下文压缩、长期对话管理
- `s08`：后台任务
- `s09-s11`：多 agent、消息总线、teammate 协作
- `s12`：task + worktree 的隔离执行模型

可以把 `learn/` 理解成一条“从原理到系统”的学习路径。

### `agents/`

`agents/` 是当前收敛后的实现，不再保留多个 `s0x_agent_loop.py` 版本，而是统一成一个主入口：

- [`agents/agent.py`](/home/liam/study/learn-claude-code/agents/agent.py)：主 agent 入口与主循环
- [`agents/tools.py`](/home/liam/study/learn-claude-code/agents/tools.py)：工具注册与 schema
- [`agents/base_tools.py`](/home/liam/study/learn-claude-code/agents/base_tools.py)：基础工具与协议辅助函数
- [`agents/manager.py`](/home/liam/study/learn-claude-code/agents/manager.py)：todo、task、background、worktree 管理
- [`agents/team.py`](/home/liam/study/learn-claude-code/agents/team.py)：teammate 生命周期与协作
- [`agents/message.py`](/home/liam/study/learn-claude-code/agents/message.py)：消息总线与事件日志
- [`agents/context.py`](/home/liam/study/learn-claude-code/agents/context.py)：上下文压缩
- [`agents/layout_message.py`](/home/liam/study/learn-claude-code/agents/layout_message.py)：会话日志记录
- [`agents/config.py`](/home/liam/study/learn-claude-code/agents/config.py)：运行配置与路径解析

可以把 `agents/` 理解成“把 `learn/` 里学到的东西拼成一个当前最强版本”。

## 当前 agent 支持的能力

统一版 agent 目前包含这些核心能力：

- bash / 文件读写 / 精确文本编辑
- todo 跟踪
- task 创建与依赖管理
- `task` 子代理
- background task
- teammate 管理与消息收发
- worktree 创建、运行、保留、移除
- inbox 注入
- 自动压缩与手动压缩
- 会话日志记录

## 运行方式

### 安装依赖

仓库当前声明的 Python 依赖在 [`pyproject.toml`](/home/liam/study/learn-claude-code/pyproject.toml)：

- `anthropic`
- `dotenv`
- `openai`

如果你使用 `uv`：

```bash
uv sync
```

如果你使用 `pip`：

```bash
pip install anthropic dotenv openai
```

### 环境变量

常见环境变量包括：

- `ANTHROPIC_AUTH_TOKEN`
- `ANTHROPIC_BASE_URL`
- `MODEL`
- `WORKDIR`
- `SKILLDIR`

仓库根目录下有 `.env`，agent 启动时会尝试加载它。

### 启动统一 agent

推荐两种方式：

```bash
python -m agents
```

或：

```bash
python agents/agent.py
```

## 运行时目录

agent 运行过程中会在仓库里使用这些目录：

- `.tasks/`：任务数据
- `.worktrees/`：worktree 索引与事件
- `.team/`：teammate 配置与 inbox
- `.logs/`：会话日志
- `output/`：学习总结、review 文档等输出

## 推荐阅读顺序

如果你是第一次看这个仓库，建议按下面顺序：

1. 先看 `learn/s01.py`，理解最小 agent loop
2. 再看 `learn/s04.py`，理解子代理模式
3. 再看 `learn/s08.py`，理解后台任务
4. 再看 `learn/s09.py` 到 `learn/s11.py`，理解多 agent 协作
5. 最后看 `learn/s12.py`，理解 worktree + task 隔离
6. 回到 [`agents/agent.py`](/home/liam/study/learn-claude-code/agents/agent.py)，看统一版如何把这些能力收拢起来

如果你希望和原始课程内容对照阅读，可以直接结合 `https://learn.shareai.run/zh/` 一起看。

## 这个仓库适合怎么用

你可以把这个仓库当成三种东西：

- 一个学习材料仓库：顺着 `learn/` 读，理解 agent 的演进
- 一个实验仓库：在 `agents/` 上继续加能力
- 一个 review 训练仓库：拿重构、状态管理、边界设计来练手

## 相关输出文档

目前 `output/` 里已经有一些和这个仓库配套的说明文档，比如：

- [`output/Agent重构Review规则清单.md`](/home/liam/study/learn-claude-code/output/Agent重构Review规则清单.md)
- `output/费曼学习复盘_Agent压缩上下文机制.md`

## 备注

这个仓库的重点不是“做一个生产级 agent 产品”，而是通过不断演进的代码，把 agent 的关键机制拆开学习，再逐步收敛成一个更完整的实现。

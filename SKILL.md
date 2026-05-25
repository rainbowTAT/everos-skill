---
description: EverOS 长期记忆系统 — 保存和搜索对话记忆，支持 Cloud 和 Local 两种部署模式
---

# EverOS 记忆系统 Skill

让 Claude Code 拥有基于 EverOS 的长期记忆能力。通过手动命令保存和搜索对话记忆。

## 何时使用

- 用户说"接入 EverOS"、"开启记忆系统"、"让 Claude 有记忆"
- 用户想把对话记忆持久化到 EverOS
- 用户要求搭建 EverOS 环境
- 用户要求保存当前对话到记忆
- 用户要求搜索历史记忆

## 部署方式选择

使用前先确定部署方式：

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| **Cloud** | 使用 EverMind 官方云服务 | 快速体验，无需 Docker |
| **Local** | 本地 Docker 部署 | 数据隐私要求高，离线使用 |

### Cloud 模式（推荐新手）

只需设置两个环境变量，无需安装 Docker：

```bash
export EVEROS_API_URL="https://api.evermind.ai"
export EVEROS_API_KEY="your_api_key"
```

获取 API Key：访问 [evermind.ai](https://evermind.ai) 注册账号。

### Local 模式

运行一键安装脚本（脚本位于本 skill 的 `scripts/` 目录下）：

```bash
python scripts/auto_setup.py
```

脚本自动完成：
1. 检测 Docker、uv、Git（uv 未装会自动安装）
2. 克隆 EverOS 源码
3. 启动 Docker Compose 数据库（MongoDB + ES + Milvus + Redis）
4. 交互式配置 .env（LLM Key、Embedding Key）
5. 安装 EverCore Python 依赖
6. 启动 EverCore API
7. 验证所有服务连通

## 手动安装（Local 模式）

如果一键安装失败，按以下步骤手动操作：

### 第一步：启动数据库

```bash
cd EverOS/methods/EverCore
docker compose up -d
```

### 第二步：配置 .env

```bash
cp env.template .env
# 编辑 .env，填入：
# - LLM_API_KEY / OPENROUTER_API_KEY（用于记忆提取）
# - VECTORIZE_API_KEY（用于向量检索，推荐 DeepInfra）
```

### 第三步：启动 EverCore

```bash
uv sync
uv run python src/run.py
```

## 日常使用

### 保存对话记忆

当你想把当前对话保存到 EverOS 时，使用 writer 模块：

```bash
python scripts/write_memory.py \
  --user-id "claude_code_user" \
  --session-id "当前会话ID" \
  --messages '[{"role":"user","content":"用户的问题"},{"role":"assistant","content":"Claude的回答"}]' \
  --flush
```

`--flush` 会触发 EverOS 从对话中自动提取结构化记忆（事实、偏好、事件等）。

### 搜索记忆

在回答用户问题前，先搜索相关历史记忆：

```bash
python scripts/search_memory.py \
  --query "搜索关键词" \
  --method hybrid \
  --top-k 5
```

检索方式：
- `keyword` — 关键词匹配（BM25）
- `vector` — 向量语义搜索
- `hybrid` — 混合搜索
- `agentic` — LLM 引导搜索

### 探测服务状态

```bash
# 自动检测 Cloud/Local 模式
python scripts/probe.py

# 强制检查 Docker（仅 Local 模式）
python scripts/probe.py --check-docker
```

## 记忆类型

EverOS 会从对话中自动提取以下类型的记忆：

| 类型 | 说明 | 示例 |
|------|------|------|
| episodic_memory | 具体事件 | "用户在5月23日讨论了实习项目" |
| profile | 用户偏好/属性 | "用户是双非学历，目标进研究型公司" |
| foresight | 预测/计划 | "用户计划下周完成SQLite迁移" |
| atomic_fact | 原子事实 | "EverOS使用MongoDB存储记忆文档" |
| agent_case | 案例 | "解决Docker内存不足的方法" |
| agent_skill | 技能 | "如何配置DeepInfra embedding" |

## 验证安装

### 检查服务

```bash
python scripts/probe.py
```

### 验证写入

保存几条记忆后搜索验证：

```bash
python scripts/search_memory.py \
  --query "刚才聊的内容" \
  --method keyword
```

有返回结果就说明写入成功。

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| Connection refused | 服务未运行 | 运行 `probe.py` 检查，启动缺失服务 |
| 401 Unauthorized | API Key 无效 | 检查 `EVEROS_API_KEY` 环境变量 |
| 记忆为空 | API Key 未配置 | Cloud: 检查环境变量；Local: 检查 `.env` 中的 LLM/Embedding Key |
| Docker 启动失败 | 内存不足 | 至少需要 4GB 空闲内存 |

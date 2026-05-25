# EverOS Memory Skill

让 Claude Code 拥有基于 EverOS 的长期记忆系统。手动保存对话记忆，语义搜索历史内容。

## 部署方式

| 方式 | 说明 | 要求 |
|------|------|------|
| **Cloud** | 使用 EverMind 官方云服务 | 仅需 API Key |
| **Local** | 本地 Docker 部署 | Docker + 4GB 内存 |

### Cloud 快速开始

```bash
# 设置环境变量
export EVEROS_API_URL="https://api.evermind.ai"
export EVEROS_API_KEY="your_api_key"

# 验证连接
python scripts/probe.py
```

获取 API Key：访问 [evermind.ai](https://evermind.ai) 注册。

### Local 安装

```bash
# 运行一键安装脚本
python scripts/auto_setup.py
```

脚本会自动完成环境搭建：Docker 数据库、EverCore API、依赖安装。

## 使用

### 保存对话记忆

```bash
python scripts/write_memory.py \
  --user-id "claude_code_user" \
  --session-id "session_001" \
  --messages '[{"role":"user","content":"你好"},{"role":"assistant","content":"你好！"}]' \
  --flush
```

### 搜索记忆

```bash
python scripts/search_memory.py \
  --query "搜索内容" \
  --method hybrid \
  --top-k 10
```

### 检查服务状态

```bash
python scripts/probe.py
```

## 目录结构

```
everos-skill/
  SKILL.md              ← 技能定义
  README.md             ← 本文档
  scripts/
    auto_setup.py       ← 一键安装（Local 模式）
    config.py           ← 配置（自动检测 Cloud/Local）
    probe.py            ← 服务探测
    search_memory.py    ← CLI 搜索工具
    write_memory.py     ← CLI 写入工具
```

## 架构

```
Claude Code
    │
    ├── Cloud 模式 ──→ https://api.evermind.ai (Bearer token)
    │
    └── Local 模式 ──→ localhost:1995 EverCore API
                            ├── MongoDB（27017）
                            ├── Elasticsearch（19200）
                            ├── Milvus（19530）
                            └── Redis（6379）
```

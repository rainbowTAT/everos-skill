# EverOS Memory Skill

让 Claude Code 拥有基于 EverOS 的长期记忆系统。支持 Cloud 和 Local 两种部署模式。

## 安装

### 1. 安装 Skill 到 Claude Code

```bash
cd everos-skill
python -X utf8 scripts/everos.py install
```

选择：
- **[1] Global（全局）** — 所有项目都能用（推荐）
- **[2] Project（项目级）** — 仅当前项目可用

安装后重启 Claude Code 生效。

### 2. 选择部署方式

| 方式 | 说明 | 要求 |
|------|------|------|
| **Cloud** | EverMind 官方云服务 | 仅需 API Key |
| **Local** | 本地 Docker 部署 | Docker Desktop + 4GB 内存 |

#### Cloud 模式

1. 访问 [evermind.ai](https://evermind.ai) 注册，获取 API Key
2. 设置环境变量：
   ```bash
   export EVEROS_API_URL="https://api.evermind.ai"
   export EVEROS_API_KEY="your_api_key"
   ```

#### Local 模式

```bash
python -X utf8 scripts/auto_setup.py
```

自动完成：Docker 数据库、EverCore API、依赖安装。

### 3. 验证

```bash
python -X utf8 scripts/everos.py status
```

## 使用

所有操作通过 `python -X utf8 scripts/everos.py` 统一入口：

| 命令 | 作用 |
|------|------|
| `install` | 安装 skill 到 Claude Code |
| `start` | 启动环境（自动拉起 Docker） |
| `save --messages '[...]' --flush` | 保存对话 |
| `search "关键词"` | 搜索记忆 |
| `status` | 检查状态 |
| `test` | 一键测试 |
| `config` | 查看配置 |
| `uninstall` | 卸载 skill |

### 启动环境

```bash
python -X utf8 scripts/everos.py start
```

Local 模式下自动启动 Docker Desktop（如未运行）。

### 保存对话

```bash
python -X utf8 scripts/everos.py save --messages '[{"role":"user","content":"你好"},{"role":"assistant","content":"你好！"}]' --flush
```

### 搜索记忆

```bash
# 关键词搜索
python -X utf8 scripts/everos.py search "用户偏好"

# 语义搜索
python -X utf8 scripts/everos.py search "饮食习惯" --method vector

# 混合搜索
python -X utf8 scripts/everos.py search "摄影器材" --method hybrid --top-k 5
```

### 一键测试

```bash
python -X utf8 scripts/everos.py test
```

自动测试全部功能，输出通过/失败结果。

## 目录结构

```
everos-skill/
  SKILL.md              ← 技能定义（Claude 读取）
  README.md             ← 本文档
  bin/
    everos.cmd          ← Windows 快捷命令
    everos.ps1          ← PowerShell 快捷命令
    everos.sh           ← Mac/Linux 快捷命令
  scripts/
    everos.py           ← 统一命令入口
    auto_setup.py       ← 一键安装（Local 模式）
    setup_skill.py      ← Skill 安装/卸载工具
    test.py             ← 一键测试脚本
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

## 记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| episodic_memory | 具体事件 | "用户在5月23日讨论了实习项目" |
| profile | 用户偏好/属性 | "用户喜欢川菜，讨厌香菜" |
| foresight | 预测/计划 | "用户计划下周完成项目" |
| atomic_fact | 原子事实 | "EverOS使用MongoDB存储记忆" |
| agent_case | 案例 | "解决Docker内存不足的方法" |
| agent_skill | 技能 | "如何配置DeepInfra embedding" |

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| Connection refused | 服务未运行 | `python -X utf8 scripts/everos.py status` 检查 |
| 401 Unauthorized | API Key 无效 | 检查 `EVEROS_API_KEY` 环境变量 |
| Docker 启动失败 | 内存不足 | 至少需要 4GB 空闲内存 |
| 未检测到配置 | 未安装 | 运行 `python -X utf8 scripts/everos.py install` |

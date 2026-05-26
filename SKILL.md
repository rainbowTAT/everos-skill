---
description: EverOS 长期记忆系统 — 保存和搜索对话记忆，支持 Cloud 和 Local 两种部署模式
---

# EverOS 记忆系统 Skill

让 Claude Code 拥有基于 EverOS 的长期记忆能力。

## 何时使用

- 用户说"接入 EverOS"、"开启记忆系统"、"让 Claude 有记忆"
- 用户想把对话记忆持久化到 EverOS
- 用户要求搭建 EverOS 环境
- 用户要求保存当前对话到记忆
- 用户要求搜索历史记忆

## 首次安装引导

当用户首次使用时，按以下步骤引导。每一步先向用户说明在做什么，再执行命令。

### 1. 安装 Skill 到 Claude Code

告知用户正在将 EverOS 记忆系统注册到 Claude Code，然后执行：

```bash
cd everos-skill && python -X utf8 scripts/everos.py install
```

脚本会提示选择全局或项目级安装。引导用户选择后，告知需要重启 Claude Code 才能生效。

### 2. 选择部署方式

向用户说明两种模式的区别，让用户选择：

```
请选择部署方式：
  [1] Cloud（云端）— 注册即用，无需 Docker，数据存云端
  [2] Local（本地）— 需要 Docker，数据完全在本地，更隐私
```

### 3a. Cloud 模式配置

引导用户完成以下操作：

1. 打开 [evermind.ai](https://evermind.ai) 注册账号
2. 获取 API Key
3. 执行以下命令设置环境变量（把 `your_api_key` 替换为实际的 key）：

```bash
export EVEROS_API_URL="https://api.evermind.ai"
export EVEROS_API_KEY="your_api_key"
```

### 3b. Local 模式安装

告知用户正在自动安装本地环境（需要 Docker Desktop，约 5-10 分钟），然后执行：

```bash
cd everos-skill && python -X utf8 scripts/auto_setup.py
```

安装过程中会自动：检测依赖 → 克隆源码 → 启动数据库 → 配置环境 → 安装依赖 → 启动 API。

如果脚本提示输入 LLM API Key，引导用户提供（用于记忆提取功能）。

### 4. 验证安装

```bash
cd everos-skill && python -X utf8 scripts/everos.py status
```

显示各组件"正常"即安装成功。如有异常，参考下方错误处理表排查。

## 日常使用

以下命令直接执行，无需额外解释。所有命令均在 `everos-skill` 目录下运行。

### 启动环境

```bash
cd everos-skill && python -X utf8 scripts/everos.py start
```

自动检测 Cloud/Local 模式。Local 模式下会自动启动 Docker Desktop（如未运行）。

### 保存当前对话

将当前对话内容序列化为 JSON 后执行。格式：`[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]`

```bash
cd everos-skill && python -X utf8 scripts/everos.py save --messages '[对话JSON]' --flush
```

`--flush` 触发记忆提取，必须带上。

### 搜索记忆

```bash
cd everos-skill && python -X utf8 scripts/everos.py search "关键词"
```

可选参数：`--method vector|keyword|hybrid|agentic`，`--top-k 数量`

### 检查状态

```bash
cd everos-skill && python -X utf8 scripts/everos.py status
```

### 一键测试

```bash
cd everos-skill && python -X utf8 scripts/everos.py test
```

自动测试：Docker → 容器 → API → 保存 → 搜索，输出通过/失败结果。

## 自动判断模式

| 用户配置 | 行为 |
|----------|------|
| 只有 Cloud 环境变量 | 自动用云端 |
| 只有本地 EverOS 安装 | 自动用本地 |
| 都有 | 提示用户选择 |

## 记忆类型

| 类型 | 说明 |
|------|------|
| episodic_memory | 对话中的具体事件 |
| profile | 用户偏好/属性 |
| foresight | 计划/预测 |
| atomic_fact | 原子事实 |
| agent_case | 解决方案案例 |
| agent_skill | 技能/方法 |

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| Connection refused | 服务未运行 | `cd everos-skill && python -X utf8 scripts/everos.py status` 检查 |
| 401 Unauthorized | API Key 无效 | 检查 `EVEROS_API_KEY` 环境变量 |
| Docker 启动失败 | 内存不足 | 至少需要 4GB 空闲内存 |
| 未检测到配置 | 未安装 | 引导用户重新执行安装流程 |

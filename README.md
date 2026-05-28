# EverOS Memory Skill

把 EverOS 长期记忆接到 Claude Code 里。目标是让新手只记一个入口：

```bash
python -X utf8 scripts/everos.py
```

The project is split into:

- Core commands: shared EverOS setup, start, save, search, and diagnosis.
- Claude Code integration: automatic memory hooks under `integrations/claude-code/`.

Codex integration is intentionally not implemented yet.

## 新手开始

```bash
cd everos-skill
python -X utf8 scripts/everos.py setup claude
python -X utf8 scripts/everos.py doctor
```

`doctor` 会自动检查环境，并告诉你下一步该运行什么。

## 常用命令

```bash
# 一键诊断
python -X utf8 scripts/everos.py doctor

# 启动本地 EverOS，Cloud 模式不需要
python -X utf8 scripts/everos.py start

# 查看状态
python -X utf8 scripts/everos.py status

# 搜索记忆
python -X utf8 scripts/everos.py search "用户喜欢什么" --method hybrid

# 保存一段对话
python -X utf8 scripts/everos.py save --messages "[{\"role\":\"user\",\"content\":\"你好\"},{\"role\":\"assistant\",\"content\":\"你好！\"}]" --flush

# 停止本地数据库
python -X utf8 scripts/everos.py stop
```

## 部署方式

| 方式 | 适合谁 | 要求 |
| --- | --- | --- |
| Cloud | 新手、想最快使用 | EverMind API Key |
| Local | 想数据留在本地 | Docker Desktop、uv、本地 EverOS |

## Claude Code 自动记忆

安装：

```bash
python -X utf8 scripts/everos.py setup claude
```

它会注册两个 Claude Code hooks：

- `UserPromptSubmit`: 用户提问前搜索 EverOS，并把相关记忆注入上下文。
- `Stop`: Claude 回答后保存本轮对话到 EverOS。

安装后重启 Claude Code 生效。

## 文档

- 首次安装：`docs/install.md`
- 日常使用：`docs/daily-use.md`
- 排错：`docs/troubleshoot.md`
- Claude Code hooks：`docs/hooks.md`

## 目录

```text
everos-skill/
  SKILL.md
  README.md
  docs/
  scripts/
  integrations/
    claude-code/
  bin/
  EverOS/
```

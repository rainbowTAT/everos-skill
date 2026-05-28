---
name: everos
description: Install, diagnose, start, and use EverOS long-term memory for Claude Code. Use when the user wants to connect EverOS, enable Claude Code memory, configure Cloud or Local EverOS, save or search conversation memories, troubleshoot EverOS setup, or add Claude Code hooks for automatic memory.
---

# EverOS Skill

Use the unified CLI first. Run commands from the `everos-skill` directory.

```bash
python -X utf8 scripts/everos.py doctor
python -X utf8 scripts/everos.py setup claude
python -X utf8 scripts/everos.py start
python -X utf8 scripts/everos.py status
python -X utf8 scripts/everos.py search "关键词"
```

## Default Workflow

1. For Claude Code automatic memory, run `python -X utf8 scripts/everos.py setup claude`.
2. If the user is confused or something fails, run `python -X utf8 scripts/everos.py doctor`.
3. If Local mode is configured, start EverOS with `python -X utf8 scripts/everos.py start`.
4. If Cloud mode is configured, do not start local services; verify with `python -X utf8 scripts/everos.py status`.
5. Save messages with `python -X utf8 scripts/everos.py save --messages '[...]' --flush`.
6. Search memory with `python -X utf8 scripts/everos.py search "query" --method hybrid`.

## Read Only When Needed

- First install details: `docs/install.md`
- Daily commands: `docs/daily-use.md`
- Troubleshooting: `docs/troubleshoot.md`
- Claude Code hooks: `docs/hooks.md`

Keep answers beginner-friendly: tell the user exactly which command to run next.

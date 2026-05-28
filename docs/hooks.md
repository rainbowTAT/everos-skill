# Claude Code Hooks

Hooks are automatic background actions. They are Claude Code specific; they are not the same thing as the shared EverOS CLI.

Install:

```bash
python -X utf8 scripts/everos.py setup claude
```

Installed hooks:

- `UserPromptSubmit`: runs `integrations/claude-code/inject_memory.py`, searches EverOS, and injects relevant memory into Claude's context.
- `Stop`: runs `integrations/claude-code/store_memory.py`, extracts the latest complete turn from Claude's transcript, saves it to EverOS, then flushes memory extraction.

Files:

```text
integrations/claude-code/
  hooks.json
  inject_memory.py
  store_memory.py
```

Uninstall:

```bash
python -X utf8 scripts/everos.py uninstall global
```

or:

```bash
python -X utf8 scripts/everos.py uninstall project
```

The uninstall command removes only EverOS hooks and keeps unrelated user hooks.

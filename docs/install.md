# EverOS Install

Use this page only for first-time setup.

## Beginner Path

Run from `everos-skill`:

```bash
python -X utf8 scripts/everos.py setup claude
```

Then run:

```bash
python -X utf8 scripts/everos.py doctor
```

## Cloud Mode

Cloud mode is the easiest path for beginners.

1. Create an EverMind account.
2. Get an API key.
3. Set environment variables:

```bash
setx EVEROS_API_URL "https://api.evermind.ai"
setx EVEROS_API_KEY "your_api_key"
```

Restart the terminal after `setx`.

## Local Mode

Local mode keeps data on the user's machine, but requires Docker Desktop.

```bash
python -X utf8 scripts/auto_setup.py
```

After setup:

```bash
python -X utf8 scripts/everos.py start
python -X utf8 scripts/everos.py status
```

## After Install

Show the user these commands:

```bash
python -X utf8 scripts/everos.py doctor
python -X utf8 scripts/everos.py start
python -X utf8 scripts/everos.py search "关键词"
```

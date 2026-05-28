# EverOS Daily Use

Run commands from `everos-skill`.

## Check What To Do

```bash
python -X utf8 scripts/everos.py doctor
```

## Install Claude Code Automatic Memory

```bash
python -X utf8 scripts/everos.py setup claude
```

Restart Claude Code after installing hooks.

## Start Local EverOS

```bash
python -X utf8 scripts/everos.py start
```

Cloud mode does not need `start`.

## Check Status

```bash
python -X utf8 scripts/everos.py status
```

## Save A Conversation

```bash
python -X utf8 scripts/everos.py save --messages "[{\"role\":\"user\",\"content\":\"你好\"},{\"role\":\"assistant\",\"content\":\"你好！\"}]" --flush
```

## Search Memories

```bash
python -X utf8 scripts/everos.py search "用户喜欢什么" --method hybrid
```

## Stop Local Databases

```bash
python -X utf8 scripts/everos.py stop
```

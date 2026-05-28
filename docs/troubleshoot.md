# EverOS Troubleshooting

Start with:

```bash
python -X utf8 scripts/everos.py doctor
```

## Common Results

`Docker 未运行`

Run:

```bash
python -X utf8 scripts/everos.py start
```

`EverCore API 未响应`

Local mode likely needs to start:

```bash
python -X utf8 scripts/everos.py start
```

`Cloud Key 未配置`

Set `EVEROS_API_KEY`, then restart the terminal.

`401 Unauthorized`

The API key is missing, invalid, or expired.

`未检测到配置`

Run:

```bash
python -X utf8 scripts/everos.py setup
```

`Claude Code 自动记忆 hooks 未完整安装`

Run:

```bash
python -X utf8 scripts/everos.py setup claude
```

Then restart Claude Code.

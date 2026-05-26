@echo off
:: EverOS CLI - Windows Batch Wrapper
:: Usage: everos <command> [args]
::   everos start              Start local environment
::   everos save [--flush]     Save current conversation
::   everos search "query"     Search memories
::   everos status             Check service status
::   everos config             Show configuration
::   everos install            Install skill to Claude Code
::   everos uninstall          Remove skill from Claude Code

python -X utf8 "%~dp0..\scripts\everos.py" %*

#!/bin/bash
# EverOS CLI - Unix Shell Wrapper
# Usage: ./everos.sh <command> [args]
#   everos.sh start              Start local environment
#   everos.sh save [--flush]     Save current conversation
#   everos.sh search "query"     Search memories
#   everos.sh status             Check service status
#   everos.sh config             Show configuration

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python -X utf8 "$SCRIPT_DIR/../scripts/everos.py" "$@"

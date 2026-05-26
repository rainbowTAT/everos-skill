# EverOS CLI - PowerShell Wrapper
# Usage: .\everos.ps1 <command> [args]

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "..\scripts\everos.py"

python -X utf8 $scriptPath @args

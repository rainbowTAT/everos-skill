"""Install everos-skill to Claude Code settings.

Supports:
  - Global: ~/.claude/settings.json (available in all projects)
  - Project: .claude/settings.json in current directory

Usage:
    python setup_skill.py                # Interactive (ask user)
    python setup_skill.py --global       # Install globally
    python setup_skill.py --project      # Install to current project
    python setup_skill.py --uninstall    # Remove from settings
"""

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = "everos"
SKILL_DESC = "EverOS 长期记忆系统 — 保存、搜索并自动注入 Claude Code 对话记忆"
INJECT_HOOK = os.path.join(SKILL_DIR, "integrations", "claude-code", "inject_memory.py")
STORE_HOOK = os.path.join(SKILL_DIR, "integrations", "claude-code", "store_memory.py")

GLOBAL_SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
PROJECT_SETTINGS = os.path.join(os.getcwd(), ".claude", "settings.json")


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved to {path}")


def get_skill_entry():
    return {
        "name": SKILL_NAME,
        "path": SKILL_DIR,
        "description": SKILL_DESC,
    }


def hook_command(script_path):
    return f'"{sys.executable}" -X utf8 "{script_path}"'


def everos_hook_commands():
    return {
        "UserPromptSubmit": hook_command(INJECT_HOOK),
        "Stop": hook_command(STORE_HOOK),
    }


def is_everos_hook(hook):
    command = hook.get("command", "") if isinstance(hook, dict) else ""
    normalized = command.replace("\\", "/")
    return (
        "/integrations/claude-code/inject_memory.py" in normalized
        or "/integrations/claude-code/store_memory.py" in normalized
    )


def remove_everos_hooks(settings):
    hooks_root = settings.get("hooks", {})
    if not isinstance(hooks_root, dict):
        return

    for event, blocks in list(hooks_root.items()):
        if not isinstance(blocks, list):
            continue
        new_blocks = []
        for block in blocks:
            hook_list = block.get("hooks", []) if isinstance(block, dict) else []
            kept_hooks = [h for h in hook_list if not is_everos_hook(h)]
            if kept_hooks:
                block = dict(block)
                block["hooks"] = kept_hooks
                new_blocks.append(block)
        if new_blocks:
            hooks_root[event] = new_blocks
        else:
            hooks_root.pop(event, None)

    if not hooks_root:
        settings.pop("hooks", None)


def install_hooks(settings):
    remove_everos_hooks(settings)
    hooks_root = settings.setdefault("hooks", {})
    for event, command in everos_hook_commands().items():
        hooks_root.setdefault(event, []).append({
            "matcher": "*",
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": 10 if event == "UserPromptSubmit" else 30,
                }
            ],
        })


def install(target):
    settings_path = GLOBAL_SETTINGS if target == "global" else PROJECT_SETTINGS
    settings = load_json(settings_path)

    skills = settings.get("skills", [])
    entry = get_skill_entry()
    installed = False

    # Check if already installed
    for i, s in enumerate(skills):
        if s.get("name") == SKILL_NAME:
            skills[i] = entry
            settings["skills"] = skills
            installed = True
            break

    if not installed:
        skills.append(entry)
        settings["skills"] = skills

    install_hooks(settings)
    save_json(settings_path, settings)

    if installed:
        print(f"[OK] Updated existing skill '{SKILL_NAME}' in {settings_path}")
    else:
        print(f"[OK] Installed skill '{SKILL_NAME}' to {settings_path}")
    print("[OK] Claude Code hooks installed: UserPromptSubmit, Stop")


def uninstall(target):
    settings_path = GLOBAL_SETTINGS if target == "global" else PROJECT_SETTINGS
    settings = load_json(settings_path)

    skills = settings.get("skills", [])
    new_skills = [s for s in skills if s.get("name") != SKILL_NAME]

    settings["skills"] = new_skills
    if not new_skills:
        settings.pop("skills", None)
    remove_everos_hooks(settings)
    save_json(settings_path, settings)
    if len(new_skills) == len(skills):
        print(f"[INFO] Skill '{SKILL_NAME}' not found; EverOS hooks removed if present")
    else:
        print(f"[OK] Removed skill '{SKILL_NAME}' and EverOS hooks from {settings_path}")


def check_status():
    """Show where the skill is currently installed."""
    print("=== everos-skill Installation Status ===\n")
    print(f"Skill source: {SKILL_DIR}\n")

    for label, path in [("Global", GLOBAL_SETTINGS), ("Project", PROJECT_SETTINGS)]:
        settings = load_json(path)
        skills = settings.get("skills", [])
        found = [s for s in skills if s.get("name") == SKILL_NAME]
        if found:
            print(f"  [{label}] {path}")
            print(f"    -> INSTALLED (path: {found[0].get('path', 'N/A')})")
        else:
            print(f"  [{label}] {path}")
            print(f"    -> NOT installed")
        hooks = settings.get("hooks", {})
        hook_count = 0
        for blocks in hooks.values() if isinstance(hooks, dict) else []:
            for block in blocks if isinstance(blocks, list) else []:
                hook_count += sum(1 for h in block.get("hooks", []) if is_everos_hook(h))
        print(f"    -> EverOS hooks: {hook_count}")


def main():
    parser = argparse.ArgumentParser(description="Install everos-skill to Claude Code")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--global", action="store_true", dest="global_", help="Install to global settings")
    group.add_argument("--project", action="store_true", help="Install to current project settings")
    group.add_argument("--uninstall", nargs="?", const="all", choices=["global", "project", "all"],
                       help="Remove from settings")
    group.add_argument("--status", action="store_true", help="Show installation status")
    args = parser.parse_args()

    if args.status:
        check_status()
        return

    if args.uninstall:
        if args.uninstall in ("global", "all"):
            uninstall("global")
        if args.uninstall in ("project", "all"):
            uninstall("project")
        return

    if args.global_:
        install("global")
        return

    if args.project:
        install("project")
        return

    # Interactive mode
    print("=== Install everos-skill to Claude Code ===\n")
    print("Choose installation scope:")
    print("  [1] Global  — available in ALL projects (recommended)")
    print("  [2] Project — only available in current project directory")
    print()

    while True:
        choice = input("Select (1/2): ").strip()
        if choice == "1":
            install("global")
            return
        elif choice == "2":
            install("project")
            return
        print("Invalid input, please enter 1 or 2")


if __name__ == "__main__":
    main()

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
SKILL_DESC = "EverOS 长期记忆系统 — 保存和搜索对话记忆"

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


def install(target):
    settings_path = GLOBAL_SETTINGS if target == "global" else PROJECT_SETTINGS
    settings = load_json(settings_path)

    skills = settings.get("skills", [])
    entry = get_skill_entry()

    # Check if already installed
    for i, s in enumerate(skills):
        if s.get("name") == SKILL_NAME:
            skills[i] = entry
            settings["skills"] = skills
            save_json(settings_path, settings)
            print(f"[OK] Updated existing skill '{SKILL_NAME}' in {settings_path}")
            return

    # Add new
    skills.append(entry)
    settings["skills"] = skills
    save_json(settings_path, settings)
    print(f"[OK] Installed skill '{SKILL_NAME}' to {settings_path}")


def uninstall(target):
    settings_path = GLOBAL_SETTINGS if target == "global" else PROJECT_SETTINGS
    settings = load_json(settings_path)

    skills = settings.get("skills", [])
    new_skills = [s for s in skills if s.get("name") != SKILL_NAME]

    if len(new_skills) == len(skills):
        print(f"[INFO] Skill '{SKILL_NAME}' not found in {settings_path}")
        return

    settings["skills"] = new_skills
    if not new_skills:
        del settings["skills"]
    save_json(settings_path, settings)
    print(f"[OK] Removed skill '{SKILL_NAME}' from {settings_path}")


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

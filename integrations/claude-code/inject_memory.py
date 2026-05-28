"""Claude Code UserPromptSubmit hook: search EverOS and inject relevant memory."""

import json
import os
import sys
import urllib.error
import urllib.request

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.abspath(os.path.join(HOOK_DIR, "..", ".."))
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from config import DEFAULT_USER_ID, HEADERS, SEARCH_URL  # noqa: E402


def output(data):
    print(json.dumps(data, ensure_ascii=False))


def read_input():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def post_json(url, payload, timeout=8):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def pick_prompt(data):
    prompt = data.get("prompt") or data.get("message") or ""
    if isinstance(prompt, list):
        texts = []
        for item in prompt:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
        prompt = "\n".join(texts)
    return str(prompt).strip()


def format_memories(result):
    data = result.get("data", {})
    lines = []

    for ep in data.get("episodes", [])[:5]:
        subject = ep.get("subject") or "记忆"
        summary = ep.get("summary") or ep.get("content") or ""
        if summary:
            lines.append(f"- {subject}: {summary[:300]}")

    for profile in data.get("profiles", [])[:3]:
        profile_data = profile.get("profile_data", {})
        if profile_data:
            text = json.dumps(profile_data, ensure_ascii=False)
            lines.append(f"- 用户画像: {text[:300]}")

    agent_mem = data.get("agent_memory") or {}
    for case in agent_mem.get("cases", [])[:3]:
        text = case.get("task_intent") or case.get("solution") or ""
        if text:
            lines.append(f"- 历史案例: {text[:300]}")
    for skill in agent_mem.get("skills", [])[:3]:
        name = skill.get("name") or "技能"
        content = skill.get("content") or skill.get("description") or ""
        lines.append(f"- {name}: {content[:300]}")

    return lines


def main():
    data = read_input()
    prompt = pick_prompt(data)
    if len(prompt) < 3:
        output({"continue": True})
        return

    payload = {
        "query": prompt,
        "method": "hybrid",
        "memory_types": ["episodic_memory", "profile", "agent_memory"],
        "top_k": 5,
        "filters": {"user_id": os.getenv("EVEROS_USER_ID", DEFAULT_USER_ID)},
    }

    try:
        result = post_json(SEARCH_URL, payload)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        output({"continue": True, "systemMessage": f"EverOS 记忆检索跳过: {e}"})
        return

    memories = format_memories(result)
    if not memories:
        output({"continue": True})
        return

    system_prompt = (
        "<everos-memory>\n"
        "以下是 EverOS 检索到的历史记忆。只在与当前任务相关时使用，不要编造未出现的信息。\n"
        + "\n".join(memories)
        + "\n</everos-memory>"
    )
    output({
        "continue": True,
        "systemMessage": f"EverOS: 已注入 {len(memories)} 条相关记忆",
        "systemPrompt": system_prompt,
    })


if __name__ == "__main__":
    main()

"""Claude Code Stop hook: save the latest complete turn to EverOS."""

import json
import os
import sys
import time
import urllib.error
import urllib.request

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.abspath(os.path.join(HOOK_DIR, "..", ".."))
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from config import AGENT_ADD_URL, AGENT_FLUSH_URL, DEFAULT_USER_ID, HEADERS  # noqa: E402


def output(data):
    print(json.dumps(data, ensure_ascii=False))


def read_input():
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def load_transcript(path):
    for _ in range(5):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f if line.strip()]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        if lines and lines[-1].get("type") == "system" and lines[-1].get("subtype") == "turn_duration":
            return lines
        time.sleep(0.1)
    return lines if "lines" in locals() else []


def text_from_content(content, role):
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    texts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if role == "user" and item_type == "tool_result":
            continue
        if item_type == "text":
            texts.append(item.get("text", ""))
    return "\n\n".join(t for t in texts if t).strip()


def latest_turn(lines):
    boundaries = [
        i for i, line in enumerate(lines)
        if line.get("type") == "system" and line.get("subtype") == "turn_duration"
    ]
    if not boundaries:
        return []
    end = boundaries[-1]
    start = boundaries[-2] + 1 if len(boundaries) >= 2 else 0
    return lines[start:end]


def extract_messages(turn):
    messages = []
    now_ms = int(time.time() * 1000)
    for line in turn:
        msg = line.get("message") or {}
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        text = text_from_content(msg.get("content"), role)
        if not text:
            continue
        messages.append({
            "role": role,
            "timestamp": now_ms + len(messages) * 1000,
            "content": text,
        })
    return messages


def post_json(url, payload, timeout=30):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def main():
    data = read_input()
    transcript_path = data.get("transcript_path")
    if not transcript_path:
        output({"continue": True})
        return

    lines = load_transcript(transcript_path)
    messages = extract_messages(latest_turn(lines))
    if not messages:
        output({"continue": True})
        return

    user_id = os.getenv("EVEROS_USER_ID", DEFAULT_USER_ID)
    session_id = data.get("session_id")
    payload = {"user_id": user_id, "messages": messages}
    if session_id:
        payload["session_id"] = session_id

    try:
        post_json(AGENT_ADD_URL, payload, timeout=20)
        flush_payload = {"user_id": user_id}
        if session_id:
            flush_payload["session_id"] = session_id
        post_json(AGENT_FLUSH_URL, flush_payload, timeout=25)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        output({"continue": True, "systemMessage": f"EverOS: 保存记忆失败: {e}"})
        return

    output({"continue": True, "systemMessage": f"EverOS: 已保存 {len(messages)} 条对话消息"})


if __name__ == "__main__":
    main()

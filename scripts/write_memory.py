"""Write conversation memory to EverOS.

Supports auto-detection of Cloud/Local mode.

Usage:
    python write_memory.py --messages '[{"role":"user","content":"hello"}]' --flush
    python write_memory.py --messages-file conversation.json --flush
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

from config import AGENT_ADD_URL, AGENT_FLUSH_URL, DEFAULT_USER_ID, HEADERS


def post_json(url, data, timeout=30):
    """POST JSON to URL and return response."""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers=HEADERS,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def flush_async(url, data):
    """Fire flush via curl in background, don't wait for response."""
    body = json.dumps(data, ensure_ascii=False)
    cmd = ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json", "-d", body]
    if HEADERS.get("Authorization"):
        cmd.extend(["-H", HEADERS["Authorization"]])
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {"data": {"status": "flushing", "message": "Flush triggered (async)"}}


def build_messages(raw_messages):
    """Convert simple {role, content} messages to agent message format."""
    now_ms = int(time.time() * 1000)
    messages = []
    for i, msg in enumerate(raw_messages):
        role = msg.get("role")
        content = msg.get("content", "")
        if not role or not content:
            continue
        messages.append({
            "role": role,
            "timestamp": now_ms + i * 1000,
            "content": content,
        })
    return messages


def main():
    parser = argparse.ArgumentParser(description="Write conversation memory to EverOS")
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help="User ID")
    parser.add_argument("--session-id", default=None, help="Session ID")
    parser.add_argument(
        "--messages",
        help='JSON array of messages: [{"role":"user","content":"..."},...]',
    )
    parser.add_argument(
        "--messages-file",
        help="Path to JSON file containing messages",
    )
    parser.add_argument("--flush", action="store_true", help="Flush after writing")
    parser.add_argument("--wait", action="store_true", help="Wait for flush to complete (slow)")
    args = parser.parse_args()

    # Read messages from argument or file
    if args.messages:
        raw_messages_str = args.messages
    elif args.messages_file:
        try:
            with open(args.messages_file, "r", encoding="utf-8") as f:
                raw_messages_str = f.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.messages_file}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: specify --messages or --messages-file", file=sys.stderr)
        sys.exit(1)

    try:
        raw = json.loads(raw_messages_str)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    messages = build_messages(raw)
    if not messages:
        print("Error: no valid messages", file=sys.stderr)
        sys.exit(1)

    payload = {"user_id": args.user_id, "messages": messages}
    if args.session_id:
        payload["session_id"] = args.session_id

    # Add messages
    try:
        result = post_json(AGENT_ADD_URL, payload)
    except urllib.error.URLError as e:
        print(f"Error: failed to save: {e}", file=sys.stderr)
        sys.exit(1)

    data = result.get("data", {})
    print(f"Add: {data.get('message_count', 0)} messages, status={data.get('status', 'unknown')}")

    # Flush if requested
    if args.flush:
        flush_payload = {"user_id": args.user_id}
        if args.session_id:
            flush_payload["session_id"] = args.session_id

        if args.wait:
            result = post_json(AGENT_FLUSH_URL, flush_payload, timeout=300)
            data = result.get("data", {})
            print(f"Flush: status={data.get('status', 'unknown')}")
        else:
            result = flush_async(AGENT_FLUSH_URL, flush_payload)
            print("Flush: triggered (async, not waiting)")


if __name__ == "__main__":
    main()

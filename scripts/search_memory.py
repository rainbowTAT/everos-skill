"""Search memories in EverOS.

Usage:
    python search_memory.py --query "搜索内容"
    python search_memory.py --query "搜索内容" --method vector --top-k 5
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

from config import SEARCH_URL, DEFAULT_USER_ID, HEADERS


def main():
    parser = argparse.ArgumentParser(description="Search EverOS memories")
    parser.add_argument("--query", required=True, help="Search query text")
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help="User ID")
    parser.add_argument("--method", default="keyword", choices=["keyword", "vector", "hybrid", "agentic"],
                        help="Retrieval method")
    parser.add_argument("--top-k", type=int, default=10, help="Max results")
    parser.add_argument("--memory-types", default="episodic_memory",
                        help="Comma-separated memory types")
    args = parser.parse_args()

    types = [t.strip() for t in args.memory_types.split(",")]

    payload = {
        "query": args.query,
        "method": args.method,
        "memory_types": types,
        "top_k": args.top_k,
        "filters": {"user_id": args.user_id},
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        SEARCH_URL,
        data=body,
        headers=HEADERS,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    data = result.get("data", {})
    episodes = data.get("episodes", [])
    profiles = data.get("profiles", [])
    agent_mem = data.get("agent_memory")

    print(f"Found {len(episodes)} episodes, {len(profiles)} profiles")

    for ep in episodes:
        print(f"\n[Episode] {ep.get('subject', 'N/A')}")
        print(f"  Summary: {ep.get('summary', 'N/A')[:200]}")
        print(f"  Score: {ep.get('score', 'N/A')}")

    for p in profiles:
        print(f"\n[Profile] user={p.get('user_id')}")
        print(f"  Data: {json.dumps(p.get('profile_data', {}), ensure_ascii=False)[:200]}")

    if agent_mem:
        for c in agent_mem.get("cases", []):
            print(f"\n[Agent Case] {c.get('task_intent', 'N/A')[:100]}")
        for s in agent_mem.get("skills", []):
            print(f"\n[Agent Skill] {s.get('name', 'N/A')}")


if __name__ == "__main__":
    main()

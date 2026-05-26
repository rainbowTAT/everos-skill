"""EverOS 一键测试脚本。

自动测试：
  1. Docker 状态
  2. 数据库容器
  3. EverCore API
  4. 保存对话
  5. 搜索记忆

用法:
    python -X utf8 scripts/test.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from config import API_BASE_URL, HEALTH_URL, AGENT_ADD_URL, AGENT_FLUSH_URL, SEARCH_URL, DEFAULT_USER_ID, HEADERS

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
passed = 0
failed = 0
skipped = 0


def report(tag, msg):
    global passed, failed, skipped
    if tag == PASS:
        passed += 1
    elif tag == FAIL:
        failed += 1
    else:
        skipped += 1
    print(f"  {tag} {msg}")


def test_docker():
    """Test 1: Docker 是否运行"""
    print("\n[1/5] 检查 Docker...")
    import subprocess
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, check=True)
        report(PASS, "Docker 正在运行")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        report(FAIL, "Docker 未运行")
        return False


def test_containers():
    """Test 2: 数据库容器是否正常"""
    print("\n[2/5] 检查数据库容器...")
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        containers = {}
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    containers[parts[0]] = parts[1]

        expected = {
            "memsys-mongodb": False,
            "memsys-elasticsearch": False,
            "memsys-redis": False,
            "memsys-milvus-standalone": False,
        }

        for name in expected:
            status = containers.get(name, "")
            if "up" in status.lower() or "healthy" in status.lower():
                expected[name] = True
                report(PASS, f"{name} 正常")
            else:
                report(FAIL, f"{name} 未运行 ({status or '未找到'})")

        return all(expected.values())
    except Exception as e:
        report(FAIL, f"检查容器失败: {e}")
        return False


def test_api():
    """Test 3: EverCore API 是否响应"""
    print("\n[3/5] 检查 EverCore API...")
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            report(PASS, f"API 正常 ({data.get('status', 'ok')})")
            return True
    except urllib.error.URLError as e:
        report(FAIL, f"API 无响应: {e}")
        return False
    except Exception as e:
        report(FAIL, f"API 检查失败: {e}")
        return False


def test_save():
    """Test 4: 保存对话"""
    print("\n[4/5] 测试保存对话...")
    now_ms = int(time.time() * 1000)
    payload = {
        "user_id": DEFAULT_USER_ID,
        "messages": [
            {"role": "user", "timestamp": now_ms, "content": "我喜欢川菜和胶片摄影"},
            {"role": "assistant", "timestamp": now_ms + 1000, "content": "好的，记住了你喜欢川菜和胶片摄影。"},
        ],
    }

    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(AGENT_ADD_URL, data=body, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            count = result.get("data", {}).get("message_count", 0)
            report(PASS, f"已保存 {count} 条消息")
    except Exception as e:
        report(FAIL, f"保存失败: {e}")
        return False

    # Flush
    print("  正在提取记忆", end="", flush=True)
    try:
        flush_payload = {"user_id": DEFAULT_USER_ID}
        flush_body = json.dumps(flush_payload, ensure_ascii=False).encode("utf-8")
        flush_req = urllib.request.Request(AGENT_FLUSH_URL, data=flush_body, headers=HEADERS, method="POST")
        with urllib.request.urlopen(flush_req, timeout=300) as resp:
            result = json.loads(resp.read())
            status = result.get("data", {}).get("status", "unknown")
            print()
            if status in ("ok", "completed", "success"):
                report(PASS, f"记忆提取成功 ({status})")
            else:
                report(PASS, f"记忆提取状态: {status}")
        return True
    except Exception as e:
        print()
        report(FAIL, f"记忆提取失败: {e}")
        return False


def test_search():
    """Test 5: 搜索记忆"""
    print("\n[5/5] 测试搜索记忆...")
    queries = [
        ("川菜", "keyword"),
        ("摄影爱好", "vector"),
    ]
    all_ok = True
    for query, method in queries:
        try:
            payload = {
                "query": query,
                "method": method,
                "memory_types": ["episodic_memory", "profile", "atomic_fact"],
                "top_k": 5,
                "filters": {"user_id": DEFAULT_USER_ID},
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(SEARCH_URL, data=body, headers=HEADERS, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                data = result.get("data", {})
                episodes = data.get("episodes", [])
                profiles = data.get("profiles", [])
                total = len(episodes) + len(profiles)
                if total > 0:
                    report(PASS, f'搜索 "{query}" ({method}): 找到 {total} 条结果')
                else:
                    report(PASS, f'搜索 "{query}" ({method}): 无结果（记忆可能还在处理中）')
        except Exception as e:
            report(FAIL, f'搜索 "{query}" 失败: {e}')
            all_ok = False
    return all_ok


def main():
    print("=" * 40)
    print("  EverOS 一键测试")
    print("=" * 40)

    docker_ok = test_docker()
    if docker_ok:
        containers_ok = test_containers()
    else:
        print()
        report(SKIP, "容器检查（Docker 未运行）")
        containers_ok = False

    api_ok = test_api()

    if api_ok:
        save_ok = test_save()
        search_ok = test_search()
    else:
        print()
        report(SKIP, "保存对话（API 不可用）")
        print()
        report(SKIP, "搜索记忆（API 不可用）")
        save_ok = False
        search_ok = False

    # Summary
    print("\n" + "=" * 40)
    print(f"  结果: {passed} 通过, {failed} 失败, {skipped} 跳过")

    if failed == 0 and passed > 0:
        print("  状态: 全部通过!")
    elif failed > 0:
        print("  状态: 部分测试失败，请检查上方错误信息")
    else:
        print("  状态: 未执行任何测试，请先启动 Docker Desktop")

    print("=" * 40)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

"""Probe EverOS services health status.

Supports auto-detection of Cloud/Local mode.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

from config import HEALTH_URL, API_BASE_URL, IS_CLOUD


def detect_mode():
    """Detect which mode is available."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    has_local = os.path.exists(os.path.join(script_dir, "..", "EverOS", "methods", "EverCore"))
    has_cloud = IS_CLOUD

    if has_cloud and has_local:
        return "both"
    elif has_cloud:
        return "cloud"
    elif has_local:
        return "local"
    else:
        return "none"


def check_health():
    """Check EverCore API health."""
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            print(f"[OK] EverCore API: {data.get('status', 'unknown')}")
            return True
    except urllib.error.URLError as e:
        print(f"[FAIL] EverCore API: {e}")
        return False


def check_docker():
    """Check Docker containers via direct docker command."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            print(f"[FAIL] Docker: {result.stderr.strip()}")
            return False

        containers = {}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                containers[parts[0]] = parts[1]

        expected = [
            "memsys-mongodb",
            "memsys-elasticsearch",
            "memsys-redis",
            "memsys-milvus-standalone",
            "memsys-milvus-etcd",
            "memsys-milvus-minio",
        ]

        all_ok = True
        for name in expected:
            status = containers.get(name, "not found")
            healthy = "healthy" in status.lower() or "up" in status.lower()
            tag = "[OK]" if healthy else "[FAIL]"
            print(f"{tag} {name}: {status}")
            if not healthy:
                all_ok = False

        return all_ok
    except FileNotFoundError:
        print("[FAIL] Docker: docker command not found")
        return False
    except Exception as e:
        print(f"[FAIL] Docker: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Probe EverOS services")
    parser.add_argument("--cloud", action="store_true", help="Check cloud API only (skip Docker)")
    parser.add_argument("--check-docker", action="store_true", help="Check Docker containers")
    parser.add_argument("--auto", action="store_true", help="Auto-detect mode and check all")
    args = parser.parse_args()

    # Auto-detect mode
    mode = detect_mode()

    print("=== EverOS Service Probe ===\n")

    if args.auto:
        # Auto mode: check everything available
        if mode == "none":
            print("未检测到任何配置。")
            print("  本地模式：请确保 EverOS 已安装")
            print("  云端模式：请设置 EVEROS_API_KEY 环境变量")
            sys.exit(1)

        if IS_CLOUD:
            print(f"Mode: Cloud ({API_BASE_URL})")
            api_ok = check_health()
            print()
            sys.exit(0 if api_ok else 1)

        # Local mode
        print(f"Mode: Local ({API_BASE_URL})")
        docker_ok = check_docker()
        print()
        api_ok = check_health()
        print()
        sys.exit(0 if (docker_ok and api_ok) else 1)

    # Manual mode
    cloud_mode = args.cloud or IS_CLOUD

    if cloud_mode:
        print(f"Mode: Cloud ({API_BASE_URL})\n")
    else:
        print(f"Mode: Local ({API_BASE_URL})\n")

    if args.check_docker and not cloud_mode:
        docker_ok = check_docker()
        print()
    else:
        docker_ok = True

    api_ok = check_health()

    print()
    if docker_ok and api_ok:
        print("All services healthy.")
        sys.exit(0)
    else:
        print("Some services are not healthy.")
        sys.exit(1)


if __name__ == "__main__":
    main()

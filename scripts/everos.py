"""EverOS unified CLI command.

Usage:
    everos start              Start local environment (Docker + DB + API)
    everos save [--flush]     Save current conversation to EverOS
    everos search "query"     Search memories
    everos status             Check service status
    everos config             Show current configuration
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

# Add scripts dir to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from config import (
    API_BASE_URL, API_KEY, IS_CLOUD, HEALTH_URL,
    AGENT_ADD_URL, AGENT_FLUSH_URL, SEARCH_URL,
    DEFAULT_USER_ID, HEADERS,
)


def detect_mode():
    """Detect which mode to use based on config."""
    has_local = os.path.exists(os.path.join(SCRIPT_DIR, "..", "EverOS", "methods", "EverCore"))
    has_cloud = bool(API_KEY)

    if has_cloud and has_local:
        return "both"
    elif has_cloud:
        return "cloud"
    elif has_local:
        return "local"
    else:
        return "none"


def prompt_mode_choice():
    """Ask user to choose mode when both are available."""
    print("\n检测到两种部署模式：")
    print("  [1] 本地模式 (Local)")
    print("  [2] 云端模式 (Cloud)")
    while True:
        choice = input("\n请选择 (1/2): ").strip()
        if choice == "1":
            return "local"
        elif choice == "2":
            return "cloud"
        print("无效输入，请输入 1 或 2")


def get_mode():
    """Get the mode to use, prompting user if needed."""
    mode = detect_mode()
    if mode == "both":
        return prompt_mode_choice()
    elif mode == "cloud":
        return "cloud"
    elif mode == "local":
        return "local"
    else:
        print("错误：未检测到任何配置。")
        print("  本地模式：请确保 EverOS 已安装")
        print("  云端模式：请设置 EVEROS_API_KEY 环境变量")
        sys.exit(1)


# === start command ===

def is_docker_running():
    """Check if Docker daemon is responding."""
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def start_docker_desktop():
    """Try to launch Docker Desktop and wait for it to be ready."""
    # Find Docker Desktop executable
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Docker\Docker\Docker Desktop.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe"),
    ]
    docker_exe = None
    for c in candidates:
        if os.path.exists(c):
            docker_exe = c
            break

    if not docker_exe:
        print("错误：找不到 Docker Desktop。请手动安装 Docker Desktop。")
        print("  下载地址: https://docs.docker.com/get-docker/")
        sys.exit(1)

    print(f"正在启动 Docker Desktop...")
    subprocess.Popen([docker_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for Docker daemon to be ready
    print("等待 Docker 就绪", end="", flush=True)
    for i in range(60):  # max 60 seconds
        if is_docker_running():
            print(" 就绪!")
            return True
        print(".", end="", flush=True)
        time.sleep(1)

    print("\n错误：Docker Desktop 启动超时（60秒）。请检查 Docker Desktop 状态。")
    sys.exit(1)


def cmd_start(args):
    """Start local EverOS environment."""
    mode = get_mode()
    if mode == "cloud":
        print("云端模式无需启动本地服务。")
        print(f"API 地址: {API_BASE_URL}")
        return

    # Local mode - start Docker and API
    repo_dir = os.path.join(SCRIPT_DIR, "..", "EverOS")
    evercore_dir = os.path.join(repo_dir, "methods", "EverCore")

    if not os.path.isdir(evercore_dir):
        print("错误：EverOS 未安装。运行 auto_setup.py 先安装。")
        sys.exit(1)

    # Ensure Docker is running (auto-start if needed)
    if not is_docker_running():
        start_docker_desktop()

    # Start databases
    print("启动数据库...")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=evercore_dir, check=True)
    print("数据库已启动")

    # Start EverCore API
    print("启动 EverCore API...")
    proc = subprocess.Popen(
        ["uv", "run", "python", "src/run.py"],
        cwd=evercore_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(f"EverCore API 启动中 (PID {proc.pid})")

    # Wait for health
    print("等待服务就绪...")
    for i in range(15):
        try:
            req = urllib.request.Request(HEALTH_URL, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                print(f"服务就绪: {resp.read().decode()}")
                return
        except (urllib.error.URLError, OSError):
            time.sleep(2)

    print("警告：API 可能还在启动中，请稍后检查状态。")


# === save command ===

def cmd_save(args):
    """Save conversation to EverOS."""
    mode = get_mode()

    # Read messages from stdin or argument
    if args.messages:
        raw_messages = args.messages
    else:
        print("请输入对话内容 (JSON 格式，按 Ctrl+D 结束):")
        raw_messages = sys.stdin.read()

    try:
        raw = json.loads(raw_messages)
    except json.JSONDecodeError as e:
        print(f"错误：无效的 JSON 格式: {e}", file=sys.stderr)
        sys.exit(1)

    # Build messages
    messages = []
    now_ms = int(time.time() * 1000)
    for i, msg in enumerate(raw):
        role = msg.get("role")
        content = msg.get("content", "")
        if not role or not content:
            continue
        messages.append({
            "role": role,
            "timestamp": now_ms + i * 1000,
            "content": content,
        })

    if not messages:
        print("错误：没有有效消息", file=sys.stderr)
        sys.exit(1)

    user_id = args.user_id or DEFAULT_USER_ID
    session_id = args.session_id

    payload = {"user_id": user_id, "messages": messages}
    if session_id:
        payload["session_id"] = session_id

    # POST to API
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(AGENT_ADD_URL, data=body, headers=HEADERS, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"错误：保存失败: {e}", file=sys.stderr)
        sys.exit(1)

    data = result.get("data", {})
    print(f"已保存 {data.get('message_count', 0)} 条消息")

    # Flush if requested
    if args.flush:
        flush_payload = {"user_id": user_id}
        if session_id:
            flush_payload["session_id"] = session_id

        flush_body = json.dumps(flush_payload, ensure_ascii=False).encode("utf-8")
        flush_req = urllib.request.Request(AGENT_FLUSH_URL, data=flush_body, headers=HEADERS, method="POST")

        try:
            with urllib.request.urlopen(flush_req, timeout=300) as resp:
                result = json.loads(resp.read())
                data = result.get("data", {})
                print(f"Flush 状态: {data.get('status', 'unknown')}")
        except urllib.error.URLError as e:
            print(f"警告：Flush 触发失败: {e}")


# === search command ===

def cmd_search(args):
    """Search memories in EverOS."""
    mode = get_mode()

    types = [t.strip() for t in args.memory_types.split(",")]

    payload = {
        "query": args.query,
        "method": args.method,
        "memory_types": types,
        "top_k": args.top_k,
        "filters": {"user_id": args.user_id or DEFAULT_USER_ID},
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(SEARCH_URL, data=body, headers=HEADERS, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"错误：搜索失败: {e}", file=sys.stderr)
        sys.exit(1)

    data = result.get("data", {})
    episodes = data.get("episodes", [])
    profiles = data.get("profiles", [])
    agent_mem = data.get("agent_memory")

    print(f"找到 {len(episodes)} 条记录, {len(profiles)} 个配置")

    for ep in episodes:
        print(f"\n[记录] {ep.get('subject', 'N/A')}")
        print(f"  摘要: {ep.get('summary', 'N/A')[:200]}")
        print(f"  分数: {ep.get('score', 'N/A')}")

    for p in profiles:
        print(f"\n[配置] user={p.get('user_id')}")
        print(f"  数据: {json.dumps(p.get('profile_data', {}), ensure_ascii=False)[:200]}")

    if agent_mem:
        for c in agent_mem.get("cases", []):
            print(f"\n[案例] {c.get('task_intent', 'N/A')[:100]}")
        for s in agent_mem.get("skills", []):
            print(f"\n[技能] {s.get('name', 'N/A')}")


# === status command ===

def cmd_status(args):
    """Check EverOS service status."""
    mode = detect_mode()

    print("=== EverOS 服务状态 ===\n")

    if mode == "none":
        print("未检测到任何配置。")
        print("  本地模式：请确保 EverOS 已安装")
        print("  云端模式：请设置 EVEROS_API_KEY 环境变量")
        return

    # Check cloud if configured
    if API_KEY:
        print(f"云端模式: {API_BASE_URL}")
        try:
            req = urllib.request.Request(HEALTH_URL, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"  状态: 正常")
        except urllib.error.URLError as e:
            print(f"  状态: 失败 - {e}")

    # Check local if configured
    repo_dir = os.path.join(SCRIPT_DIR, "..", "EverOS")
    if os.path.isdir(os.path.join(repo_dir, "methods", "EverCore")):
        print(f"\n本地模式: {API_BASE_URL}")

        # Check Docker
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                containers = {}
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split("\t", 1)
                        if len(parts) == 2:
                            containers[parts[0]] = parts[1]

                expected = ["memsys-mongodb", "memsys-elasticsearch", "memsys-redis",
                           "memsys-milvus-standalone", "memsys-milvus-etcd", "memsys-milvus-minio"]

                for name in expected:
                    status = containers.get(name, "未运行")
                    healthy = "healthy" in status.lower() or "up" in status.lower()
                    tag = "正常" if healthy else "异常"
                    print(f"  {name}: {tag}")
            else:
                print("  Docker: 无法获取状态")
        except FileNotFoundError:
            print("  Docker: 未安装")

        # Check API
        try:
            req = urllib.request.Request(HEALTH_URL, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"  EverCore API: 正常")
        except urllib.error.URLError:
            print("  EverCore API: 未运行")


# === config command ===

def cmd_config(args):
    """Show current configuration."""
    mode = detect_mode()

    print("=== EverOS 配置 ===\n")
    print(f"检测模式: {mode}")
    print(f"API 地址: {API_BASE_URL}")
    print(f"Cloud Key: {'已配置' if API_KEY else '未配置'}")

    repo_dir = os.path.join(SCRIPT_DIR, "..", "EverOS")
    print(f"本地安装: {'是' if os.path.isdir(os.path.join(repo_dir, 'methods', 'EverCore')) else '否'}")


# === test command ===

def cmd_test(args):
    """Run all-in-one test."""
    test_script = os.path.join(SCRIPT_DIR, "test.py")
    subprocess.run([sys.executable, "-X", "utf8", test_script])


# === install command ===

def cmd_install(args):
    """Install skill to Claude Code settings."""
    setup_script = os.path.join(SCRIPT_DIR, "setup_skill.py")
    cmd = [sys.executable, "-X", "utf8", setup_script]
    if args.global_:
        cmd.append("--global")
    elif args.project:
        cmd.append("--project")
    subprocess.run(cmd)


def cmd_uninstall(args):
    """Uninstall skill from Claude Code settings."""
    setup_script = os.path.join(SCRIPT_DIR, "setup_skill.py")
    cmd = [sys.executable, "-X", "utf8", setup_script, "--uninstall"]
    if args.scope:
        cmd.append(args.scope)
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="EverOS 统一命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  everos install                  安装 skill 到 Claude Code
  everos start                    启动本地环境
  everos test                     一键测试所有功能
  everos save --messages '[...]'  保存对话
  everos search "关键词"           搜索记忆
  everos status                   检查状态
  everos config                   查看配置
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # install
    install_parser = subparsers.add_parser("install", help="安装 skill 到 Claude Code")
    install_group = install_parser.add_mutually_exclusive_group()
    install_group.add_argument("--global", action="store_true", dest="global_", help="安装到全局")
    install_group.add_argument("--project", action="store_true", help="安装到当前项目")

    # uninstall
    uninstall_parser = subparsers.add_parser("uninstall", help="从 Claude Code 移除 skill")
    uninstall_parser.add_argument("scope", nargs="?", choices=["global", "project", "all"],
                                  help="移除范围")

    # start
    subparsers.add_parser("start", help="启动本地环境")

    # save
    save_parser = subparsers.add_parser("save", help="保存对话到 EverOS")
    save_parser.add_argument("--messages", help="JSON 格式的对话内容")
    save_parser.add_argument("--user-id", help="用户 ID")
    save_parser.add_argument("--session-id", help="会话 ID")
    save_parser.add_argument("--flush", action="store_true", help="触发记忆提取")

    # search
    search_parser = subparsers.add_parser("search", help="搜索历史记忆")
    search_parser.add_argument("query", help="搜索关键词")
    search_parser.add_argument("--method", default="keyword",
                              choices=["keyword", "vector", "hybrid", "agentic"],
                              help="检索方式")
    search_parser.add_argument("--top-k", type=int, default=10, help="返回数量")
    search_parser.add_argument("--user-id", help="用户 ID")
    search_parser.add_argument("--memory-types", default="episodic_memory",
                              help="记忆类型，逗号分隔")

    # status
    subparsers.add_parser("status", help="检查服务状态")

    # config
    subparsers.add_parser("config", help="查看配置")

    # test
    subparsers.add_parser("test", help="一键测试所有功能")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "start": cmd_start,
        "save": cmd_save,
        "search": cmd_search,
        "status": cmd_status,
        "config": cmd_config,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "test": cmd_test,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()

"""EverOS Local Mode Auto Setup.

Clones EverOS, starts Docker databases, installs dependencies,
configures .env, and launches EverCore API.

Usage:
    python auto_setup.py [--repo-dir DIR] [--skip-clone]
"""

import argparse
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO_DIR = os.path.join(SCRIPT_DIR, "..", "EverOS")
EVERCORE_DIR = "methods/EverCore"


def run(cmd, cwd=None, check=True):
    """Run a shell command and print it."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check)


def check_tool(name):
    """Check if a CLI tool is available."""
    return shutil.which(name) is not None


def ensure_docker():
    if not check_tool("docker"):
        print("[ERROR] Docker is not installed. Install Docker first:")
        print("  https://docs.docker.com/get-docker/")
        sys.exit(1)
    print("[OK] Docker found")


def ensure_uv():
    if check_tool("uv"):
        print("[OK] uv found")
        return
    print("[INFO] Installing uv...")
    if sys.platform == "win32":
        run(["powershell", "-c", "irm https://astral.sh/uv/install.ps1 | iex"], check=False)
    else:
        run(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"], check=False)
    if not check_tool("uv"):
        print("[ERROR] uv installation failed. Install manually: https://docs.astral.sh/uv/")
        sys.exit(1)
    print("[OK] uv installed")


def clone_repo(repo_dir):
    if os.path.exists(os.path.join(repo_dir, ".git")):
        print(f"[OK] Repo already exists at {repo_dir}")
        return
    print(f"[INFO] Cloning EverOS to {repo_dir}...")
    run(["git", "clone", "https://github.com/EverMind-AI/EverOS.git", repo_dir])


def start_databases(evercore_dir):
    print("[INFO] Starting Docker databases...")
    run(["docker", "compose", "up", "-d"], cwd=evercore_dir)
    print("[OK] Docker databases started")


def configure_env(evercore_dir):
    env_file = os.path.join(evercore_dir, ".env")
    template = os.path.join(evercore_dir, "env.template")

    if os.path.exists(env_file):
        print("[OK] .env already exists, skipping")
        return

    if not os.path.exists(template):
        print("[WARN] env.template not found, skipping .env configuration")
        return

    print("\n[CONFIG] .env configuration needed")
    print("  You need at least an LLM API key for memory extraction.\n")

    llm_key = input("  LLM API Key (OpenRouter, or press Enter to skip): ").strip()
    embed_key = input("  Vectorize API Key (DeepInfra, or press Enter to skip): ").strip()

    with open(template, "r", encoding="utf-8") as f:
        content = f.read()

    if llm_key:
        content = content.replace("OPENROUTER_API_KEY=your-openrouter-api-key", f"OPENROUTER_API_KEY={llm_key}")
        content = content.replace("LLM_API_KEY=your-llm-api-key", f"LLM_API_KEY={llm_key}")
        content = content.replace("LLM_API_KEY=" + "sk-or-v1-" + "xxxx", f"LLM_API_KEY={llm_key}")
    if embed_key:
        content = content.replace("VECTORIZE_FALLBACK_API_KEY=xxxxx", f"VECTORIZE_FALLBACK_API_KEY={embed_key}")

    with open(env_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("[OK] .env configured")


def install_deps(evercore_dir):
    print("[INFO] Installing Python dependencies...")
    run(["uv", "sync"], cwd=evercore_dir)
    print("[OK] Dependencies installed")


def start_server(evercore_dir):
    print("[INFO] Starting EverCore API server...")
    proc = subprocess.Popen(
        ["uv", "run", "python", "src/run.py"],
        cwd=evercore_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[OK] EverCore API starting (PID {proc.pid})")
    print("     Server will be at http://localhost:1995")
    print("     Check logs with: docker compose logs -f")
    return proc


def verify_services():
    """Quick health check."""
    import time
    import urllib.request
    import urllib.error

    print("[INFO] Waiting for services to be ready...")
    for i in range(15):
        try:
            req = urllib.request.Request("http://localhost:1995/health", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                print(f"[OK] EverCore API healthy: {resp.read().decode()}")
                return True
        except (urllib.error.URLError, OSError):
            time.sleep(2)
    print("[WARN] API not ready yet — it may still be starting. Check logs.")
    return False


def main():
    parser = argparse.ArgumentParser(description="EverOS Local Auto Setup")
    parser.add_argument("--repo-dir", default=DEFAULT_REPO_DIR, help="Path to EverOS repo")
    parser.add_argument("--skip-clone", action="store_true", help="Skip git clone")
    args = parser.parse_args()

    repo_dir = os.path.abspath(args.repo_dir)
    evercore_dir = os.path.join(repo_dir, EVERCORE_DIR)

    print("=== EverOS Local Setup ===\n")

    # 1. Check prerequisites
    ensure_docker()
    ensure_uv()

    # 2. Clone repo
    if not args.skip_clone:
        clone_repo(repo_dir)

    if not os.path.isdir(evercore_dir):
        print(f"[ERROR] EverCore not found at {evercore_dir}")
        sys.exit(1)

    # 3. Start databases
    start_databases(evercore_dir)

    # 4. Configure .env
    configure_env(evercore_dir)

    # 5. Install dependencies
    install_deps(evercore_dir)

    # 6. Start server
    start_server(evercore_dir)

    # 7. Verify
    verify_services()

    print("\n=== Setup Complete ===")
    print("  API: http://localhost:1995")
    print("  Diagnose: python -X utf8 scripts/everos.py doctor")
    print("  Start: python -X utf8 scripts/everos.py start")
    print("  Status: python -X utf8 scripts/everos.py status")
    print("  Stop: python -X utf8 scripts/everos.py stop")


if __name__ == "__main__":
    main()

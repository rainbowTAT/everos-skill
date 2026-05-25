"""EverOS Memory Skill configuration.

Supports two deployment modes:
  - Cloud: set EVEROS_API_KEY (uses https://api.evermind.ai)
  - Local: default (uses http://localhost:1995, no auth needed)
"""

import os

CLOUD_URL = "https://api.evermind.ai"

API_KEY = os.getenv("EVEROS_API_KEY", "")
API_BASE_URL = os.getenv("EVEROS_API_URL", CLOUD_URL if API_KEY else "http://localhost:1995")
API_V1 = f"{API_BASE_URL}/api/v1"

# Endpoints
AGENT_ADD_URL = f"{API_V1}/memories/agent"
AGENT_FLUSH_URL = f"{API_V1}/memories/agent/flush"
SEARCH_URL = f"{API_V1}/memories/search"
HEALTH_URL = f"{API_BASE_URL}/health"

DEFAULT_USER_ID = "claude_code_user"

# Headers — includes Authorization when using cloud
HEADERS = {"Content-Type": "application/json; charset=utf-8"}
if API_KEY:
    HEADERS["Authorization"] = f"Bearer {API_KEY}"

# Mode detection
IS_CLOUD = bool(API_KEY)

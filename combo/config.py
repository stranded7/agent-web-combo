from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=_PROJECT_ROOT / ".env")
except Exception:  # pragma: no cover
    pass


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def get_tavily_key() -> str:
    return _env("TAVILY_API_KEY")


def get_exa_key() -> str:
    return _env("EXA_API_KEY")


def get_anysearch_key() -> str:
    return _env("ANYSEARCH_API_KEY")


def get_kitesurf_config() -> dict:
    """Return Kitesurf CDP connection config.

    Prefer KITESURF_WS_ENDPOINT if set; otherwise build it from
    CF_ACCOUNT_ID and CF_API_TOKEN.
    """
    endpoint = _env("KITESURF_WS_ENDPOINT")
    account_id = _env("CF_ACCOUNT_ID")
    api_token = _env("CF_API_TOKEN")

    if not endpoint and account_id:
        endpoint = (
            f"wss://api.cloudflare.com/client/v4/accounts/{account_id}"
            "/browser-run/devtools/browser?browser=kitesurf"
        )

    return {
        "endpoint": endpoint,
        "account_id": account_id,
        "api_token": api_token,
        "configured": bool(endpoint and api_token),
    }


def get_agent_reach_cmd() -> str:
    return _env("AGENT_REACH_CMD") or "agent-reach"

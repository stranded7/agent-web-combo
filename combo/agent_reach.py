from __future__ import annotations

import shutil
import subprocess

from .config import get_agent_reach_cmd


def is_installed() -> bool:
    return shutil.which(get_agent_reach_cmd()) is not None


def run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Run agent-reach CLI (or a configured replacement)."""
    cmd = get_agent_reach_cmd()
    if not shutil.which(cmd):
        raise FileNotFoundError(
            "agent-reach CLI not found on PATH. Install it first: pip install agent-reach"
        )
    return subprocess.run(
        [cmd, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def doctor() -> str:
    proc = run("doctor")
    return proc.stdout or proc.stderr

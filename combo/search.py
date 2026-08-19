from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import requests

from .config import get_anysearch_key, get_exa_key, get_tavily_key


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = "unknown"
    raw: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Tavily
# ---------------------------------------------------------------------------
def search_tavily(query: str, max_results: int = 5, api_key: str | None = None) -> list[SearchResult]:
    key = api_key or get_tavily_key()
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not configured")

    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": False,
    }
    resp = requests.post(
        "https://api.tavily.com/search",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    results: list[SearchResult] = []
    for item in data.get("results", []):
        results.append(
            SearchResult(
                title=item.get("title") or item.get("url") or "",
                url=item.get("url", ""),
                snippet=item.get("content") or "",
                source="tavily",
                raw=item,
            )
        )
    return results


def tavily_extract(url: str, api_key: str | None = None) -> str:
    key = api_key or get_tavily_key()
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not configured")
    resp = requests.post(
        "https://api.tavily.com/extract",
        json={"urls": [url]},
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results") or []
    if results:
        return results[0].get("raw_content") or results[0].get("content") or ""
    return ""


# ---------------------------------------------------------------------------
# Exa
# ---------------------------------------------------------------------------
def search_exa(query: str, max_results: int = 5, api_key: str | None = None) -> list[SearchResult]:
    key = api_key or get_exa_key()
    if not key:
        raise RuntimeError("EXA_API_KEY is not configured")

    payload = {
        "query": query,
        "numResults": max_results,
        "contents": {"highlights": True},
    }
    resp = requests.post(
        "https://api.exa.ai/search",
        json=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    results: list[SearchResult] = []
    for item in data.get("results", []):
        highlights = item.get("highlights") or []
        results.append(
            SearchResult(
                title=item.get("title") or item.get("url") or "",
                url=item.get("url", ""),
                snippet="\n".join(highlights) if highlights else (item.get("text") or ""),
                source="exa",
                raw=item,
            )
        )
    return results


def exa_extract(url: str, api_key: str | None = None) -> str:
    key = api_key or get_exa_key()
    if not key:
        raise RuntimeError("EXA_API_KEY is not configured")
    resp = requests.post(
        "https://api.exa.ai/contents",
        json={"ids": [url], "text": {"maxCharacters": 50000}},
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results") or []
    if results:
        return results[0].get("text") or ""
    return ""


# ---------------------------------------------------------------------------
# AnySearch (MCP tools/call over Streamable HTTP)
# ---------------------------------------------------------------------------
ANYSEARCH_ENDPOINT = "https://api.anysearch.com/mcp"


def _anysearch_call(name: str, arguments: dict[str, Any], api_key: str | None = None) -> Any:
    key = api_key if api_key is not None else get_anysearch_key()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Anysearch-Client": "agent-web-combo/0.1.0",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    resp = requests.post(ANYSEARCH_ENDPOINT, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"AnySearch error: {data['error']}")
    result = data.get("result", {})
    if result.get("isError"):
        raise RuntimeError(f"AnySearch tool error: {result}")
    content = result.get("content") or []
    text = "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
    return text


def _parse_anysearch_markdown(text: str) -> list[SearchResult]:
    """Parse AnySearch's markdown search output into SearchResult objects."""
    results: list[SearchResult] = []
    blocks = re.split(r"\n###\s+\d+\.\s+", "\n" + text.strip())
    for block in blocks[1:]:
        title_line = block.splitlines()[0].strip() if block.splitlines() else ""
        url_match = re.search(r"\*\*URL\*\*:\s*(\S+)", block)
        if not url_match:
            continue
        # Remove the URL line and any "Source" line for the snippet.
        snippet_lines = []
        for line in block.splitlines()[1:]:
            stripped = line.strip()
            if "**URL**" in stripped or "**Source**" in stripped:
                continue
            snippet_lines.append(stripped)
        snippet = "\n".join(snippet_lines).strip()
        results.append(
            SearchResult(
                title=title_line,
                url=url_match.group(1),
                snippet=snippet[:2000],
                source="anysearch",
            )
        )
    return results


def search_anysearch(query: str, max_results: int = 5, api_key: str | None = None) -> list[SearchResult]:
    text = _anysearch_call(
        "search",
        {"query": query, "max_results": max_results},
        api_key=api_key,
    )
    parsed = _parse_anysearch_markdown(text)
    if parsed:
        return parsed
    # Fallback: if the markdown parser didn't find anything, return raw text as one result.
    return [SearchResult(title=query, url="", snippet=text[:2000], source="anysearch")]


def anysearch_extract(url: str, api_key: str | None = None) -> str:
    return _anysearch_call("extract", {"url": url}, api_key=api_key)


# ---------------------------------------------------------------------------
# Provider registry / auto select
# ---------------------------------------------------------------------------
SEARCH_PROVIDERS = {
    "tavily": search_tavily,
    "exa": search_exa,
    "anysearch": search_anysearch,
}


def available_providers() -> list[str]:
    providers = []
    if get_tavily_key():
        providers.append("tavily")
    if get_exa_key():
        providers.append("exa")
    # AnySearch works anonymously, so it is always available.
    providers.append("anysearch")
    return providers


def search(query: str, provider: str = "auto", max_results: int = 5) -> list[SearchResult]:
    if provider == "auto":
        providers = available_providers()
        if not providers:
            raise RuntimeError("No search provider configured (AnySearch should always be available)")
        provider = providers[0]

    if provider not in SEARCH_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Choose from {list(SEARCH_PROVIDERS)}")

    return SEARCH_PROVIDERS[provider](query, max_results=max_results)

from __future__ import annotations

from dataclasses import dataclass

from . import kitesurf, search as search_mod
from .search import SearchResult


@dataclass
class ResearchItem:
    result: SearchResult
    extracted: str = ""
    rendered_title: str = ""
    rendered_text: str = ""
    screenshot: str | None = None


@dataclass
class ResearchOutput:
    query: str
    provider: str
    items: list[ResearchItem]


def research(
    query: str,
    *,
    provider: str = "auto",
    max_results: int = 5,
    render: bool = False,
    render_limit: int = 3,
    extract: bool = False,
    screenshot_dir: str | None = None,
) -> ResearchOutput:
    """Search first, then optionally extract/render top results with Kitesurf."""
    results = search_mod.search(query, provider=provider, max_results=max_results)
    limit = render_limit if render else len(results)
    items: list[ResearchItem] = []

    for result in results[:limit]:
        item = ResearchItem(result=result)
        if extract:
            try:
                item.extracted = _extract_with_any_provider(result.url)
            except Exception as exc:
                item.extracted = f"[extract failed: {exc}]"

        if render:
            try:
                if screenshot_dir:
                    safe = _safe_name(result.url)
                    shot = f"{screenshot_dir}/{safe}.png"
                else:
                    shot = None
                page = kitesurf.render_page(result.url, screenshot_path=shot)
                item.rendered_title = page.title
                item.rendered_text = page.text
                item.screenshot = page.screenshot_path
            except Exception as exc:
                item.rendered_text = f"[kitesurf render failed: {exc}]"

        items.append(item)

    return ResearchOutput(query=query, provider=provider, items=items)


def _extract_with_any_provider(url: str) -> str:
    """Try AnySearch extract (anonymous-friendly) first, then provider-specific."""
    try:
        text = search_mod.anysearch_extract(url)
        if text.strip():
            return text
    except Exception:
        pass

    for fn in (search_mod.tavily_extract, search_mod.exa_extract):
        try:
            text = fn(url)
            if text.strip():
                return text
        except Exception:
            continue
    return ""


def _safe_name(url: str) -> str:
    return (
        url.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "_")
        .replace("#", "_")[:120]
        or "page"
    )

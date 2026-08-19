"""MCP server exposing the agent-web-combo tools.

Run with:
    python -m combo_mcp
or:
    python combo_mcp.py
"""
from __future__ import annotations

import asyncio
import json

from mcp.server.mcpserver import MCPServer

from combo import kitesurf, search
from combo.agent_reach import doctor as agent_reach_doctor
from combo.agent_reach import is_installed as agent_reach_is_installed
from combo.pipeline import research


server = MCPServer(
    name="agent-web-combo",
    title="Agent Web Combo",
    version="0.1.0",
    description=(
        "Search APIs (Tavily/Exa/AnySearch) + Kitesurf/Playwright rendering "
        "+ agent-reach platform access."
    ),
)


def _format_results(results: list[search.SearchResult]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.title}")
        lines.append(f"   URL: {r.url}")
        if r.snippet:
            lines.append(f"   Snippet: {r.snippet[:500]}")
    return "\n".join(lines) or "No results."


@server.tool(
    name="combo_search",
    description=(
        "Search the web using Tavily, Exa, or AnySearch. "
        "Returns ranked results with title, URL, and snippet."
    ),
)
async def combo_search(
    query: str,
    provider: str = "auto",
    max_results: int = 5,
) -> str:
    try:
        results = await asyncio.to_thread(
            search.search,
            query,
            provider=provider,
            max_results=max_results,
        )
        return _format_results(results)
    except Exception as exc:
        return f"Error: {exc}"


@server.tool(
    name="combo_render",
    description=(
        "Render a URL with Kitesurf via Playwright CDP. "
        "Returns page title, body text, and optional screenshot path."
    ),
)
async def combo_render(
    url: str,
    screenshot_path: str | None = None,
    max_chars: int = 20000,
) -> str:
    try:
        page = await asyncio.to_thread(
            kitesurf.render_page,
            url,
            screenshot_path=screenshot_path,
            text_max_chars=max_chars,
        )
        parts = [
            f"URL: {page.url}",
            f"Title: {page.title}",
        ]
        if page.screenshot_path:
            parts.append(f"Screenshot: {page.screenshot_path}")
        parts.append("")
        parts.append(page.text)
        return "\n".join(parts)
    except Exception as exc:
        return f"Error: {exc}"


@server.tool(
    name="combo_research",
    description=(
        "Full pipeline: search, optionally extract page content, "
        "optionally render with Kitesurf and save screenshots."
    ),
)
async def combo_research(
    query: str,
    provider: str = "auto",
    max_results: int = 5,
    extract: bool = False,
    render: bool = False,
    render_limit: int = 3,
    screenshot_dir: str | None = None,
) -> str:
    try:
        output = await asyncio.to_thread(
            research,
            query,
            provider=provider,
            max_results=max_results,
            extract=extract,
            render=render,
            render_limit=render_limit,
            screenshot_dir=screenshot_dir,
        )
        lines = [
            f"Query: {output.query}",
            f"Provider: {output.provider}",
            f"Results: {len(output.items)}",
            "",
        ]
        for idx, item in enumerate(output.items, 1):
            r = item.result
            lines.append(f"[{idx}] {r.title}")
            lines.append(f"    URL: {r.url}")
            if item.extracted:
                lines.append(f"    Extracted: {item.extracted[:300]}")
            if item.rendered_title:
                lines.append(f"    Rendered title: {item.rendered_title}")
            if item.rendered_text:
                lines.append(f"    Rendered text: {item.rendered_text[:300]}")
            if item.screenshot:
                lines.append(f"    Screenshot: {item.screenshot}")
            lines.append("")
        return "\n".join(lines)
    except Exception as exc:
        return f"Error: {exc}"


@server.tool(
    name="combo_agent_reach_doctor",
    description=(
        "Run agent-reach doctor to check the status of local internet "
        "channels (GitHub, YouTube, Bilibili, Twitter, Xiaohongshu, etc.)."
    ),
)
async def combo_agent_reach_doctor() -> str:
    if not agent_reach_is_installed():
        return "agent-reach CLI is not installed. Run: pip install agent-reach"
    try:
        return await asyncio.to_thread(agent_reach_doctor)
    except Exception as exc:
        return f"Error: {exc}"


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import sys

from . import kitesurf, search
from .agent_reach import doctor as agent_reach_doctor
from .agent_reach import is_installed as agent_reach_is_installed
from .pipeline import research


def _print_results(results: list[search.SearchResult]) -> None:
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.title}")
        print(f"   URL: {r.url}")
        if r.snippet:
            snippet = r.snippet.replace("\n", " ")[:300]
            print(f"   Snippet: {snippet}")
        print()


def cmd_search(args: argparse.Namespace) -> int:
    results = search.search(args.query, provider=args.provider, max_results=args.max_results)
    _print_results(results)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    page = kitesurf.render_page(args.url, screenshot_path=args.screenshot)
    print(f"URL:  {page.url}")
    print(f"Title: {page.title}")
    if page.screenshot_path:
        print(f"Screenshot: {page.screenshot_path}")
    print()
    print(page.text[: args.max_chars])
    return 0


def cmd_research(args: argparse.Namespace) -> int:
    output = research(
        args.query,
        provider=args.provider,
        max_results=args.max_results,
        render=args.render,
        render_limit=args.render_limit,
        extract=args.extract,
        screenshot_dir=args.screenshot_dir,
    )
    print(f"Query: {output.query}")
    print(f"Provider: {output.provider}")
    print(f"Results: {len(output.items)}\n")
    for idx, item in enumerate(output.items, 1):
        r = item.result
        print(f"[{idx}] {r.title}")
        print(f"    URL: {r.url}")
        if item.extracted:
            print(f"    Extracted: {item.extracted[:300].replace(chr(10), ' ')}")
        if item.rendered_title:
            print(f"    Rendered title: {item.rendered_title}")
        if item.rendered_text:
            print(f"    Rendered text: {item.rendered_text[:300].replace(chr(10), ' ')}")
        if item.screenshot:
            print(f"    Screenshot: {item.screenshot}")
        print()
    return 0


def cmd_agent_reach(args: argparse.Namespace) -> int:
    if not agent_reach_is_installed():
        print("agent-reach CLI is not installed. Run: pip install agent-reach", file=sys.stderr)
        return 1
    print(agent_reach_doctor())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="combo",
        description="Search APIs + Kitesurf/Playwright + agent-reach combo",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search with Tavily/Exa/AnySearch")
    p_search.add_argument("query")
    p_search.add_argument("--provider", default="auto", choices=["auto", "tavily", "exa", "anysearch"])
    p_search.add_argument("--max-results", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    p_render = sub.add_parser("render", help="Render a URL with Kitesurf + Playwright")
    p_render.add_argument("url")
    p_render.add_argument("--screenshot")
    p_render.add_argument("--max-chars", type=int, default=20000)
    p_render.set_defaults(func=cmd_render)

    p_research = sub.add_parser("research", help="Search then optionally render with Kitesurf")
    p_research.add_argument("query")
    p_research.add_argument("--provider", default="auto", choices=["auto", "tavily", "exa", "anysearch"])
    p_research.add_argument("--max-results", type=int, default=5)
    p_research.add_argument("--render", action="store_true", help="Render top results with Kitesurf")
    p_research.add_argument("--render-limit", type=int, default=3)
    p_research.add_argument("--extract", action="store_true", help="Extract page text via AnySearch/Tavily/Exa")
    p_research.add_argument("--screenshot-dir", help="Save screenshots to this directory")
    p_research.set_defaults(func=cmd_research)

    p_agent = sub.add_parser("agent-reach", help="Check agent-reach CLI status")
    p_agent.set_defaults(func=cmd_agent_reach)

    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

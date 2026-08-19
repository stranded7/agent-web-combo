from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from .config import get_kitesurf_config


@dataclass
class RenderedPage:
    url: str
    title: str
    text: str
    screenshot_path: str | None = None


def is_configured() -> bool:
    return get_kitesurf_config()["configured"]


def quick_screenshot(url: str, screenshot_path: str) -> str:
    """Fallback screenshot via Browser Run Quick Actions (works with Kitesurf)."""
    cfg = get_kitesurf_config()
    if not cfg["configured"]:
        raise RuntimeError("Kitesurf is not configured")
    if not cfg.get("account_id"):
        raise RuntimeError("CF_ACCOUNT_ID is required for Quick Actions screenshot fallback")
    endpoint = (
        f"https://api.cloudflare.com/client/v4/accounts/{cfg['account_id']}"
        "/browser-run/screenshot?browser=kitesurf"
    )
    resp = requests.post(
        endpoint,
        json={"url": url},
        headers={"Authorization": f"Bearer {cfg['api_token']}", "Content-Type": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    os.makedirs(os.path.dirname(os.path.abspath(screenshot_path)), exist_ok=True)
    with open(screenshot_path, "wb") as f:
        f.write(resp.content)
    return screenshot_path


def render_page(
    url: str,
    *,
    screenshot_path: str | None = None,
    wait_ms: int = 2000,
    text_max_chars: int = 20000,
) -> RenderedPage:
    """Open a page in Kitesurf via Playwright CDP and return title/text/screenshot.

    Requires a Cloudflare account with Browser Run enabled and Kitesurf in beta.
    """
    cfg = get_kitesurf_config()
    if not cfg["configured"]:
        raise RuntimeError(
            "Kitesurf is not configured. Set CF_ACCOUNT_ID and CF_API_TOKEN "
            "(or KITESURF_WS_ENDPOINT + CF_API_TOKEN)."
        )

    from playwright.sync_api import sync_playwright

    headers = {"Authorization": f"Bearer {cfg['api_token']}"} if cfg["api_token"] else {}

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cfg["endpoint"], headers=headers)
        try:
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(wait_ms)

            title = page.title()
            text = ""
            try:
                text = page.inner_text("body")
            except Exception:
                text = ""

            shot = None
            if screenshot_path:
                try:
                    os.makedirs(os.path.dirname(os.path.abspath(screenshot_path)), exist_ok=True)
                    page.screenshot(path=screenshot_path, full_page=False)
                    shot = screenshot_path
                except Exception:
                    # Kitesurf's CDP screenshot is not always supported; use Quick Actions.
                    shot = quick_screenshot(url, screenshot_path)

            return RenderedPage(
                url=url,
                title=title,
                text=text[:text_max_chars],
                screenshot_path=shot,
            )
        finally:
            # For CDP-connected browsers, close() disconnects the session.
            browser.close()

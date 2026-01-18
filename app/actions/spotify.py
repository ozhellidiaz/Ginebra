import asyncio
from typing import Optional

from playwright.async_api import Page


async def _try_click(page: Page, selectors: list[str], timeout_ms: int = 3000) -> bool:
    for sel in selectors:
        try:
            await page.click(sel, timeout=timeout_ms)
            return True
        except Exception:
            continue
    return False


async def ensure_logged_in(page: Page) -> bool:
    """Best-effort detection: returns True if user seems logged in."""
    # Spotify changes often; this is heuristic.
    try:
        await page.wait_for_timeout(500)
        # If "Log in" button exists, probably not logged.
        loc = page.locator("text=Log in")
        if await loc.count() > 0:
            return False
    except Exception:
        pass
    return True


async def play(page: Page, query: str) -> None:
    # Open Search
    await page.goto("https://open.spotify.com/search", wait_until="domcontentloaded")
    # Search input changes; try a few selectors
    input_selectors = [
        "input[data-testid='search-input']",
        "input[placeholder*='What do you want to play']",
        "input[placeholder*='¿Qué quieres escuchar']",
        "input[type='search']",
    ]

    search_input = None
    for sel in input_selectors:
        try:
            search_input = page.locator(sel)
            await search_input.wait_for(timeout=5000)
            break
        except Exception:
            search_input = None

    if search_input is None:
        raise RuntimeError("No encontré el input de búsqueda en Spotify")

    await search_input.fill(query)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(1200)

    # Click first result that looks like a track/play button
    # Prefer a play button in the top results.
    play_selectors = [
        "button[data-testid='play-button']",
        "button[aria-label^='Play']",
        "button[aria-label^='Reproducir']",
    ]

    clicked = await _try_click(page, play_selectors, timeout_ms=4000)
    if clicked:
        return

    # Fallback: click first track row then hit space
    try:
        first_row = page.locator("[data-testid='tracklist-row']").first
        await first_row.click(timeout=4000)
        await page.keyboard.press("Space")
        return
    except Exception:
        pass

    raise RuntimeError("No pude iniciar la reproducción en Spotify")

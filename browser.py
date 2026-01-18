import os
import asyncio
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext, Page

from . import settings


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


@dataclass
class ServiceSession:
    context: BrowserContext
    page: Page


class BrowserManager:
    """Singleton-style Playwright manager.

    Uses **persistent** contexts in /data to keep logins across deploys.
    """

    def __init__(self) -> None:
        self._pw = None
        self._lock = asyncio.Lock()
        self._whatsapp: Optional[ServiceSession] = None
        self._spotify: Optional[ServiceSession] = None

    async def _startup(self) -> None:
        if self._pw is None:
            self._pw = await async_playwright().start()

    async def close(self) -> None:
        async with self._lock:
            if self._whatsapp:
                await self._whatsapp.context.close()
                self._whatsapp = None
            if self._spotify:
                await self._spotify.context.close()
                self._spotify = None
            if self._pw:
                await self._pw.stop()
                self._pw = None

    async def _get_or_create(self, name: str, url: str) -> ServiceSession:
        await self._startup()
        assert self._pw is not None

        root = os.path.join(settings.DATA_DIR, "browser", name)
        _ensure_dir(root)

        context = await self._pw.chromium.launch_persistent_context(
            user_data_dir=root,
            headless=settings.PW_HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        return ServiceSession(context=context, page=page)

    async def whatsapp(self) -> ServiceSession:
        async with self._lock:
            if self._whatsapp is None:
                self._whatsapp = await self._get_or_create("whatsapp", "https://web.whatsapp.com/")
            return self._whatsapp

    async def spotify(self) -> ServiceSession:
        async with self._lock:
            if self._spotify is None:
                self._spotify = await self._get_or_create("spotify", "https://open.spotify.com/")
            return self._spotify

    async def screenshot_whatsapp(self) -> bytes:
        sess = await self.whatsapp()
        return await sess.page.screenshot(full_page=True)

    async def screenshot_spotify(self) -> bytes:
        sess = await self.spotify()
        return await sess.page.screenshot(full_page=True)


browser_manager = BrowserManager()

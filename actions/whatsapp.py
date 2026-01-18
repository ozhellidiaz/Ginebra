import re
import unicodedata

from playwright.async_api import Page


def _normalize_name(s: str) -> str:
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s


async def _wait_for_chat_ui(page: Page) -> None:
    # On WhatsApp Web, the main app container is usually present.
    await page.wait_for_timeout(500)


async def ensure_logged_in(page: Page) -> bool:
    # If QR canvas is present, likely not logged in.
    try:
        if await page.locator("canvas").count() > 0 and await page.locator("text=Scan me").count() > 0:
            return False
    except Exception:
        pass
    # Heuristic: search box exists when logged in
    try:
        await page.locator("div[contenteditable='true']").first.wait_for(timeout=2000)
        return True
    except Exception:
        return False


async def open_chat(page: Page, contact: str) -> None:
    await page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
    await _wait_for_chat_ui(page)

    # Try to focus search box: WhatsApp uses a contenteditable div for search.
    search_candidates = [
        "div[contenteditable='true'][data-tab='3']",
        "div[contenteditable='true'][data-tab='2']",
        "div[contenteditable='true'][role='textbox']",
    ]

    search = None
    for sel in search_candidates:
        loc = page.locator(sel).first
        try:
            await loc.wait_for(timeout=4000)
            search = loc
            break
        except Exception:
            continue

    if search is None:
        raise RuntimeError("No encontré la caja de búsqueda de WhatsApp (¿no has iniciado sesión?)")

    await search.click()
    await search.fill(contact)
    await page.wait_for_timeout(1200)

    # Click first result
    # WhatsApp results are listitems; we'll click a span with title matching, else first chat.
    try:
        exact = page.locator(f"span[title='{contact}']").first
        if await exact.count() > 0:
            await exact.click(timeout=3000)
            return
    except Exception:
        pass

    # Fuzzy fallback: find any span[title] in results and click first
    spans = page.locator("span[title]")
    n = await spans.count()
    target_norm = _normalize_name(contact)
    best_idx = None
    for i in range(min(n, 25)):
        title = await spans.nth(i).get_attribute("title")
        if not title:
            continue
        if _normalize_name(title) == target_norm:
            best_idx = i
            break
    if best_idx is None and n > 0:
        best_idx = 0

    if best_idx is None:
        raise RuntimeError("No encontré ese contacto/chat en WhatsApp")

    await spans.nth(best_idx).click(timeout=3000)


async def send_message(page: Page, contact: str, message: str) -> None:
    await open_chat(page, contact)

    # message box
    box_candidates = [
        "div[contenteditable='true'][data-tab='10']",
        "div[contenteditable='true'][data-tab='9']",
        "footer div[contenteditable='true']",
        "div[contenteditable='true'][role='textbox']",
    ]
    box = None
    for sel in box_candidates:
        loc = page.locator(sel).last
        try:
            await loc.wait_for(timeout=4000)
            box = loc
            break
        except Exception:
            continue

    if box is None:
        raise RuntimeError("No encontré la caja para escribir el mensaje")

    await box.click()
    await box.fill(message)
    await page.keyboard.press("Enter")

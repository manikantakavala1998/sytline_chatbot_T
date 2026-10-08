"""Smoke-check support console and ticket form layouts without changing server data."""

from pathlib import Path
from tempfile import gettempdir

from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:8001"
OUTPUT = Path(gettempdir()) / "sytline-support-ui-check"


def no_horizontal_overflow(page, name):
    overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
    assert overflow <= 0, f"{name}: {overflow}px of horizontal overflow"


def main():
    OUTPUT.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width, height in [(390, 844), (768, 1024), (1366, 768)]:
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"{BASE}/admin.html", wait_until="domcontentloaded")
            page.locator("#console").wait_for(state="visible")
            for view in ("home", "tickets", "disliked"):
                page.locator(f".nav-item[data-view='{view}']").click()
                assert page.locator(f"#view-{view}").is_visible()
                no_horizontal_overflow(page, f"admin {view} {width}")
                page.screenshot(path=str(OUTPUT / f"admin-{view}-{width}.png"))
            page.close()

        page = browser.new_page(viewport={"width": 1366, "height": 768}, color_scheme="dark")
        page.goto(f"{BASE}/admin.html", wait_until="domcontentloaded")
        page.locator("#console").wait_for(state="visible")
        page.locator(".nav-item[data-view='tickets']").click()
        no_horizontal_overflow(page, "admin tickets dark")
        page.screenshot(path=str(OUTPUT / "admin-tickets-dark.png"))
        page.close()

        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_function("typeof buildTicketPanel === 'function'")
        page.wait_for_timeout(1000)
        page.evaluate("""() => {
          document.querySelector('#messages').replaceChildren(buildTicketPanel('visual-test', 999));
        }""")
        page.locator(".ticket-button").first.click()
        assert page.locator(".ticket-note").is_visible()
        no_horizontal_overflow(page, "chat ticket form")
        page.screenshot(path=str(OUTPUT / "chat-ticket-form-390.png"))
        page.get_by_role("button", name="Cancel").click()
        assert page.get_by_role("button", name="Create support ticket").is_visible()
        page.close()
        browser.close()
    print(f"PASS support UI desktop, tablet, mobile, dark mode, ticket form; screenshots: {OUTPUT}")


if __name__ == "__main__":
    main()

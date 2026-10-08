"""Manual visual regression probe for the local chat UI.

Run with ``python -m scripts.check_responsive_layout``. It opens the local
HTML file, prints viewport/layout diagnostics, and saves screenshots under
the system temporary directory for visual inspection.
"""

from pathlib import Path
from tempfile import gettempdir

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(gettempdir()) / "syte-responsive-check"
VIEWPORTS = [
    (280, 568), (320, 568), (360, 740), (390, 844), (480, 800),
    (667, 375), (768, 1024), (1024, 500), (1024, 768),
    (1366, 400), (1366, 768), (1920, 1080),
]


def metrics(page):
    return page.evaluate("""() => {
      const rect = selector => {
        const el = document.querySelector(selector);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {x: Math.round(r.x), y: Math.round(r.y),
          right: Math.round(r.right), bottom: Math.round(r.bottom),
          width: Math.round(r.width), height: Math.round(r.height)};
      };
      return {
        viewport: [innerWidth, innerHeight],
        document: [document.documentElement.scrollWidth,
          document.documentElement.scrollHeight],
        header: rect('.app-header'), brand: rect('.brand'),
        actions: rect('.header-actions'), chat: rect('.chat-card'),
        messages: rect('.messages'), welcome: rect('.welcome'),
        composer: rect('.composer'), input: rect('#chat-input'),
        send: rect('#send-button'), context: rect('.context-panel'),
        fields: [...document.querySelectorAll('.context-grid input, .context-grid select')]
          .map(el => { const r = el.getBoundingClientRect();
            return [Math.round(r.x), Math.round(r.y), Math.round(r.right), Math.round(r.bottom)]; }),
        footer: rect('.message-footer'),
        footerWidths: (() => { const el = document.querySelector('.message-footer');
          return el ? [el.clientWidth, el.scrollWidth] : null; })(),
        contextScroll: (() => { const el = document.querySelector('.context-panel');
          return [el.clientHeight, el.scrollHeight]; })(),
        iconVisible: getComputedStyle(document.querySelector('.context-button > span:first-child')).display !== 'none'
      };
    }""")


def main():
    OUTPUT.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width, height in VIEWPORTS:
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.goto((ROOT / "frontend" / "chatbot" / "index.html").as_uri(), wait_until="domcontentloaded")
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUTPUT / f"chat-{width}x{height}.png"))
            initial = metrics(page)
            page.locator("#context-toggle").click()
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUTPUT / f"context-{width}x{height}.png"))
            expanded = metrics(page)
            page.locator("#context-toggle").click()
            page.evaluate("""() => {
              document.querySelector('#messages').replaceChildren();
              renderMessage('A customer order may have a long reference and several details that must wrap cleanly at every width.',
                'bot', {route: 'MARKDOWN_RAG_RESPONSE', timestamp: new Date().toISOString(),
                  decisionTrace: {intent: 'HELP_PROCESS', selected_route: 'MARKDOWN_RAG'},
                  id: 'visual-test', sources: ['order_and_billing_variations.md']});
            }""")
            page.wait_for_timeout(400)
            message = metrics(page)
            page.screenshot(path=str(OUTPUT / f"message-{width}x{height}.png"))
            assert initial["document"][0] <= width, f"horizontal page overflow at {width}x{height}"
            assert initial["brand"]["right"] <= initial["actions"]["x"] + 1
            assert initial["composer"]["bottom"] <= initial["chat"]["bottom"]
            if width <= 350:
                assert initial["welcome"]["y"] >= initial["messages"]["y"] - 1
            assert expanded["iconVisible"]
            if width <= 700:
                assert expanded["context"]["bottom"] <= height
                assert expanded["chat"]["height"] == initial["chat"]["height"]
                assert expanded["contextScroll"][0] <= height
            assert message["footerWidths"][1] <= message["footerWidths"][0] + 1
            if width <= 960:
                assert page.locator("#sidebar").evaluate("el => el.classList.contains('collapsed')")
                page.locator("#sidebar-toggle").click()
                page.wait_for_timeout(300)
                sidebar = page.locator("#sidebar").bounding_box()
                assert sidebar and sidebar["x"] >= 0 and sidebar["x"] + sidebar["width"] <= width
                page.locator("#sidebar-overlay").click(position={"x": width - 2, "y": height // 2})
                assert page.locator("#sidebar").evaluate("el => el.classList.contains('collapsed')")
            print(f"PASS {width}x{height}: context={expanded['context']['height']}px, "
                  f"chat={expanded['chat']['height']}px, footer={message['footerWidths']}")
            page.close()
        browser.close()


if __name__ == "__main__":
    main()

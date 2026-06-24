"""
Divundu Water Level Charts — Screenshot Scraper
Screenshots the HMMP Looker Studio dashboard charts for Divundu.

Produces:
  divundu_charts.png  — Water Level + Discharge chart screenshot

Requirements:
    pip install playwright
    playwright install chromium

Run manually:
    python scrape_divundu.py
"""

import os
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = (
    "https://lookerstudio.google.com/embed/reporting/"
    "1cf4b8e8-11ed-4bb2-863d-32df06f259a1/page/p_cux9lixr3c"
)
OUTPUT = os.path.join(os.path.dirname(__file__), "divundu_charts.png")
DEBUG  = os.path.join(os.path.dirname(__file__), "divundu_debug.png")
DEBUG2 = os.path.join(os.path.dirname(__file__), "divundu_debug2.png")


def scrape_divundu_charts():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        print(f"[{datetime.now()}] Loading HMMP dashboard (embed URL)...")
        page.goto(URL, wait_until="load", timeout=120000)
        page.wait_for_timeout(20000)

        # Debug1: initial state after load
        page.screenshot(path=DEBUG)
        print(f"[{datetime.now()}] Debug1 screenshot saved")

        # Print all text on page (leaf nodes AND shallow parents) to find Divundu
        all_text = page.evaluate("""
            () => {
                const seen = new Set();
                return Array.from(document.querySelectorAll('*'))
                    .filter(el => {
                        const t = el.textContent.trim();
                        return t.length > 0 && t.length < 80 && !seen.has(t) && seen.add(t);
                    })
                    .map(el => ({
                        tag: el.tagName,
                        text: el.textContent.trim(),
                        children: el.children.length
                    }))
                    .slice(0, 200);
            }
        """)
        print(f"[{datetime.now()}] Page text elements:")
        divundu_found = False
        for item in all_text:
            print(f"  [{item['tag']} children={item['children']}] {item['text']!r}")
            if 'DIVUNDU' in item['text'].upper():
                divundu_found = True

        # Click Divundu — try multiple strategies
        clicked = page.evaluate("""
            () => {
                const allEls = Array.from(document.querySelectorAll('*'));

                // Strategy 1: find smallest element whose ONLY text is Divundu
                const exact = allEls.filter(el =>
                    el.textContent.trim().toUpperCase() === 'DIVUNDU'
                );
                if (exact.length > 0) {
                    // prefer leaf nodes
                    const leaf = exact.find(e => e.children.length === 0) || exact[0];
                    leaf.click();
                    return 'exact: ' + leaf.textContent.trim();
                }

                // Strategy 2: find any element containing Divundu with short text
                const partial = allEls.filter(el =>
                    el.textContent.trim().toUpperCase().includes('DIVUNDU') &&
                    el.textContent.trim().length < 30
                );
                if (partial.length > 0) {
                    const leaf = partial.find(e => e.children.length === 0) || partial[0];
                    leaf.click();
                    return 'partial: ' + leaf.textContent.trim();
                }

                return false;
            }
        """)
        print(f"[{datetime.now()}] Clicked Divundu: {clicked}")

        # Wait for charts to render
        wait_ms = 20000 if clicked else 5000
        page.wait_for_timeout(wait_ms)

        # Debug2: state after clicking Divundu
        page.screenshot(path=DEBUG2)
        print(f"[{datetime.now()}] Debug2 screenshot saved")

        # Final screenshot
        page.screenshot(path=OUTPUT)
        print(f"[{datetime.now()}] Chart screenshot saved → {OUTPUT}")

        browser.close()
        return OUTPUT


if __name__ == "__main__":
    scrape_divundu_charts()

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
        # Tall viewport to capture as much content as possible
        page = browser.new_page(viewport={"width": 1440, "height": 1600})

        print(f"[{datetime.now()}] Loading HMMP dashboard (embed URL)...")
        page.goto(URL, wait_until="load", timeout=120000)
        page.wait_for_timeout(20000)

        # Debug1: initial state
        page.screenshot(path=DEBUG, full_page=True)
        print(f"[{datetime.now()}] Debug1 screenshot saved")

        # Print all text to find Divundu element
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
        for item in all_text:
            print(f"  [{item['tag']} children={item['children']}] {item['text']!r}")

        # Click Divundu
        clicked = page.evaluate("""
            () => {
                const allEls = Array.from(document.querySelectorAll('*'));

                // Strategy 1: exact text match
                const exact = allEls.filter(el =>
                    el.textContent.trim().toUpperCase() === 'DIVUNDU'
                );
                if (exact.length > 0) {
                    const leaf = exact.find(e => e.children.length === 0) || exact[0];
                    leaf.click();
                    return 'exact: ' + leaf.textContent.trim();
                }

                // Strategy 2: short text containing Divundu
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

        # Wait for charts to render after click
        page.wait_for_timeout(20000)

        # Scroll to bottom to make sure charts are in view
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        # Debug2: full page after clicking Divundu
        page.screenshot(path=DEBUG2, full_page=True)
        print(f"[{datetime.now()}] Debug2 screenshot saved")

        # Print text again to see what changed
        all_text2 = page.evaluate("""
            () => {
                const seen = new Set();
                return Array.from(document.querySelectorAll('*'))
                    .filter(el => {
                        const t = el.textContent.trim();
                        return t.length > 0 && t.length < 80 && !seen.has(t) && seen.add(t);
                    })
                    .map(el => el.textContent.trim())
                    .slice(0, 100);
            }
        """)
        print(f"[{datetime.now()}] Text after click:")
        for t in all_text2:
            print(f"  {t!r}")

        # Final screenshot (full page)
        page.screenshot(path=OUTPUT, full_page=True)
        print(f"[{datetime.now()}] Chart screenshot saved → {OUTPUT}")

        browser.close()
        return OUTPUT


if __name__ == "__main__":
    scrape_divundu_charts()

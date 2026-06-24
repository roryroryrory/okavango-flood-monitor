"""
Divundu Water Level Charts — Screenshot Scraper
Screenshots the HMMP Looker Studio dashboard charts for Divundu.

Produces:
  divundu_charts.png  — Water Level + Discharge chart screenshot

Requirements:
    pip install playwright pillow
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
        page = browser.new_page(viewport={"width": 1440, "height": 1600})

        print(f"[{datetime.now()}] Loading HMMP dashboard...")
        page.goto(URL, wait_until="load", timeout=120000)
        page.wait_for_timeout(20000)

        # Debug1: initial state (full page)
        page.screenshot(path=DEBUG, full_page=True)
        print(f"[{datetime.now()}] Debug1 saved")

        # Click Divundu station
        clicked = page.evaluate("""
            () => {
                const allEls = Array.from(document.querySelectorAll('*'));
                const exact = allEls.filter(el =>
                    el.textContent.trim().toUpperCase() === 'DIVUNDU'
                );
                if (exact.length > 0) {
                    const leaf = exact.find(e => e.children.length === 0) || exact[0];
                    leaf.click();
                    return 'exact: ' + leaf.textContent.trim();
                }
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
        page.wait_for_timeout(20000)

        # Scroll to the "Season Periods" / charts section
        page.evaluate("""
            () => {
                const els = Array.from(document.querySelectorAll('*'));
                // Find the Season Periods banner — charts sit just below it
                const target = els.find(el =>
                    el.textContent.trim().toLowerCase().includes('season periods') &&
                    el.textContent.trim().length < 50
                );
                if (target) {
                    target.scrollIntoView({ behavior: 'instant', block: 'start' });
                } else {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            }
        """)
        page.wait_for_timeout(2000)

        # Debug2: viewport after scrolling to charts
        page.screenshot(path=DEBUG2)
        print(f"[{datetime.now()}] Debug2 saved")

        # Final output: viewport screenshot showing charts
        page.screenshot(path=OUTPUT)
        print(f"[{datetime.now()}] Chart screenshot saved → {OUTPUT}")

        browser.close()
        return OUTPUT


if __name__ == "__main__":
    scrape_divundu_charts()

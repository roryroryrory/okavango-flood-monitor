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

# Base page URL — the ?s= state param isn't reliably applied in headless mode
# so we navigate to the page and then click through to the charts
URL = (
    "https://datastudio.google.com/u/0/reporting/"
    "1cf4b8e8-11ed-4bb2-863d-32df06f259a1/page/p_cux9lixr3c"
)
OUTPUT = os.path.join(os.path.dirname(__file__), "divundu_charts.png")
DEBUG  = os.path.join(os.path.dirname(__file__), "divundu_debug.png")


def scrape_divundu_charts():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Wide viewport so both charts sit side-by-side
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        print(f"[{datetime.now()}] Loading HMMP dashboard...")
        page.goto(URL, wait_until="load", timeout=120000)

        # Initial render wait
        page.wait_for_timeout(15000)
        page.screenshot(path=DEBUG)
        print(f"[{datetime.now()}] Debug screenshot saved")

        # Click HYDROLOGY HISTORICAL nav button
        clicked = page.evaluate("""
            () => {
                const els = Array.from(document.querySelectorAll('*'));
                const target = els.find(el =>
                    el.children.length === 0 &&
                    el.textContent.trim().toUpperCase() === 'HYDROLOGY HISTORICAL'
                );
                if (target) { target.click(); return true; }
                return false;
            }
        """)
        print(f"[{datetime.now()}] Clicked HYDROLOGY HISTORICAL: {clicked}")
        page.wait_for_timeout(10000)

        # Debug: screenshot of station list page
        DEBUG2 = os.path.join(os.path.dirname(__file__), "divundu_debug2.png")
        page.screenshot(path=DEBUG2)
        print(f"[{datetime.now()}] Debug2 screenshot saved")

        # Debug: print all visible text to find Divundu in the list
        all_text = page.evaluate("""
            () => Array.from(document.querySelectorAll('*'))
                .filter(el => el.children.length === 0 && el.textContent.trim().length > 0)
                .map(el => el.textContent.trim())
                .filter(t => t.length < 60)
                .slice(0, 100)
        """)
        print(f"[{datetime.now()}] Visible text elements:")
        for t in all_text:
            print(f"  {t!r}")

        # Try clicking Divundu in the station list
        clicked2 = page.evaluate("""
            () => {
                const els = Array.from(document.querySelectorAll('*'));
                const target = els.find(el =>
                    el.children.length === 0 &&
                    el.textContent.trim().toUpperCase().includes('DIVUNDU')
                );
                if (target) { target.click(); return target.textContent.trim(); }
                return false;
            }
        """)
        print(f"[{datetime.now()}] Clicked Divundu station: {clicked2}")

        # Wait for charts to render
        page.wait_for_timeout(15000)

        # Take the final screenshot
        page.screenshot(path=OUTPUT)
        print(f"[{datetime.now()}] Chart screenshot saved → {OUTPUT}")

        browser.close()
        return OUTPUT


if __name__ == "__main__":
    scrape_divundu_charts()

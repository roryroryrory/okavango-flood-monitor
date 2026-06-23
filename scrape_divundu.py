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
    "https://datastudio.google.com/u/0/reporting/"
    "1cf4b8e8-11ed-4bb2-863d-32df06f259a1/page/p_cux9lixr3c?s=oneAO01NKf0"
)
OUTPUT = os.path.join(os.path.dirname(__file__), "divundu_charts.png")


def scrape_divundu_charts():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Wide viewport so both charts are visible side-by-side
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        print(f"[{datetime.now()}] Loading Looker Studio dashboard...")
        page.goto(URL, wait_until="load", timeout=120000)

        # Looker Studio renders charts progressively — wait for them to fully load
        print(f"[{datetime.now()}] Waiting for charts to render...")
        page.wait_for_timeout(20000)

        # Take full-page screenshot first to capture everything
        page.screenshot(path=OUTPUT)
        print(f"[{datetime.now()}] Screenshot saved → {OUTPUT}")

        browser.close()
        return OUTPUT


if __name__ == "__main__":
    scrape_divundu_charts()

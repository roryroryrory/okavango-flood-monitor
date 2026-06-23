"""
Okavango Flood Monitor — Data Scraper
Scrapes Rundu & Mukwe streamflow data from the Namibia Flood & Drought Monitor.

Produces two files:
  flood_data.json        — current levels + forecast (for the summary widget)
  flood_timeseries.json  — full historical + 10-day forecast time series (for the graph)

Requirements:
    pip install playwright
    playwright install chromium

Run manually:
    python scrape_flood_data.py

Schedule daily (Mac/Linux cron — runs at 8am):
    0 8 * * * /usr/bin/python3 /path/to/scrape_flood_data.py
"""

import json
import os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

URL = "https://hydrology.soton.ac.uk/apps/nam_app/"
OUTPUT_SUMMARY    = os.path.join(os.path.dirname(__file__), "flood_data.json")
OUTPUT_TIMESERIES = os.path.join(os.path.dirname(__file__), "flood_timeseries.json")

# Map point layerIds discovered via browser inspection (stable identifiers)
STATIONS = {
    "RUNDU": {"layerId": 12028470, "lat": -17.9,  "lng": 19.75},
    "MUKWE": {"layerId": 12031297, "lat": -18.033, "lng": 21.417},
}


def extract_dygraph_timeseries(page):
    """
    Click each map marker and read the dygraph time series that loads.
    Returns a dict: { "RUNDU": [...], "MUKWE": [...] }
    Each entry is a list of { date, hist, fcst_mean, fcst_p25, fcst_p75, fcst_p5, fcst_p95 }
    """
    timeseries = {}

    for name, info in STATIONS.items():
        print(f"  Clicking {name} marker (layerId {info['layerId']})...")

        # Fire a click on the Leaflet marker via JavaScript
        page.evaluate(f"""
            (function() {{
                const mapEl = document.querySelector('.leaflet-container');
                const lmap  = mapEl.htmlwidget_data_init_result.getMap();
                lmap.eachLayer(function(l) {{
                    if (l.options && l.options.layerId === {info['layerId']}) {{
                        l.fire('click', {{ latlng: l._latlng }});
                    }}
                }});
            }})();
        """)

        # Wait for dygraph to re-render with new station data
        page.wait_for_timeout(5000)

        # Extract the raw data from the dygraph instance
        data = page.evaluate("""
            (function() {
                const el  = document.getElementById('time_plot');
                const dyg = el && el.htmlwidget_data_init_result && el.htmlwidget_data_init_result.dygraph;
                if (!dyg || !dyg.rawData_) return null;
                return dyg.rawData_.map(function(r) {
                    return {
                        date:      new Date(r[0]).toISOString().slice(0, 10),
                        hist:      r[1] ? r[1][0] : null,
                        fcst_mean: r[2] ? r[2][0] : null,
                        fcst_p25:  r[4] ? r[4][0] : null,
                        fcst_p75:  r[4] ? r[4][1] : null,
                        fcst_p5:   r[3] ? r[3][0] : null,
                        fcst_p95:  r[3] ? r[3][2] : null,
                    };
                });
            })();
        """)

        if data:
            hist_rows = [d for d in data if d["hist"] is not None]
            last_hist = hist_rows[-1] if hist_rows else {}
            print(f"    {name}: {len(data)} points, last hist {last_hist.get('date')} = {last_hist.get('hist', '?'):.2f} m³/s")
            timeseries[name] = data
        else:
            print(f"    WARNING: No dygraph data found for {name}")

    return timeseries


def scrape_flood_levels():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[{datetime.now()}] Loading NAM-FDM...")
        page.goto(URL, wait_until="load", timeout=120000)
        # Extra wait — site has live data feeds; give JS time to render
        page.wait_for_timeout(15000)
        page.screenshot(path="debug_after_load.png")
        print(f"[{datetime.now()}] Screenshot saved → debug_after_load.png")

        # ── Step 1: Current levels from the River Points table ──────────────
        # Tab IDs are dynamic in Shiny — find tabs by visible text instead
        print(f"[{datetime.now()}] Getting current levels from River Points table...")

        # Print all tab links found on the page for debugging
        tabs = page.query_selector_all('a[role="tab"], .nav-tabs a, ul.nav a')
        print(f"  Found {len(tabs)} tab elements:")
        for t in tabs:
            print(f"    href={t.get_attribute('href')}  text={t.inner_text().strip()!r}")

        # Click the tab containing "River" or "Points" text
        page.get_by_role("tab").filter(has_text="River").first.click()
        page.wait_for_timeout(2000)
        page.screenshot(path="debug_after_tab1.png")

        # Click the sub-tab containing "River Points"
        page.get_by_role("tab").filter(has_text="River Points").first.click()
        page.wait_for_selector('#DataTables_Table_1 tbody tr', timeout=60000)
        page.wait_for_timeout(3000)
        page.screenshot(path="debug_after_tab2.png")

        rows = page.query_selector_all('#DataTables_Table_1 tbody tr')
        current_levels = {}

        for row in rows:
            cells = row.query_selector_all('td')
            if len(cells) < 6:
                continue
            cell_text = [c.inner_text().strip() for c in cells]
            location = cell_text[1]
            for name in STATIONS:
                if name in location.upper():
                    current_levels[name] = {
                        "id":                           cell_text[0],
                        "name":                         location,
                        "current_flow_m3s":             float(cell_text[2]) if cell_text[2] not in ("", "NA") else None,
                        "current_percentile":           float(cell_text[3]) if cell_text[3] not in ("", "NA") else None,
                        "forecast_10day_max_m3s":       float(cell_text[4]) if cell_text[4] not in ("", "NA") else None,
                        "forecast_10day_max_percentile":float(cell_text[5]) if cell_text[5] not in ("", "NA") else None,
                    }

        # ── Step 2: Full time series via map marker clicks ──────────────────
        print(f"[{datetime.now()}] Extracting time series from map markers...")
        # Navigate back to Current Conditions tab (the map)
        page.get_by_role("tab").filter(has_text="Current Conditions").first.click()
        page.wait_for_timeout(3000)

        timeseries = extract_dygraph_timeseries(page)

        browser.close()

        if not current_levels:
            raise RuntimeError("No station data found — page structure may have changed.")

        now = datetime.now(timezone.utc).isoformat()

        # ── Save summary JSON (flood_data.json) ─────────────────────────────
        summary = {
            "updated_utc": now,
            "source": URL,
            "stations": current_levels,
        }
        with open(OUTPUT_SUMMARY, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"[{datetime.now()}] Saved summary → {OUTPUT_SUMMARY}")

        # ── Save timeseries JSON (flood_timeseries.json) ────────────────────
        ts_output = {
            "exportedAt": now,
            "source": URL,
            "note": "Modelled streamflow from NAM-FDM (VIC hydrological model). Values in m³/s.",
            "stations": {}
        }
        for name, info in STATIONS.items():
            ts_output["stations"][name] = {
                "layerId": info["layerId"],
                "lat": info["lat"],
                "lng": info["lng"],
                "current_flow_m3s":   current_levels.get(name, {}).get("current_flow_m3s"),
                "current_percentile": current_levels.get(name, {}).get("current_percentile"),
                "data": timeseries.get(name, []),
            }
        with open(OUTPUT_TIMESERIES, "w") as f:
            json.dump(ts_output, f, indent=2)
        print(f"[{datetime.now()}] Saved timeseries → {OUTPUT_TIMESERIES}")

        # ── Print summary ───────────────────────────────────────────────────
        for name, data in current_levels.items():
            print(f"  {name}: {data['current_flow_m3s']} m³/s (pctl {data['current_percentile']}%)")

        return summary


if __name__ == "__main__":
    scrape_flood_levels()

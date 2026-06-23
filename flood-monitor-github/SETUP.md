# Flood Monitor — GitHub Actions Setup

This runs the flood scraper every day at 10am SAST and pushes the JSON files to your SiteGround server automatically.

---

## Step 1 — Create a GitHub repository

1. Go to https://github.com/new
2. Name it something like `okavango-flood-monitor`
3. Set it to **Private** (keeps your FTP credentials safe even if you expose the repo later)
4. Click **Create repository**

---

## Step 2 — Upload the files

Upload these three files to the root of your new repo:

- `scrape_flood_data.py`
- `requirements.txt`
- `.github/workflows/daily-flood-update.yml`

You can drag-and-drop them via the GitHub web interface, or use GitHub Desktop.

> **Note:** The `.github/workflows/` folder structure must be preserved exactly.

---

## Step 3 — Add your SiteGround FTP credentials as Secrets

In your GitHub repo, go to:
**Settings → Secrets and variables → Actions → New repository secret**

Add these four secrets:

| Secret name | What to put in it |
|---|---|
| `FTP_HOST` | Your SiteGround FTP hostname (e.g. `ftp.theafricanwild.com` or the IP from SiteGround's FTP accounts page) |
| `FTP_USER` | Your FTP username |
| `FTP_PASS` | Your FTP password |
| `FTP_PATH` | The folder path on the server where the JSON files should go (e.g. `public_html/flood-data`) |

> Find your FTP details in SiteGround → Site Tools → FTP Accounts.

---

## Step 4 — Test it manually

Once the files are uploaded and secrets are set:

1. Go to your repo → **Actions** tab
2. Click **Daily Flood Data Update** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch the logs — it should scrape and upload in ~2 minutes

---

## Step 5 — You're done

After a successful manual test, the workflow will run automatically every day at 08:00 UTC (10:00 SAST). The `flood_data.json` and `flood_timeseries.json` files on your server will update daily, and your flood widget/graph pages will always show fresh data.

---

## Troubleshooting

- **FTP connection refused**: Check that your SiteGround FTP host is correct and FTP (not SFTP) is enabled.
- **Scraper fails**: The source website (hydrology.soton.ac.uk) may be down temporarily — the next day's run will retry automatically.
- **Wrong folder on server**: Double-check `FTP_PATH` — it should be the path relative to your FTP root (usually the same as the web root).

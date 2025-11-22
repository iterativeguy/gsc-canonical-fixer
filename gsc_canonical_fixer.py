# ===============================================================================
# GSC Canonical Fixer – Fix Google canonical issues after domain migration
# Free • Open Source • 2025 Ready
# GitHub: https://github.com/iterativeguy/gsc-canonical-fixer
#
# If this tool saved your migration, consider supporting:
# → https://buymeacoffee.com/iterativeguy
# ===============================================================================

"""
⚠️  IMPORTANT WARNING – READ BEFORE USING THIS SCRIPT ⚠️

This tool uses Google's official Indexing API (200 requests/day free quota) 
and URL Inspection API.

YOU MUST USE IT RESPONSIBLY:
• Only on sites you own or have explicit permission to manage
• Do not remove or bypass the built-in delays and quota limits
• Do not exceed the 200 requests/day quota on purpose
• Always respect Google's policies: 
  https://developers.google.com/search/apis/indexing-api/v3/quota

Abusing the Indexing API can result in temporary or permanent quota suspension 
for your Google Cloud project.

THE AUTHOR IS NOT RESPONSIBLE FOR:
• Quota suspensions or account restrictions
• Misuse on third-party sites
• Any damage caused by incorrect configuration or abuse

By running this script you agree to use it ethically and in full compliance 
with Google's Terms of Service.

Use at your own risk.

If this tool saved your migration, consider supporting:
→ https://buymeacoffee.com/iterativeguy

"""

# ===============================================================================
# INSTALL ONCE:
# python -m pip install pandas tqdm requests beautifulsoup4 lxml google-api-python-client google-auth
# ===============================================================================

import pandas as pd
import sqlite3
import time
import argparse
import webbrowser
import os
from datetime import datetime
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ============================= CONFIGURATION =============================
# EDIT ONLY THESE 8 LINES

KEY_FILE         = 'my-gcc-key.json'          # Your service account JSON file
SITE_URL         = 'sc-domain:example.com'    # GSC property: sc-domain:example.com or https://example.com/
OLD_DOMAIN       = 'olddomain.com'            # Old domain (no https://, no trailing slash)
NEW_DOMAIN       = 'newdomain.com'            # New domain (no https://, no trailing slash)
CSV_FILE_PATH    = 'Table.csv'                # Exported GSC file
CSV_COLUMN_NAME  = 'URL'                      # Column name containing the URLs
DB_FILE          = 'gsc_canonical_fixer.db'   # Local tracking database
BATCH_SIZE       = 180                        # Safe limit (max 200/day)

# ==========================================================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            url TEXT PRIMARY KEY,
            added_at TEXT,
            submitted_at TEXT,
            canonical_ok_at TEXT,
            last_status TEXT,
            observation TEXT
        )
    ''')
    conn.commit()
    return conn, c

def import_csv(conn, c):
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        urls = df[CSV_COLUMN_NAME].astype(str).dropna().str.strip().tolist()
        added = 0
        for url in urls:
            c.execute("INSERT OR IGNORE INTO urls (url, added_at) VALUES (?, ?)",
                      (url, datetime.now().isoformat()))
            if c.rowcount: added += 1
        conn.commit()
        print(f"Imported {len(urls)} URLs from CSV → {added} new")
    except Exception as e:
        print(f"CSV import failed: {e}")

def check_page_canonical(url):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    try:
        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'lxml')
        tag = soup.find('link', rel='canonical')
        if not tag or not tag.get('href'):
            return False, "No canonical tag found"
        href = tag['href']
        clean = href.replace('https://', '').replace('http://', '').split('/')[0]
        return NEW_DOMAIN in clean, href
    except:
        return False, "Request failed / timeout"

def get_google_canonical(url):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=['https://www.googleapis.com/auth/webmasters'])
        service = build('searchconsole', 'v1', credentials=credentials)
        req = {'inspectionUrl': url, 'siteUrl': SITE_URL}
        resp = service.urlInspection().index().inspect(body=req).execute()
        return resp['inspectionResult']['indexStatusResult'].get('googleCanonical', '')
    except:
        return None

def submit_to_indexing(url):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=['https://www.googleapis.com/auth/indexing'])
        service = build('indexing', 'v3', credentials=credentials)
        service.urlNotifications().publish(body={'url': url, 'type': 'URL_UPDATED'}).execute()
        return True
    except HttpError as e:
        if '429' in str(e):
            print("\nQUOTA EXCEEDED (200/day) – Script stopped")
            exit()
        return False

def generate_and_open_report():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM urls ORDER BY added_at DESC", conn)
    conn.close()

    total = len(df)
    submitted = len(df[df['last_status'] == 'SUBMITTED'])
    fixed = len(df[df['last_status'] == 'FIXED'])
    errors = total - submitted - fixed

    html = f"""<!DOCTYPE html>
<html><head><title>GSC Canonical Fixer Report</title>
<meta charset="utf-8">
<style>
    body {{font-family: system-ui, sans-serif; margin:40px; background:#f8f9fa;}}
    h1 {{color:#1967d2;}} .card {{background:white; padding:25px; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.1); margin-bottom:30px;}}
    table {{width:100%; border-collapse:collapse; background:white; border-radius:8px; overflow:hidden;}}
    th {{background:#1967d2; color:white; padding:15px;}}
    td {{padding:12px 15px; border-bottom:1px solid #eee;}}
    tr:hover {{background:#f5f9ff;}}
    .s {{color:#0d9d58; font-weight:bold;}} .f {{color:#1a73e8; font-weight:bold;}} .e {{color:#d93025;}}
</style></head><body>
<h1>GSC Canonical Fixer – Final Report</h1>
<div class="card"><h2>Summary</h2>
<p><strong>Total URLs:</strong> {total}</p>
<p><strong>Submitted to Indexing API:</strong> <span class="s">{submitted}</span></p>
<p><strong>Already fixed by Google:</strong> <span class="f">{fixed}</span></p>
<p><strong>Errors / Skipped:</strong> <span class="e">{errors}</span></p>
<p><em>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</em></p></div>
<table><tr><th>URL</th><th>Status</th><th>Observation</th><th>Submitted</th><th>Fixed</th></tr>"""
    for _, r in df.iterrows():
        cls = "f" if r['last_status'] == "FIXED" else "s" if r['last_status'] == "SUBMITTED" else "e"
        st = r['last_status'] or "Pending"
        html += f"<tr><td><a href='{r['url']}'>{r['url'][:90]}{'...' if len(r['url'])>90 else ''}</a></td>"
        html += f"<td class='{cls}'>{st}</td><td>{r['observation'] or '-'}</td>"
        html += f"<td>{r['submitted_at'][:16] if r['submitted_at'] else '-'}</td>"
        html += f"<td>{r['canonical_ok_at'][:16] if r['canonical_ok_at'] else '-'}</td></tr>"
    html += "</table></body></html>"

    with open("GSC_Canonical_Fixer_Report.html", "w", encoding="utf-8") as f:
        f.write(html)
    webbrowser.open('file://' + os.path.realpath("GSC_Canonical_Fixer_Report.html"))
    print("\nHTML report generated and opened!")

def main():
    parser = argparse.ArgumentParser(description="Fix Google canonical issues after domain migration")
    parser.add_argument('--force', action='store_true', help="Re-process all URLs even if already fixed")
    args = parser.parse_args()

    conn, c = init_db()
    import_csv(conn, c)

    query = "SELECT url FROM urls WHERE last_status IS NULL OR last_status != 'FIXED'"
    if args.force:
        query = "SELECT url FROM urls"
    urls = [row[0] for row in c.execute(query + f" LIMIT {BATCH_SIZE}")]

    if not urls:
        print("Nothing to do – all URLs already fixed!")
        generate_and_open_report()
        return

    print(f"Starting batch of {len(urls)} URLs...\n")

    for url in tqdm(urls, desc="Processing", bar_format="{l_bar}{bar} | {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"):
        observation = ""
        status = "ERROR"

        page_ok, page_msg = check_page_canonical(url)
        if not page_ok:
            observation = f"Page canonical wrong: {page_msg}"
            tqdm.write(f"  Page issue → {url}")
        else:
            google_canon = get_google_canonical(url)
            if google_canon and OLD_DOMAIN in google_canon.replace('https://', '').replace('http://', ''):
                if submit_to_indexing(url):
                    status = "SUBMITTED"
                    observation = f"Submitted → Google had: {google_canon}"
                    tqdm.write(f"  Submitted → {url}")
                else:
                    status = "SUBMIT_FAILED"
                    observation = "Indexing API failed"
            else:
                status = "FIXED"
                observation = f"Already correct → Google sees: {google_canon or 'new domain'}"
                tqdm.write(f"  Already fixed → {url}")

        c.execute("""UPDATE urls SET last_status=?, observation=?,
                     submitted_at=COALESCE(submitted_at, ?),
                     canonical_ok_at=COALESCE(canonical_ok_at, ?)
                     WHERE url=?""",
                  (status, observation,
                   datetime.now().isoformat() if status == "SUBMITTED" else None,
                   datetime.now().isoformat() if status == "FIXED" else None, url))
        conn.commit()
        time.sleep(1)

    print("\nBatch finished!")
    generate_and_open_report()
    conn.close()

if __name__ == "__main__":
    main()

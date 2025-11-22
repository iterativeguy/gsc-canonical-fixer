# GSC Canonical Fixer

**Fix Google's canonical mess after domain migration – in hours instead of months**

After any domain migration, Google keeps thousands of pages indexed on the old domain — even with perfect 301s and canonical tags.

This open-source Python tool fixes it automatically using official Google APIs.

Tested and used successfully on 5k–50k page sites in 2025.

## Features
- Live <link rel="canonical"> validation
- URL Inspection API + Indexing API
- Smart quota management (never wastes your 200/day limit)
- SQLite tracking – resume anytime
- Beautiful HTML report that opens automatically
- --force mode

## Like the tool? Say thanks

If this script saved your migration (or your sanity):

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/iterativeguy)

→ https://buymeacoffee.com/iterativeguy

Every beer helps keep more free SEO tools coming. Thank you!

## Installation

```bash
python -m pip install pandas tqdm requests beautifulsoup4 lxml google-api-python-client google-auth
```

## Setup – 5 minutes only

1. **Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Enable: Google Search Console API + Web Search Indexing API
   - Create Service Account → download JSON key → rename to my-gcc-key.json

2. **Google Search Console**
   - Settings → Users & permissions → Add user
   - Paste the service account email → give Owner permission

3. **Export from GSC**
   - Pages report → Export → CSV → save as Table.csv

4. **Edit the 8 config lines in canonical_fixer.py**
   ```python
   KEY_FILE         = 'my-gcc-key.json'
   SITE_URL         = 'sc-domain:example.com'    # or https://example.com/
   OLD_DOMAIN       = 'olddomain.com'
   NEW_DOMAIN       = 'example.com'
   CSV_FILE_PATH    = 'Table.csv'
   CSV_COLUMN_NAME  = 'URL'
   DB_FILE          = 'gsc_canonical_fixer.db'
   BATCH_SIZE       = 180
   ```

5. **Run**
   ```bash
   python canonical_fixer.py          # normal run
   python canonical_fixer.py --force  # re-process everything
   ```

HTML report opens automatically when finished.

## Important warnings
- Only use on sites you own or have explicit permission
- Never remove delays or quota limits
- Respect Google's policies: https://developers.google.com/search/apis/indexing-api/v3/quota
- Author is not responsible for quota suspension or misuse

## License
MIT © 2025 [iterativeguy](https://github.com/iterativeguy) – Free forever

Made with frustration, coffee and love for the SEO community.

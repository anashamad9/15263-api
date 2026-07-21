# 15263 Offers API

Static JSON API for affiliate offers assigned to affiliate ID `15263`.

The project syncs columns B-F from the Google Sheet:

- B: Offer Name
- C: Code
- D: Affiliate ID
- E: Discount
- F: GEO

Run the sync locally:

```bash
python3 scripts/sync_sheet.py
```

The generated endpoint is:

```text
docs/api/offers.json
```

For GitHub Pages, enable Pages from the `docs/` folder on the `main` branch. The GitHub Action runs every 15 minutes and commits any changed JSON.

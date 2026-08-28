# Group Works Web App

A mobile-friendly web companion to the [Group Works card deck](https://groupworksdeck.org) — 91 patterns of healthy group process, created by the Group Pattern Language Project (CC BY-SA).

Used with permission.

## Features

- **Browse** all 91 patterns by category or A–Z, with search
- **Draw** a random card, optionally filtered by category
- **Spreads** — tarot-style layouts (2–7 cards, or custom up to 13) for designing or debriefing gatherings
- Category divider cards with official descriptions
- Related pattern chips on each card detail view
- Links through to the full pattern on groupworksdeck.org

## Files

| File | Purpose |
|---|---|
| `groupworks.html` | The single-file web app — host this on your server |
| `fetch_hearts.py` | Scrapes official heart text + related cards from groupworksdeck.org and patches them into `groupworks.html` |
| `extract_cards.py` | Splits the Group Works PDF into per-card images |
| `convert_to_jpg.py` | Converts extracted PNG card images to JPGs |
| `fix_page22.py` | Fixes cards that came from the wrong PDF page during extraction |
| `card_filenames.txt` | Checklist of all 91 expected image filenames |

## Setup

### 1. Get the card images

Request the free PDF download at [groupworksdeck.org](https://groupworksdeck.org), then:

```bash
pip install pymupdf pillow
python extract_cards.py GroupWorks.pdf
python convert_to_jpg.py
```

This creates a `cards/` folder with 91 JPGs. Upload that folder alongside `groupworks.html` on your server.

### 2. Fetch official card text and related patterns

```bash
pip install requests beautifulsoup4
python fetch_hearts.py
```

Run from the same folder as `groupworks.html`. It visits each pattern page on groupworksdeck.org, scrapes the Heart text and related pattern list, and patches them directly into `groupworks.html`. Takes ~3 minutes. A backup is saved to `groupworks.html.bak`.

### 3. Deploy

Upload to your server:

```
your-site/groupworks/
  groupworks.html
  cards/
    aesthetics_of_space.jpg
    ... (91 files)
```

## Card image filenames

See `card_filenames.txt` for the full list of expected filenames. Images go in a `cards/` subfolder next to `groupworks.html`. Any card without a matching image falls back to a styled text face automatically.

## Credits

Card content © the Group Pattern Language Project, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).  
Web app © 2025 miltonics, [MIT License](LICENSE).  
Built as an independent companion, used with permission. Not officially affiliated with groupworksdeck.org.

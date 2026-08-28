# Group Works Web App

A mobile-friendly web companion to the [Group Works card deck](https://groupworksdeck.org) — 91 patterns of healthy group process, created by the Group Pattern Language Project (CC BY-SA).

Used with permission.

## What it does

- Browse all 91 patterns by category or A–Z, with search
- Draw a random card, optionally filtered by category
- Lay spreads (like tarot) to design or debrief a gathering
- Links through to the full pattern on groupworksdeck.org

---

## Setup

### Step 1 — Get the files

Download or clone this repo:

```
https://github.com/miltonics/groupworks-web-app
```

### Step 2 — Get the card images

1. Go to [groupworksdeck.org](https://groupworksdeck.org) and download the free PDF
2. The file will be named **GroupWorks-Deck-2019-Download-4up.pdf**
3. Put the PDF in the same folder as `extract_cards.py`

### Step 3 — Install Python dependencies

```powershell
pip install pymupdf pillow
```

### Step 4 — Extract the card images

```powershell
python extract_cards.py "GroupWorks-Deck-2019-Download-4up.pdf"
```

This creates a `cards\` folder with all 91 card images plus the 9 category cards, correctly named. Takes about a minute.

### Step 5 — Deploy

Upload these two things to your web server in the same folder:

```
groupworks.html
cards\
```

That's it. Open `groupworks.html` in a browser to verify everything looks right before uploading.

---

## Optional: fetch official card text

The app ships with plain-language summaries for each card. To replace them with the official "Heart" text from groupworksdeck.org:

```powershell
pip install requests beautifulsoup4
python fetch_hearts.py
```

Run this from the same folder as `groupworks.html`. It visits each pattern page, scrapes the official text, and patches it into the HTML file. Takes about 3 minutes. A backup is saved as `groupworks.html.bak`.

---

## Files

| File | Purpose |
|---|---|
| `groupworks.html` | The web app — this is what you host |
| `extract_cards.py` | Extracts card images from the PDF |
| `fetch_hearts.py` | Fetches official card text from groupworksdeck.org |
| `convert_tiles.py` | Alternative: converts PNGs to JPGs if you have them already |
| `card_filenames.txt` | Reference list of all 91 expected image filenames |

---

## Credits

Card content © the Group Pattern Language Project, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
Web app © 2025 miltonics, [MIT License](LICENSE).
Built as an independent companion, used with permission. Not officially affiliated with groupworksdeck.org.


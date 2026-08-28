"""
extract_cards.py — Group Works PDF → cards/ folder
====================================================
Usage (Windows PowerShell):
    python extract_cards.py GroupWorks.pdf

What it does:
1. Renders every page of the PDF as a high-quality JPEG
2. Reads the text on each page to figure out which card it is
3. Renames (or copies) each image to the filename the app expects
4. Writes a report showing what was matched and what wasn't

Requirements:
    pip install pymupdf pillow

Place this script in the same folder as groupworks.html.
Run it once; it creates a  cards/  subfolder automatically.
"""

import sys, re, shutil, pathlib, json
import fitz          # PyMuPDF
from PIL import Image
import io

# ── canonical card list (must match the app's DECK array) ──────────────────
CARDS = [
    # Intention
    "Commitment", "Invitation", "Priority Focus", "Purpose", "Setting Intention",
    # Context
    "Aesthetics of Space", "Circle", "Gaia", "Group Culture",
    "History and Context", "Nooks in Space and Time", "Power of Place",
    "Whole System in the Room",
    # Relationship
    "Appreciation", "Breaking Bread Together", "Celebrate",
    "Good Faith Assumptions", "Honour Each Person", "Hosting", "Power Shift",
    "Shared Airtime", "Tend Relationships", "Transparency",
    # Flow
    "Balance Process and Content", "Balance Structure and Flexibility",
    "Closing", "Divergence and Convergence Rhythm", "Follow the Energy",
    "Iteration", "Opening and Welcome", "Preparedness",
    "Reflection-Action Cycle", "Rest", "Right Size Bite", "Ritual",
    "Seasoned Timing", "Subgroup and Whole Group", "Trajectory",
    # Creativity
    "Challenge", "Expressive Arts", "Generate Possibilities", "Improvise",
    "Mode Choice", "Playfulness", "Power of Constraints",
    # Perspective
    "Common Ground", "Embrace Dissonance and Difference", "Fractal",
    "Go Meta", "Seeing the Forest, Seeing the Trees", "Time Shift",
    "Translation", "Unity and Diversity", "Value the Margins",
    "Viewpoint Shift",
    # Modelling
    "Appropriate Boundaries", "Courageous Modelling", "Discharging",
    "Dwell with Emotions", "Guerrilla Facilitation", "Holding Space",
    "Listening", "Mirroring", "Not about You", "Self-Awareness",
    "Shared Leadership and Roles", "Simplify", "Taking Responsibility",
    "Witness with Compassion",
    # Inquiry & Synthesis
    "Deliberate", "Distilling", "Experts on Tap", "Feedback", "Go Deeper",
    "Harvesting", "Inform the Group Mind", "Inquiry",
    "Mapping and Measurement", "Moving toward Alignment", "Naming",
    "Story", "Yes, and",
    # Faith
    "All Grist for the Mill", "Dive In", "Emergence", "Letting Go", "Magic",
    "Presence", "Silence", "Spirit", "Trust the Wisdom of the Group",
]

def card_to_filename(name: str) -> str:
    """'Aesthetics of Space'  →  'aesthetics_of_space.jpg'"""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug + ".jpg"

# Build lookup: normalised text fragment → canonical name
def normalise(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())

LOOKUP = {normalise(c): c for c in CARDS}
# also index by first significant word for fuzzy matching
FIRST_WORD = {normalise(c).split()[0]: c for c in CARDS}

def best_match(page_text: str) -> str | None:
    """Return canonical card name found in page_text, or None."""
    norm = normalise(page_text)
    # exact substring match (longest first to avoid partial collisions)
    for key in sorted(LOOKUP, key=len, reverse=True):
        if key in norm:
            return LOOKUP[key]
    # fallback: first-word match
    words = norm.split()
    for w in words:
        if w in FIRST_WORD:
            return FIRST_WORD[w]
    return None

def render_page(page, dpi=200) -> bytes:
    """Render a PDF page to JPEG bytes at given DPI."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_cards.py <path-to-groupworks.pdf>")
        sys.exit(1)

    pdf_path = pathlib.Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    out_dir = pathlib.Path("cards")
    out_dir.mkdir(exist_ok=True)
    raw_dir = pathlib.Path("cards_raw")   # unmatched pages land here
    raw_dir.mkdir(exist_ok=True)

    print(f"\nOpening {pdf_path.name}  ({pdf_path.stat().st_size // 1024} KB)")
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    print(f"Pages found: {total}\n")

    matched   = {}   # canonical name → output filename
    unmatched = []   # page numbers that didn't match

    for page_num in range(total):
        page = doc[page_num]
        text = page.get_text()
        name = best_match(text)

        jpeg = render_page(page)

        if name:
            fname = card_to_filename(name)
            dest  = out_dir / fname
            dest.write_bytes(jpeg)
            matched[name] = fname
            print(f"  p{page_num+1:03d}  ✓  {fname}")
        else:
            raw_name = f"page_{page_num+1:03d}.jpg"
            (raw_dir / raw_name).write_bytes(jpeg)
            unmatched.append(page_num + 1)
            print(f"  p{page_num+1:03d}  ?  → cards_raw/{raw_name}  (no match)")

    doc.close()

    # ── report ────────────────────────────────────────────────────────────
    missing = [c for c in CARDS if c not in matched]

    print("\n" + "="*60)
    print(f"Matched:   {len(matched):3d} / 91 cards")
    print(f"Unmatched pages (saved to cards_raw/): {len(unmatched)}")
    print(f"Cards with no image yet:               {len(missing)}")

    if missing:
        print("\nMissing cards — rename the right file in cards_raw/ manually:")
        for c in missing:
            print(f"  {card_to_filename(c)}")

    if unmatched:
        print(f"\nUnmatched pages: {unmatched}")
        print("Open cards_raw/ and compare visually to the list above.")

    # write a JSON manifest so you can inspect the mapping
    manifest = {
        "matched": matched,
        "missing": missing,
        "unmatched_pages": unmatched,
    }
    pathlib.Path("cards_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("\nFull mapping saved to cards_manifest.json")
    print("\nDone. Upload the  cards/  folder next to  groupworks.html  on your server.")

if __name__ == "__main__":
    main()

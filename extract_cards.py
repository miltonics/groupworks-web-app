"""
extract_cards.py — Group Works 4-up PDF → cards/ folder
========================================================
Uses exact positional mapping (alphabetical order) rather than
text matching, so quadrant bleed doesn't matter.

Usage (PowerShell):
    pip install pymupdf pillow
    python extract_cards.py "GroupWorks-Deck-2019-Download-4up.pdf"

PDF structure:
  Pages 1-22:  4 unique pattern cards per page, A-Z order
  Page 23:     3 pattern cards (W, W, Y) + 1st category card
  Pages 24-25: category divider cards (4 per page)
  Page 26:     blank templates x4 (skipped)
  Page 27:     logo/back design x4 (saves card_back.jpg)
"""

import sys, pathlib, json
import pymupdf as fitz
from PIL import Image
import io

# ── Complete card sequence in PDF order ───────────────────────────────────
# 91 pattern cards A-Z, then category cards
# Category order on pages 23-25 needs to be confirmed —
# script will save them as category_p23_br.jpg etc. if CATEGORY_ORDER
# doesn't match. Adjust CATEGORY_ORDER after first run if needed.

PATTERNS = [
    # Page 1
    "Aesthetics of Space", "All Grist for the Mill", "Appreciation", "Appropriate Boundaries",
    # Page 2
    "Balance Process and Content", "Balance Structure and Flexibility", "Breaking Bread Together", "Celebrate",
    # Page 3
    "Challenge", "Circle", "Closing", "Commitment",
    # Page 4
    "Common Ground", "Courageous Modelling", "Deliberate", "Discharging",
    # Page 5
    "Distilling", "Dive In", "Divergence and Convergence Rhythm", "Dwell with Emotions",
    # Page 6
    "Embrace Dissonance and Difference", "Emergence", "Experts on Tap", "Expressive Arts",
    # Page 7
    "Feedback", "Follow the Energy", "Fractal", "Gaia",
    # Page 8
    "Generate Possibilities", "Go Deeper", "Go Meta", "Good Faith Assumptions",
    # Page 9
    "Group Culture", "Guerrilla Facilitation", "Harvesting", "History and Context",
    # Page 10
    "Holding Space", "Honour Each Person", "Hosting", "Improvise",
    # Page 11
    "Inform the Group Mind", "Inquiry", "Invitation", "Iteration",
    # Page 12
    "Letting Go", "Listening", "Magic", "Mapping and Measurement",
    # Page 13
    "Mirroring", "Mode Choice", "Moving toward Alignment", "Naming",
    # Page 14
    "Nooks in Space and Time", "Not about You", "Opening and Welcome", "Playfulness",
    # Page 15
    "Power of Constraints", "Power of Place", "Power Shift", "Preparedness",
    # Page 16
    "Presence", "Priority Focus", "Purpose", "Reflection-Action Cycle",
    # Page 17
    "Rest", "Right Size Bite", "Ritual", "Seasoned Timing",
    # Page 18
    "Seeing the Forest, Seeing the Trees", "Self-Awareness", "Setting Intention", "Shared Airtime",
    # Page 19
    "Shared Leadership and Roles", "Silence", "Simplify", "Spirit",
    # Page 20
    "Story", "Subgroup and Whole Group", "Taking Responsibility", "Tend Relationships",
    # Page 21
    "Time Shift", "Trajectory", "Translation", "Transparency",
    # Page 22
    "Trust the Wisdom of the Group", "Unity and Diversity", "Value the Margins", "Viewpoint Shift",
    # Page 23 (first 3 slots)
    "Whole System in the Room", "Witness with Compassion", "Yes, and",
]

# Category cards — order on pages 23-25 TBD
# Page 23 BR = first category; Pages 24-25 = 8 more
# Adjust this list after checking the actual PDF pages 23-25
CATEGORIES = [
    "Intention", "Context", "Relationship", "Flow", "Creativity",
    "Perspective", "Modelling", "Inquiry & Synthesis", "Faith",
]

CATEGORY_FILENAMES = {
    "Intention":           "intention.jpg",
    "Context":             "context.jpg",
    "Relationship":        "relationship.jpg",
    "Flow":                "flow.jpg",
    "Creativity":          "creativity.jpg",
    "Perspective":         "perspective.jpg",
    "Modelling":           "modelling.jpg",
    "Inquiry & Synthesis": "inquiry_and_synthesis.jpg",
    "Faith":               "faith.jpg",
}

def card_to_filename(name):
    import re
    if name in CATEGORY_FILENAMES:
        return CATEGORY_FILENAMES[name]
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug + ".jpg"

# ── Crop tuning ───────────────────────────────────────────────────────────
# The PDF has an outer margin and a gutter between cards.
# Expressed as fractions of page width/height.
# Adjust these if the black card border is clipped or too much white shows.
#
# OUTER_MARGIN: white space around the outside of the 2x2 grid
# GUTTER:       white space between cards (center gutter, split equally)
#
OUTER_MARGIN_X = 0.02   # left/right page margin
OUTER_MARGIN_Y = 0.02   # top/bottom page margin
GUTTER_X       = 0.02   # horizontal gutter between left and right cards
GUTTER_Y       = 0.02   # vertical gutter between top and bottom cards

# Derived card boundaries (fractions of page)
# Left card:   from OUTER_MARGIN_X  to 0.5 - GUTTER_X/2
# Right card:  from 0.5 + GUTTER_X/2  to 1 - OUTER_MARGIN_X
# Top card:    from OUTER_MARGIN_Y  to 0.5 - GUTTER_Y/2
# Bottom card: from 0.5 + GUTTER_Y/2  to 1 - OUTER_MARGIN_Y

def make_quads(omx, omy, gx, gy):
    lx0, lx1 = omx,         0.5 - gx / 2
    rx0, rx1 = 0.5 + gx/2,  1.0 - omx
    ty0, ty1 = omy,         0.5 - gy / 2
    by0, by1 = 0.5 + gy/2,  1.0 - omy
    return [
        (lx0, ty0, lx1, ty1),  # TL
        (rx0, ty0, rx1, ty1),  # TR
        (lx0, by0, lx1, by1),  # BL
        (rx0, by0, rx1, by1),  # BR
    ]

QUADS = make_quads(OUTER_MARGIN_X, OUTER_MARGIN_Y, GUTTER_X, GUTTER_Y)
QUAD_LABELS = ["TL", "TR", "BL", "BR"]

def render_quadrant(page, quad, dpi=250):
    r = page.rect
    x0 = r.x0 + quad[0] * r.width
    y0 = r.y0 + quad[1] * r.height
    x1 = r.x0 + quad[2] * r.width
    y1 = r.y0 + quad[3] * r.height
    clip = fitz.Rect(x0, y0, x1, y1)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, clip=clip, colorspace=fitz.csRGB, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92, optimize=True)
    return buf.getvalue()

def main():
    if len(sys.argv) < 2:
        print('Usage: python extract_cards.py "GroupWorks-Deck-2019-Download-4up.pdf"')
        sys.exit(1)

    pdf_path = pathlib.Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    out_dir = pathlib.Path("cards")
    out_dir.mkdir(exist_ok=True)

    print(f"\nOpening {pdf_path.name}  ({pdf_path.stat().st_size // 1024} KB)")
    doc = fitz.open(str(pdf_path))
    print(f"Pages: {len(doc)}\n")

    # Build the full slot sequence:
    # 91 patterns fill pages 1-23 (first 3 slots of p23)
    # 9 categories fill p23 BR + p24 all 4 + p25 first 4
    # p26 = blank (skip)
    # p27 = logo back

    # Assign names to each page/quad slot
    slots = {}  # (page_num_0indexed, quad_idx) -> filename

    # Pattern cards: pages 0-21 (4 each) + page 22 first 3
    for i, name in enumerate(PATTERNS):
        page_idx = i // 4
        quad_idx = i % 4
        slots[(page_idx, quad_idx)] = card_to_filename(name)

    # Category cards: page 22 slot 3, then page 23 all 4, then page 24 first 4
    cat_positions = [
        (22, 3),  # page 23 BR
        (23, 0), (23, 1), (23, 2), (23, 3),  # page 24 all
        (24, 0), (24, 1), (24, 2), (24, 3),  # page 25 all
    ]
    for i, name in enumerate(CATEGORIES):
        page_idx, quad_idx = cat_positions[i]
        slots[(page_idx, quad_idx)] = card_to_filename(name)

    # Page 26 (idx 25) = blank, skip
    # Page 27 (idx 26) = logo back — save one copy
    slots[(26, 0)] = "card_back.jpg"

    # Extract
    manifest = {}
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        for qi, (quad, label) in enumerate(zip(QUADS, QUAD_LABELS)):
            key = (page_idx, qi)
            ref = f"p{page_idx+1:02d}-{label}"

            if key not in slots:
                continue  # blank page or extra logo copies

            fname = slots[key]
            jpeg = render_quadrant(page, quad)
            (out_dir / fname).write_bytes(jpeg)
            manifest[fname] = ref
            print(f"  {ref}  →  {fname}")

    doc.close()

    pathlib.Path("cards_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(f"\n{'='*50}")
    print(f"Extracted: {len(manifest)} files → cards/")
    print(f"Manifest:  cards_manifest.json")
    print(f"\nIMPORTANT: Check pages 23-25 category order.")
    print(f"Open the PDF and confirm the category card order matches CATEGORIES list.")
    print(f"If not, edit CATEGORIES in this script and re-run.")

if __name__ == "__main__":
    main()

"""
fix_page22.py — re-split page-22.png into its 4 cards
=======================================================
Usage:
    python fix_page22.py page-22.png

Splits the image into 4 quadrants (top-left, top-right,
bottom-left, bottom-right) and saves them as the four cards
that were mistakenly pulled from page-25 (the blank template):

    top-left     -> whole_system_in_the_room.jpg
    top-right    -> witness_with_compassion.jpg
    bottom-left  -> yes_and.jpg
    bottom-right -> intention.jpg   (category divider - optional)

Adjust the mapping below if your quadrant order differs.
Output goes into cards/ (overwriting the bad files).
"""

import sys, pathlib
from PIL import Image

if len(sys.argv) < 2:
    print("Usage: python fix_page22.py page-22.png")
    sys.exit(1)

src = pathlib.Path(sys.argv[1])
img = Image.open(src).convert("RGB")
w, h = img.size
hw, hh = w // 2, h // 2

quads = {
    "whole_system_in_the_room.jpg": (0,   0,  hw, hh),   # top-left
    "witness_with_compassion.jpg":  (hw,  0,  w,  hh),   # top-right
    "yes_and.jpg":                  (0,   hh, hw, h ),   # bottom-left
    "intention.jpg":                (hw,  hh, w,  h ),   # bottom-right
}

out_dir = pathlib.Path("cards")
out_dir.mkdir(exist_ok=True)

for fname, box in quads.items():
    crop = img.crop(box)
    dest = out_dir / fname
    crop.save(dest, "JPEG", quality=90, optimize=True)
    print(f"  saved cards/{fname}  ({crop.size[0]}x{crop.size[1]})")

print("\nDone. 'intention.jpg' is the category divider, not a deck card -")
print("delete it from cards/ unless you want it for something else.")

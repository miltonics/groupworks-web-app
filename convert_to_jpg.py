"""
convert_to_jpg.py — batch convert card PNGs to JPGs
=====================================================
Usage:
    pip install pillow --break-system-packages
    python convert_to_jpg.py

Run this from the folder containing your PNGs (e.g. ~/Downloads/tiles).
It creates a cards/ subfolder with JPG versions, skipping the
logo/extra/category files that the app doesn't use.
"""

import pathlib
from PIL import Image

SKIP_PREFIXES = ("group_works_logo", "group_works_extra")
SKIP_NAMES = {
    "intention", "context", "relationship", "flow", "creativity",
    "perspective", "modelling", "inquiry_and_synthesis", "faith",
}

src_dir = pathlib.Path(".")
out_dir = pathlib.Path("cards")
out_dir.mkdir(exist_ok=True)

converted = 0
skipped = 0

for png in sorted(src_dir.glob("*.png")):
    stem = png.stem
    if stem.startswith(SKIP_PREFIXES) or stem in SKIP_NAMES:
        skipped += 1
        continue

    img = Image.open(png)
    if img.mode in ("RGBA", "P"):
        bg = Image.new("RGB", img.size, (247, 240, 225))  # match card stock color
        bg.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[-1])
        img = bg
    else:
        img = img.convert("RGB")

    dest = out_dir / (stem + ".jpg")
    img.save(dest, "JPEG", quality=90, optimize=True)
    converted += 1
    print(f"  {png.name}  ->  cards/{dest.name}")

print(f"\nConverted: {converted}")
print(f"Skipped (logos/extras/category tiles): {skipped}")
print(f"\nUpload the cards/ folder next to groupworks.html")

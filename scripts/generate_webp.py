"""
Generate WebP fallbacks for images in the posters/ directory.
Usage: python generate_webp.py

The script will create .webp files next to the originals (e.g. poster.jpg -> poster.webp).
It skips files that already have a webp newer than the source.
Requires Pillow (PIL) to be installed in the environment.
"""
from pathlib import Path
from PIL import Image
import sys

ROOT = Path(__file__).resolve().parents[1]
POSTERS = ROOT / 'posters'

if not POSTERS.exists():
    print(f"Posters directory not found: {POSTERS}")
    sys.exit(1)

count = 0
skipped = 0
errors = 0

for p in sorted(POSTERS.iterdir()):
    if not p.is_file():
        continue
    if p.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
        continue
    webp_path = p.with_suffix('.webp')
    # skip if webp exists and is newer than source
    if webp_path.exists() and webp_path.stat().st_mtime >= p.stat().st_mtime:
        skipped += 1
        continue
    try:
        with Image.open(p) as im:
            # Convert palette images / png with alpha correctly
            if im.mode in ('P', 'RGBA'):
                # Preserve alpha if present
                if 'A' in im.getbands():
                    im = im.convert('RGBA')
                else:
                    im = im.convert('RGB')
            else:
                im = im.convert('RGB')

            # save as webp
            im.save(webp_path, 'WEBP', quality=85, method=6)
        print(f"Created: {webp_path.name}")
        count += 1
    except Exception as e:
        print(f"Error processing {p.name}: {e}")
        errors += 1

print(f"\nDone. Created: {count}, Skipped: {skipped}, Errors: {errors}")

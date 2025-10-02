"""Optimize poster images in the posters/ directory.
Resizes images to a max dimension and recompresses JPEGs to lower quality to save space.
Requires: pillow

Usage:
    python scripts/optimize_posters.py

This script will replace images in-place. It creates backups as .bak before overwriting.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
POSTERS = ROOT / 'posters'

if not POSTERS.exists():
    print('posters/ directory not found.')
    raise SystemExit(1)

MAX_WIDTH = 800
MAX_HEIGHT = 1200
QUALITY = 82

print('Optimizing posters in', POSTERS)
for p in sorted(POSTERS.glob('*.jpg')):
    try:
        print('  Optimizing', p.name)
        img = Image.open(p)
        img = img.convert('RGB')
        img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)
        bak = p.with_suffix(p.suffix + '.bak')
        if not bak.exists():
            p.replace(bak)
            # write optimized to original path
            img.save(p, format='JPEG', quality=QUALITY, optimize=True)
        else:
            # bak exists, just overwrite
            img.save(p, format='JPEG', quality=QUALITY, optimize=True)
    except Exception as e:
        print('  Failed to optimize', p.name, e)
print('Done.')

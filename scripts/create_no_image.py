from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTERS = ROOT / 'posters'
POSTERS.mkdir(parents=True, exist_ok=True)
OUT = POSTERS / 'no-image.jpg'

W, H = 500, 750
BG = (40, 44, 52)
FG = (220, 220, 220)

img = Image.new('RGB', (W, H), color=BG)
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('arial.ttf', 40)
except Exception:
    font = ImageFont.load_default()
text = 'No Image'
try:
    bbox = d.textbbox((0,0), text, font=font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]
except Exception:
    w, h = d.textsize(text, font=font)
    
d.text(((W-w)/2, (H-h)/2), text, font=font, fill=FG)
img.save(OUT, format='JPEG', quality=85)
print('Wrote', OUT)

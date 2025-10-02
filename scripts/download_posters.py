#!/usr/bin/env python3
import json
import os
import re
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOVIES_JSON = ROOT / 'movies.json'
POSTERS_DIR = ROOT / 'posters'
INDEX_HTML = ROOT / 'index.html'
INDEX_LOCAL = ROOT / 'index.local.html'

def safe_name(title):
    name = re.sub(r'[^A-Za-z0-9]+', '-', title).strip('-').lower()
    return name[:60]

def get_ext_from_url(url):
    p = url.split('?')[0]
    if '.' in p:
        ext = os.path.splitext(p)[1]
        if ext.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            return ext
    return '.jpg'


def download(url, outpath, max_size=5 * 1024 * 1024):
    """Download URL to outpath with basic validation (content-type image/* and size limit).
    Returns (ok: bool, error_message_or_None)
    """
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as r:
            ctype = r.headers.get('Content-Type', '')
            if not ctype.startswith('image/'):
                return False, f'Not an image (Content-Type: {ctype})'
            length = r.headers.get('Content-Length')
            if length and int(length) > max_size:
                return False, f'File too large ({length} bytes)'
            data = r.read()
            if len(data) > max_size:
                return False, f'File too large after download ({len(data)} bytes)'
            with open(outpath, 'wb') as f:
                f.write(data)
        return True, None
    except HTTPError as e:
        return False, f'HTTP {e.code}'
    except URLError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def update_index_embedded(movies):
    # Replace content of <script id="movies-data" type="application/json">...</script>
    if not INDEX_HTML.exists():
        print('index.html not found; skipping embedded update')
        return
    txt = INDEX_HTML.read_text(encoding='utf-8')
    pattern = re.compile(r'(<script[^>]+id=["\']movies-data["\'][^>]*>)(.*?)(</script>)', re.S)
    new_json = json.dumps(movies, ensure_ascii=False, indent=2)
    if pattern.search(txt):
        txt = pattern.sub(r"\1\n" + new_json + r"\n\3", txt)
        INDEX_HTML.write_text(txt, encoding='utf-8')
        print('Updated embedded JSON in index.html')
    else:
        print('No embedded movies-data script found in index.html')

    if INDEX_LOCAL.exists():
        txt = INDEX_LOCAL.read_text(encoding='utf-8')
        if pattern.search(txt):
            txt = pattern.sub(r"\1\n" + new_json + r"\n\3", txt)
            INDEX_LOCAL.write_text(txt, encoding='utf-8')
            print('Updated embedded JSON in index.local.html')


def main():
    print('Loading', MOVIES_JSON)
    movies = json.loads(MOVIES_JSON.read_text(encoding='utf-8'))
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    changed = False
    for m in movies:
        poster = m.get('poster')
        title = m.get('title', 'movie')
        name = safe_name(title)

        # Skip if poster already a local file that exists and is not the generic placeholder
        if isinstance(poster, str) and poster.startswith('posters/') and poster != 'posters/no-image.jpg':
            ppath = ROOT / poster
            if ppath.exists():
                print('Local poster exists, skipping:', poster)
                continue

        # We only attempt to find a poster when the current poster is the placeholder
        if poster == 'posters/no-image.jpg' or not poster:
            print(f'Attempting to find poster for: {title}')
            # Try Wikipedia first
            try:
                wiki_title = quote(title.replace(' ', '_'), safe='()')
                wiki_url = f'https://en.wikipedia.org/wiki/{wiki_title}'
                print('Fetching', wiki_url)
                req = Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=20) as r:
                    html = r.read().decode('utf-8', errors='ignore')
            except Exception as e:
                print('Could not fetch Wikipedia page for', title, e)
                html = ''

            image_url = None
            if html:
                # Prefer og:image
                m1 = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
                if m1:
                    image_url = m1.group(1)
                else:
                    # Look for infobox image
                    m2 = re.search(r'<table[^>]+class=["\'][^"\']*infobox[^"\']*["\'][\s\S]*?<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
                    if m2:
                        image_url = m2.group(1)

            # If we didn't find an image, attempt the "(film)" Wikipedia page (handles disambiguation)
            if not image_url:
                try:
                    film_title = f"{title} (film)"
                    wiki_title_film = quote(film_title.replace(' ', '_'), safe='()')
                    wiki_url_film = f'https://en.wikipedia.org/wiki/{wiki_title_film}'
                    print('Trying film page', wiki_url_film)
                    req2 = Request(wiki_url_film, headers={'User-Agent': 'Mozilla/5.0'})
                    with urlopen(req2, timeout=20) as r2:
                        html2 = r2.read().decode('utf-8', errors='ignore')
                    m1 = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html2)
                    if m1:
                        image_url = m1.group(1)
                    else:
                        m2 = re.search(r'<table[^>]+class=["\'][^"\']*infobox[^"\']*["\'][\s\S]*?<img[^>]+src=["\']([^"\']+)["\']', html2, re.I)
                        if m2:
                            image_url = m2.group(1)
                except Exception:
                    pass

            if image_url:
                # Normalize protocol-relative URLs
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):  # relative
                    image_url = 'https://en.wikipedia.org' + image_url

                ext = get_ext_from_url(image_url)
                filename = f'{name}{ext}'
                outpath = POSTERS_DIR / filename

                # Retry download a few times
                attempts = 3
                for attempt in range(1, attempts + 1):
                    print(f'Downloading ({attempt}/{attempts}):', image_url)
                    ok, err = download(image_url, outpath)
                    if ok:
                        m['poster'] = f'posters/{filename}'
                        changed = True
                        print('Downloaded poster for', title)
                        break
                    else:
                        print('Download failed:', err)
                        if attempt < attempts:
                            time.sleep(1 * attempt)
                else:
                    print('All attempts failed for', title)
                    # leave placeholder as-is
            else:
                print('No candidate image found for', title)
                # leave placeholder as-is
        else:
            # If poster is a remote URL (http/https or protocol-relative), try to download it
            if isinstance(poster, str) and (poster.startswith('http://') or poster.startswith('https://') or poster.startswith('//')):
                image_url = poster
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                ext = get_ext_from_url(image_url)
                filename = f'{name}{ext}'
                outpath = POSTERS_DIR / filename
                print('Downloading remote poster for', title)
                ok, err = download(image_url, outpath)
                if ok:
                    m['poster'] = f'posters/{filename}'
                    changed = True
                else:
                    print('Failed to download remote poster for', title, err)
                    # keep existing field
    if changed:
        MOVIES_JSON.write_text(json.dumps(movies, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Updated movies.json to reference local posters')
    else:
        print('No changes to movies.json')
    update_index_embedded(movies)

if __name__ == '__main__':
    main()

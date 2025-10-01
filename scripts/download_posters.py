#!/usr/bin/env python3
import json
import os
import re
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
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


def download(url, outpath):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as r, open(outpath, 'wb') as f:
            f.write(r.read())
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
        url = m.get('poster')
        title = m.get('title','movie')
        name = safe_name(title)
        ext = get_ext_from_url(url) if isinstance(url, str) else '.jpg'
        filename = f'{name}{ext}'
        outpath = POSTERS_DIR / filename
        if outpath.exists():
            print('Exists, skipping:', filename)
            m['poster'] = f'posters/{filename}'
            continue
        print('Downloading:', title, '->', outpath)
        ok, err = download(url, outpath)
        if not ok:
            print('Failed:', title, err)
            # set placeholder remote (not downloading placeholder)
            m['poster'] = 'https://via.placeholder.com/500x750?text=No+Image'
            changed = True
        else:
            m['poster'] = f'posters/{filename}'
            changed = True
    if changed:
        MOVIES_JSON.write_text(json.dumps(movies, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Updated movies.json to reference local posters')
    else:
        print('No changes to movies.json')
    update_index_embedded(movies)

if __name__ == '__main__':
    main()

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOVIES_JSON = ROOT / 'movies.json'

movies = json.loads(MOVIES_JSON.read_text(encoding='utf-8'))

queries = ['spider', 'dragon', 'flash', 'dark', 'xyz']

print('Search tests:')
for q in queries:
    ql = q.lower()
    matches = [m['title'] for m in movies if ql in m['title'].lower()]
    print(f"  query='{q}' -> {len(matches)} matches")
    for t in matches:
        print(f"    - {t}")

print('\nPoster file existence:')
missing = []
for m in movies:
    p = ROOT / m['poster']
    if not p.exists():
        missing.append((m['title'], str(p)))

if not missing:
    print('  All poster files present.')
else:
    print('  Missing posters:')
    for title, path in missing:
        print(f"    - {title}: {path}")

print('\nResponsive/CSS checks:')
index = (ROOT / 'index.html').read_text(encoding='utf-8')
meta_ok = '<meta name="viewport"' in index
grid_ok = 'grid-template-columns:repeat(auto-fit' in index or 'grid-template-columns:repeat(auto-fill' in index
print(f"  viewport meta present: {meta_ok}")
print(f"  responsive grid present: {grid_ok}")

print('\nAccessibility checks:')
# The accessibility attributes are added dynamically in JS. Check for the JS patterns we inject:
tabindex_ok = 'tabIndex' in index or 'card.tabIndex' in index
# role is set via setAttribute('role', 'button') in JS
role_ok = "setAttribute('role'" in index or 'setAttribute("role"' in index or "setAttribute(\"role\"" in index
aria_ok = 'aria-pressed' in index and 'aria-label' in index
print(f"  movie cards have JS tabindex present: {tabindex_ok}")
print(f"  role set via setAttribute present: {role_ok}")
print(f"  aria attributes present: {aria_ok}")

# Modal / details checks
modal_backdrop_ok = 'id="movieModalBackdrop"' in index
modal_dialog_ok = 'role="dialog"' in index or "id=\"movieModal\"" in index
modal_close_ok = 'id="modalClose"' in index
print('\nModal/details checks:')
print(f"  modal backdrop present: {modal_backdrop_ok}")
print(f"  modal dialog present: {modal_dialog_ok}")
print(f"  modal close button present: {modal_close_ok}")

# Movie Finder

This is a simple static Movie Finder site (single-page HTML) that shows a searchable grid of movie posters.

How to view locally
- Open `index.html` (or `Movie Finder.html`) in your browser.
- Or run a local static server from the repository root:

```powershell
cd 'C:\Users\lukej\movie finder\https-jjl04.github.io-movie-finder-'
python -m http.server 8000
# then open http://localhost:8000/ in your browser
```

Publish with GitHub Pages
- Make sure the repository is pushed to GitHub under `JJL04/<repo-name>`.
- In the repo settings -> Pages, set the source to the `main` branch and the `/` (root) folder.
- The site will be available at `https://jjl04.github.io/<repo-name>/` once Pages finishes building.

If you still see a 404 after enabling Pages, confirm:
- The branch and folder selected in Settings -> Pages are correct.
- There is an `index.html` at the repository root.

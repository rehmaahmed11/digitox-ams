# Preview — AMS Light theme, without Blogger

Static HTML previews of [`../ams-blogger-theme.xml`](../ams-blogger-theme.xml) plus screenshots
("shots") of them. Same CSS, same markup as the real theme — only the content is sample data
(post titles, dates, topic counts). Open them before uploading anything to Blogger.

## Open it

| File | Page |
|---|---|
| [`index.html`](index.html) | Homepage — hero, post cards, sidebar |
| [`post.html`](post.html) | Single post — the real AMS Caps Lock OSD post |
| [`label.html`](label.html) | Topic page (`Free tool`) |

Just double-click a file, or serve the repo root:

```bash
python3 theme/tools/build.py serve   # http://localhost:4173/theme/preview/index.html
```

The three pages cross-link from the dark bar at the top. Links that only exist on Blogger
(`/search/label/…`, archive dates, post URLs) point at the live blog paths and won't resolve
in this static preview — that's expected.

## Shots (screenshots, 1280 px desktop / 390 px mobile, full page)

| Shot | Of |
|---|---|
| [`shot-index.png`](shot-index.png) · [`shot-index-mobile.png`](shot-index-mobile.png) | `index.html` |
| [`shot-post.png`](shot-post.png) · [`shot-post-mobile.png`](shot-post-mobile.png) | `post.html` |
| [`shot-label.png`](shot-label.png) | `label.html` |

## Regenerate

```bash
python3 theme/tools/build.py all    # rewrites the 3 HTML files + runs the audit (0 failures)
```

The HTML files are committed on purpose (see the negations in `/.gitignore`) so the theme can
be eyeballed on GitHub — before this, `theme/preview/*` was git-ignored and generated previews
never got pushed. Re-shoot the PNGs after a visual change by screenshotting the served pages.

© 2026 AMS

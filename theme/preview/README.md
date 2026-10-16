# Preview — AMS Editorial theme, without Blogger

Static HTML previews of [`../ams-blogger-theme.xml`](../ams-blogger-theme.xml) plus screenshots
("shots") of them. Same CSS, same markup as the real theme — only the content is sample data
(post titles, dates, topic counts). Open them before uploading anything to Blogger.

## Open it

| File | Page |
|---|---|
| [`index.html`](index.html) | Homepage — hero + stats, lead story, index rows, sidebar |
| [`post.html`](post.html) | Single post — the real AMS Caps Lock OSD post |
| [`label.html`](label.html) | Topic page (`Free tool`) |
| [`responsive.html`](responsive.html) | **All six viewports at once** — 1440 / 1280 / 1024 / 834 / 600 / 390 px |
| [`img/`](img) | Web-sized copies of the images the sample post uses (see *Images*) |

Just double-click a file, or serve the repo root:

```bash
python3 theme/tools/build.py serve
#   /theme/preview/index.html        the theme
#   /theme/preview/responsive.html   the same page in six device frames
```

`responsive.html` renders `index.html` inside a live `<iframe>` at each device width, so the media
queries fire exactly as they do on that screen — it is the fastest way to check a breakpoint change,
and it never goes stale the way a PNG shot does. Below 980 px the frames scale to fit the window
instead of showing their true pixel width.

The links that only exist on Blogger (`/search/label/…`, archive dates, post URLs) point at the live
blog paths and won't resolve in this static preview — that's expected.

## Shots (screenshots, 1280 px desktop / 390 px mobile, full page)

| Shot | Of |
|---|---|
| [`shot-index.png`](shot-index.png) · [`shot-index-mobile.png`](shot-index-mobile.png) | `index.html` |
| [`shot-post.png`](shot-post.png) · [`shot-post-mobile.png`](shot-post-mobile.png) | `post.html` |
| [`shot-label.png`](shot-label.png) | `label.html` |

> **These are still the v2 (AMS Light) shots.** The redesign changed the layout; the sandbox has no
> browser, so they need re-shooting locally: serve the preview, screenshot `index.html` at 1280 px
> and 390 px (full page) plus `post.html` / `label.html`, and save them over the files above. The
> v3 layout is documented in [`../README.md`](../README.md) and visible live in `responsive.html`.

## Images

The audit warns about any image inside the sample post over the blog budget (≤ 1280 px wide,
≤ 120 KB). `theme/preview/img/` holds the exported, web-sized copies and the preview renderer uses
them when present — the same rule a real post must follow:

```bash
python3 theme/tools/build.py images   # re-exports theme/preview/img/ from the post's source images
```

Needs ImageMagick (`convert`). Without it the preview falls back to the original asset and the audit
keeps warning about its byte size.

## Regenerate

```bash
python3 theme/tools/build.py all    # rewrites the HTML + responsive.html + runs the audit (0 failures)
```

The HTML files are committed on purpose (see the negations in `/.gitignore`) so the theme can be
eyeballed on GitHub — before this, `theme/preview/*` was git-ignored and generated previews never
got pushed.

© 2026 AMS

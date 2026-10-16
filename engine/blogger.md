# Engine spec — Blogger / Google post

How the engine produces a blog post for each product. Brand rules: [`BRAND.md`](BRAND.md). Theme: [`theme.md`](theme.md).

## Format (fixed)

| Item | Value |
|---|---|
| Platform | Blogger (Google) — post HTML pasted as-is |
| Length | ~400–600 words |
| SEO title | `AMS ‹Tool› — ‹one-line promise›` (≤ 60 chars) |
| Meta description | 140–160 chars, contains the tool name + the promise |
| Labels (tags) | `AMS`, `Windows`, `Free tool`, `‹Tool category›` |
| Images | Product preview + at least one scene still from the promo video, alt text on every image |
| Links | Setup.exe download · portable exe · YouTube video · AMS YouTube channel |
| Footer | `© 2026 AMS · Subscribe to AMS on YouTube` |

## Structure of every post (in this order)

1. **Hook** — 2–3 sentences on the everyday pain the tool removes (same pain as the video Hook scene).
2. **The problem** — short list of what goes wrong without it (matches the video Problem chips).
3. **Introducing AMS ‹Tool›** — what it is, one paragraph; the real preview image.
4. **What it does** — 4–6 bullets of features (matches the video Features cards).
5. **Install in seconds** — 3 numbered steps (matches the video Install scene); mention: no admin rights, starts with Windows.
6. **Download** — big clear links (Setup.exe, portable exe), system requirements (Windows 10 & 11).
7. **Watch the video** — link to the 65s promo on YouTube.
8. **Footer** — © 2026 AMS + Subscribe link.

## Performance rules (the theme is 100/100, do not spend it in the post)

| Rule | Detail |
|---|---|
| Image width | export at 1280 px wide max for the 720 px reading column (2x), then let Blogger resize |
| Image weight | aim < 120 KB each; WebP or compressed PNG; **no** screenshots straight from the editor |
| Image tags | keep Blogger's `width`/`height`, add `loading='lazy' decoding='async'`, alt text on all |
| Order | the first thing in the post is text (the hook) — never an image, iframe or ad slot |
| Video | link to the promo, embed only *below* the download section; never autoplay |
| Meta description | fill *Search description* in the post editor: the theme passes it straight through |
| Labels | first label = the tab it belongs to (`Free tool`, `Windows`) so the tab bar links stay exact |
| Buttons | `.btn .btn-primary` for the download, `.btn .btn-red` for Subscribe — the theme styles them |
| Nothing else | no inline `<style>`, no `<script>`, no third-party embeds, no `<center>`/`font` tags |

`python3 theme/tools/build.py audit` renders the sample post (`blogger/ams-capslock-osd/post.md`)
through the theme and checks its images, headings and alt text — a post that breaks the budget shows
up there as a `WARN`. Point `POST_MD` at your own `post.md` to check a new one before publishing.

## Voice

Same as everything AMS: friendly, punchy, short sentences, confident (see [`BRAND.md`](BRAND.md) "Voice").
The post closes with the tagline pattern: *"Know your ‹thing›. Every time."*

## Output

→ [`../blogger/<tool>/post.md`](../blogger) — one `post.md` per product, ready to paste into Blogger
(title, meta description, labels and body are all inside; the theme handles the look).

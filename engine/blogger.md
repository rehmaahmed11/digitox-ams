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

## Voice

Same as everything AMS: friendly, punchy, short sentences, confident (see [`BRAND.md`](BRAND.md) "Voice").
The post closes with the tagline pattern: *"Know your ‹thing›. Every time."*

## Output

→ [`../blogger/<tool>/post.md`](../blogger) — one `post.md` per product, ready to paste into Blogger
(title, meta description, labels and body are all inside; the theme handles the look).

# Theme — the AMS blog theme

The installable **Blogger (Google)** theme. `ams-blogger-theme.xml` is **AMS Light**: a clean light
theme built to score **100/100 in every PageSpeed Insights category** (Performance, Accessibility,
Best practices, SEO) on *every* page — with the AMS branding in the tab bar.

| File | What |
|---|---|
| [`ams-blogger-theme.xml`](ams-blogger-theme.xml) | **The theme to install.** Light, zero-JS, inline CSS, tab nav bar. |
| [`legacy-dark-v1.xml`](legacy-dark-v1.xml) | The previous dark glass theme (v1) — kept for reference, not maintained. |
| [`tools/build.py`](tools/build.py) | Renders `preview/` and audits the theme (see *Check it yourself*). |
| `preview/` | Generated static preview pages (`index.html`, `post.html`, `label.html`). |

Production rules: [`../engine/theme.md`](../engine/theme.md) · brand: [`../engine/BRAND.md`](../engine/BRAND.md).

## Install on Blogger

1. Blogger dashboard → **Theme** → the **⋮ / ↓** menu next to *Customise* → **Restore**.
2. Upload `ams-blogger-theme.xml` (Blogger replaces the current theme — export a backup first).
3. **Layout**: the *Page tabs* gadget adds your static pages as tabs; *Search / Topics / Archive*
   sit in the sidebar. The About-AMS card and the Subscribe tab are part of the theme.
4. Set **Header → Title** `AMS` and **Description** to your tagline (e.g.
   *Small tools. Big care.*) — both appear in the bar; the tagline shows from 900 px up.

## What you get

- **Light palette** `#F6F8FC` page / white surfaces, brand blue `#005CD6` for accents and
  `#0050BC` for text-links, deep-red `#C42B25 → #8E1414` only on Subscribe buttons.
- **Tab nav bar** — sticky, brand mark + wordmark on the left, tabs on the right with a 2 px active
  underline, `aria-current` state, horizontally scrollable on phones (no hamburger, so no JS).
- **Text-first LCP** — the biggest painted element is always a headline (hero on the homepage, post
  title on a post), never an image or a font that has to download.
- **Zero requests** — no webfonts, no CDN CSS, no framework, no JS, no third-party embeds. The only
  file is the HTML document itself (inline CSS ≈ 3.9 KB gzipped).
- **CLS 0** — no font swap, `color-scheme: light` locked, marks and buttons size-locked, images carry
  `width`/`height`.
- Contrast-checked for **WCAG AA** on white *and* on the tinted panels, plus labelled search field,
  skip link, `role='list'` on styled lists, ≥44 px touch targets (48 px tabs on phones).
- Post pages: gradient hero band, glass-free flat cards, label chips, `.btn` button styles, print
  stylesheet, `prefers-reduced-motion` respected.

## Why it is fast (the four things that usually cost Blogger blogs their score)

| Normal Blogger page | This theme |
|---|---|
| `widgets.css` — render-blocking, ~28 KB, rarely used | skipped: `<html b:css='false' …>` |
| `widgets.js` — ~120 KB of unused JS, hurts TBT | skipped: `b:js='false'` |
| `@import` Google Fonts — blocks render, shifts layout | no webfont: `'Inter'` is used only if the visitor has it, otherwise the system UI stack |
| Full-size post images above the fold = the LCP element | no thumbnails in lists; post images are lazy + size-locked |

> **One trade-off of `b:js='false'`:** Blogger's own JS widgets stop working — the in-page comment
> form, the image lightbox and the Contact Form gadget. Comments are not rendered by this theme (it
> links out instead). If you want them back, change `b:js='false'` to `b:js='true'` in the second
> line of the theme — you lose ~120 KB of JS and usually 3–8 mobile points.
> `b:css='false'` can also make the **Layout** page look unstyled; the gadgets still drag and drop.

## Check it yourself

```bash
python3 theme/tools/build.py all      # renders preview/ + runs the audit (needs only Python 3)
python3 theme/tools/build.py serve    # http://localhost:4173/theme/preview/index.html
```

The audit resolves the template (every `data:` tag, `b:if`, `b:loop`, `b:include`) and checks the
things Lighthouse fails you on: one `<h1>`, no skipped headings, no duplicate ids, alt + width +
height + `loading` on every image, no font under 12 px, no `@import`/`@font-face`/external URL,
tap-target sizes, WCAG contrast for every palette pair, payload budget, DOM size per page, and the
byte size of the images inside the sample post (that one is content, and it is what usually costs the
last points — today it warns about `preview_ams_v2.png` at 153 KB).

Then measure a real page:

1. Open the preview (or your blog) → DevTools → **Lighthouse** → run *Performance, Accessibility,
   Best practices, SEO* on **Mobile**.
2. Or paste the post URL into <https://pagespeed.web.dev>.
3. Expect: FCP ≈ LCP on the headline, CLS 0.00, TBT 0 ms, 1 request for the document
   (+ your images). Everything below "field data" is lab data — the lab is what you control.

## Getting the last points on real posts

The theme cannot fix content, so follow this in every post (also in
[`../engine/blogger.md`](../engine/blogger.md)):

- **Size images before you insert them.** Max 1280 px wide for the reading column, WebP/PNG under
  ~120 KB. In the post HTML, keep Blogger's `width`/`height` on `<img>` and add
  `loading="lazy" decoding="async"` (Blogger usually does).
- **Use the `=w…` trick** on `blogspot.com` image URLs: `…/s1600/photo.png` → `…/w800/photo.png`.
- **Never** paste a video iframe at the top of a post — put the YouTube *link* in the text, embed
  only below the download section.
- No AdSense units above the fold; ads always cost LCP. If you run ads, expect 70–90, not 100.
- Give every post a **Search description** (Blogger post editor → right rail) — that fills the meta
  description, which the theme can only pass through.
- Turn **off** *Monetize → Ads* / third-party gadgets you do not use; Layout → delete unused gadgets.

## Tweaking

All values live in one `:root` token block at the top of `b:skin`:

| Token | Current | Note |
|---|---|---|
| `--bg` `--surface` `--surface-2` | `#F6F8FC` `#FFFFFF` `#EDF2FA` | page, card, tinted panel |
| `--ink` / `--ink-2` | `#0B1220` / `#3D4757` | body / muted text — **do not lighten** (contrast) |
| `--accent` / `--accent-2` | `#0050BC` / `#003E99` | links, active tab — AA-checked on white and on `--surface-2` |
| `--brand-1` / `--brand-2` | `#409CFF` / `#005CD6` | decorative gradients, the mark, the hairline under the bar |
| `--grad` | `#0B63D6 → #0047B3` | buttons: both ends keep white text ≥ 5.5:1 |
| `--wrap` / `--read` / `--rail` | `1080px` / `720px` / `296px` | grid: hero, reading column, sidebar |
| `--r` / `--r-s` / `--r-l` | `14/10/22px` | radii |

- **Tab bar order/labels:** edit the `<ul class='tablist'>` inside the Header widget's
  `b:includable` — one `<li><a class='tab' …>` per tab (`class='tab on'` marks the active tab;
  Home does it automatically via `data:blog.pageType == "index"`).
- **Brand logo instead of the wordmark:** replace the inline `<svg class='mark'>` with
  `<img alt='AMS' src='…' width='34' height='34'>` — an `<img>` costs one request, the SVG costs none.
- **Want real Inter?** One line in `<head>`, still non-blocking and still no layout shift:
  `<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&amp;display=optional' rel='stylesheet' media='print' onload='this.media="all"'/>`
  (`display=optional` = the font is only used when it is already cached, so first paint never waits;
   `&amp;` is there because the theme file is XML.)
- **Dark variant:** copy the `:root` block into `@media (prefers-color-scheme:dark){…}` and keep the
  same contrast floors (`legacy-dark-v1.xml` has the old palette to borrow from).

© 2026 AMS

# Theme — the AMS blog theme

The installable **Blogger (Google)** theme. `ams-blogger-theme.xml` is **AMS Editorial v3**: a premium
editorial light theme (navy masthead + footer, light reading body, featured lead story, index rows,
sticky sidebar) built to score **100/100 in every PageSpeed Insights category** (Performance,
Accessibility, Best practices, SEO) on *every* page, on **every screen size** — PC, laptop, tablet and
mobile — with the AMS branding in the tab bar.

> v2 (*AMS Light*) was rejected in review as too generic. v3 keeps every performance rule from the
> spec and changes the design system: real typographic scale, asymmetric hero, a lead story, an index
> of hairline rows instead of identical boxes, and five deliberate breakpoints instead of two.

| File | What |
|---|---|
| [`ams-blogger-theme.xml`](ams-blogger-theme.xml) | **The theme to install.** Editorial light, zero-JS, inline CSS, navy tab masthead. |
| [`legacy-dark-v1.xml`](legacy-dark-v1.xml) | The previous dark glass theme (v1) — kept for reference, not maintained. |
| [`tools/build.py`](tools/build.py) | Renders `preview/`, exports web-sized post images, audits the theme (see *Check it yourself*). |
| [`preview/`](preview) | Generated static preview pages (`index`, `post`, `label`) + `responsive.html` (6 device frames) — committed, see [`preview/README.md`](preview/README.md). |

Production rules: [`../engine/theme.md`](../engine/theme.md) · brand: [`../engine/BRAND.md`](../engine/BRAND.md).

## Install on Blogger

1. Blogger dashboard → **Theme** → the **⋮ / ↓** menu next to *Customise* → **Restore**.
2. Upload `ams-blogger-theme.xml` (Blogger replaces the current theme — export a backup first).
3. **Layout**: the *Page tabs* gadget adds your static pages as tabs; *Search / Topics / Archive*
   sit in the sidebar. The About-AMS card and the Subscribe tab are part of the theme.
4. Set **Header → Title** `AMS` and **Description** to your tagline (e.g.
   *Small tools. Big care.*) — both appear in the masthead; the tagline shows from 900 px up.
5. Re-check the three hero numbers in the homepage band (`.band-x`): they are brand claims, not data.

## The layout, per screen

| Width | What changes |
|---|---|
| **≥ 1440 px** — large PC / ultrawide | 1360 px canvas, 48 px gutters, hero headline 64 px, post column 740 px, more air between rows. |
| **1080 – 1439 px** — laptop / desktop | Full editorial grid: feed on the left, **sticky 318 px sidebar** on the right; hero splits into text + a vertical stats rail; post pages centre a 700 px reading column *with* the sidebar beside it. |
| **900 – 1079 px** — tablet landscape / small laptop | Masthead collapses to **one sticky row** (brand left, tabs right); the feed goes **2-up hairline rows**; the sidebar drops *under* the feed as a **2-up widget grid**; post column is capped at 780 px and centred. |
| **560 – 899 px** — tablet portrait / phablet | Single column; 17 px body; hero stats in 3 columns; footer in 2 columns; tabs are a full-bleed scrollable strip (no hamburger — no JS). |
| **< 560 px** — mobile | 16.5 px body, 44–48 px tap targets, hero buttons fill the line, one card per row, sidebar widgets stacked after the content. |

Nothing between the breakpoints is a gap: fluid parts (`--gut`, headline sizes, section padding) use
`clamp()`, so 600 px, 768 px, 1024 px and 1366 px all look intentional rather than interpolated.
Open `preview/responsive.html` to see all six viewports side by side, no screenshots needed.

## What you get

- **Navy chrome, light body** — `#0B1220 → #111E36` masthead and footer around a `#F4F7FC` page with
  white cards; brand blue `#005CD6` for accents, `#0050BC` for text-links, deep red `#C42B25 → #8E1414`
  only on Subscribe. A 2 px `#409CFF → #005CD6` hairline sits under the masthead.
- **Editorial hierarchy** — kicker → headline → standfirst → CTA → three stat claims in the hero;
  the newest post renders as a **lead story** (boxed, larger type, `LATEST` flag) and everything
  below it as **index rows** with a hairline and a 64 px brand underline on hover. Identical boxes
  everywhere was the main thing that made v2 read as a template.
- **Sticky tab masthead** — brand mark + wordmark + tagline on the left, tabs on the right with a 2 px
  active underline, `aria-current`, scrollable strip below 900 px.
- **Text-first LCP** — the biggest painted element is always a headline (hero on the homepage, post
  title on a post), never an image or a font that has to download.
- **Zero requests** — no webfonts, no CDN CSS, no framework, no JS, no third-party embeds. The only
  file is the HTML document itself (inline CSS ≈ 5.1 KB gzipped).
- **CLS 0** — no font swap, `color-scheme: light` locked, marks and buttons size-locked, images carry
  `width`/`height`.
- Contrast-checked for **WCAG AA** on white, on the tinted panels *and* on navy (the audit measures all
  of them), plus labelled search field, skip link, `role='list'` on styled lists, ≥44 px touch targets.
- Post pages: lede-sized first paragraph, ruled `H2`s, tinted blockquote, zebra tables, dark code
  block, label chips, `.btn` styles, print stylesheet, `prefers-reduced-motion` respected.

## Why it is still fast (the four things that usually cost Blogger blogs their score)

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
python3 theme/tools/build.py all      # renders preview/ + responsive.html + runs the audit
python3 theme/tools/build.py images   # re-exports web-sized copies of the post images (needs ImageMagick)
python3 theme/tools/build.py serve    # http://localhost:4173/theme/preview/responsive.html
```

The audit resolves the template (every `data:` tag, `b:if`, `b:loop`, `b:include`) and checks the
things Lighthouse fails you on: one `<h1>`, no skipped headings, no duplicate ids, alt + width +
height + `loading` on every image, no font under 12 px, no `@import`/`@font-face`/external URL,
tap-target sizes, WCAG contrast for **every** palette pair including the navy chrome, the inline-CSS
budget, DOM size per page, and the byte size of the images inside the sample post. Today:
**72 passed, 0 warnings, 0 failures**.

Then measure a real page:

1. Open the preview (or your blog) → DevTools → **Lighthouse** → run *Performance, Accessibility,
   Best practices, SEO* on **Mobile**.
2. Or paste the post URL into <https://pagespeed.web.dev>.
3. Expect: FCP ≈ LCP on the headline, CLS 0.00, TBT 0 ms, 1 request for the document
   (+ your images). Resize DevTools to 768 px / 1024 px / 1440 px — the layout should never look
   stretched, squeezed or half-empty.

## Getting the last points on real posts

The theme cannot fix content, so follow this in every post (also in
[`../engine/blogger.md`](../engine/blogger.md)):

- **Size images before you insert them.** Max 1280 px wide for the reading column, WebP/PNG under
  ~120 KB. `build.py images` shows the export recipe the preview uses.
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
| `--bg` `--surface` `--surface-2` | `#F4F7FC` `#FFFFFF` `#EDF2FA` | page, card, tinted panel |
| `--navy` `--navy-2` | `#0B1220` `#111E36` | masthead + footer gradient ends |
| `--on-navy` / `--on-navy-2` | `#DCE6F5` / `#9ECBFF` | text on navy — both AA-checked, never lighten |
| `--ink` / `--ink-2` / `--ink-3` | `#0B1220` / `#3D4757` / `#5A6577` | body / muted text / placeholder — **do not lighten** (contrast) |
| `--accent` / `--accent-2` | `#0050BC` / `#003E99` | links, `LATEST` flag — AA-checked on white and on `--surface-2` |
| `--brand-1` / `--brand-2` | `#409CFF` / `#005CD6` | decorative gradients, the mark, the hairline under the bar |
| `--grad` / `--grad-red` / `--mark` | blue / red / brand | buttons: both ends keep white text ≥ 5.5:1 |
| `--wrap` / `--read` / `--rail` | `1240px` / `700px` / `318px` | canvas, reading column, sidebar (all re-set at 1440 px) |
| `--gut` / `--bar` | `clamp(18px,4.4vw,44px)` / `62px` | side padding, masthead height (also = sticky offset) |
| `--r` / `--r-s` / `--r-l` | `14/9/20px` | radii |

- **Which post is the lead?** The theme styles the *first* card of a homepage feed
  (`.is-lead > :first-child`), so it is always your newest post — no markup to keep in sync. Drop
  the `is-lead` from `<div expr:class='data:view.isHomepage ? "feed is-lead" : "feed"'>` for a flat
  index of rows on every page.
- **Tab bar order/labels:** edit the `<ul class='tablist'>` inside the Header widget's
  `b:includable` — one `<li><a class='tab' …>` per tab (`class='tab on'` marks the active tab;
  Home does it automatically via `data:blog.pageType == "index"`). Static pages come from the
  *Page tabs* gadget.
- **Brand logo instead of the wordmark:** replace the inline `<svg class='mark'>` with
  `<img alt='AMS' src='…' width='36' height='36'>` — an `<img>` costs one request, the SVG costs none.
- **Want real Inter?** One line in `<head>`, still non-blocking and still no layout shift:
  `<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&amp;display=optional' rel='stylesheet' media='print' onload='this.media="all"'/>`
  (`display=optional` = the font is only used when it is already cached, so first paint never waits;
   `&amp;` is there because the theme file is XML.)
- **Dark variant:** copy the `:root` block into `@media (prefers-color-scheme:dark){…}` and keep the
  same contrast floors (`legacy-dark-v1.xml` has the old palette to borrow from).

© 2026 AMS

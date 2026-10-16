# Engine spec — blog theme

How the engine produces / updates the AMS blog theme. Brand rules: [`BRAND.md`](BRAND.md).

## What the theme is

The visual theme of the **AMS blog on Blogger (Google)**: one installable XML file that makes every
post look like AMS — **light**, quiet surfaces, brand blue, tab nav bar, and a PageSpeed-Insights
score of 100 in all four categories on every page.

→ Lives in [`../theme/`](../theme): `ams-blogger-theme.xml` (install this), `legacy-dark-v1.xml`
(the old dark glass look, reference only), `tools/build.py` (preview renderer + audit), `README.md`
(install, tweaks, how to measure).

## Rules

| Item | Value |
|---|---|
| Background / surfaces | `#F6F8FC` page, `#FFFFFF` card, `#EDF2FA` tinted panel |
| Text | `#0B1220` body, `#3D4757` muted — both are AA-checked, never lighten |
| Accent | brand gradient `#409CFF → #005CD6` for decoration; links/active tab `#0050BC` |
| Buttons | pill; primary `#0B63D6 → #0047B3`, Subscribe `#C42B25 → #8E1414` (white text ≥ 4.5:1) |
| Type | Inter if installed locally, otherwise the system UI stack. Body ≥ 16 px, nothing under 12 px |
| Header | sticky bar: brand mark + `AMS` wordmark (+ tagline from ≥900 px) and a **tab nav bar** |
| Tabs | `Home · Free tools · Windows · <your pages> · Subscribe`; 2 px active underline; scrollable strip on phones |
| Cards | flat white, 1 px `#E2E8F2` border, radius 14/22, soft shadow — no glass, no blur |
| Footer | `© 2026 AMS` + YouTube link + Back to top |
| Feel | premium, light, minimal, editorial |

## Performance budget (hard limits — the audit in `../theme/tools/build.py` enforces them)

| Budget | Why |
|---|---|
| 0 external requests: no webfont, no CDN CSS, no framework, no embeds | every extra request is a round trip before paint |
| 0 bytes of JavaScript, `b:js='false'` + `b:css='false'` | skips Blogger's `widgets.js` + `widgets.css` |
| all CSS inline in `b:skin`, ≤ 4.6 KB gzipped | fits the first round trip (≈10 × 1.4 KB) |
| LCP must be a text node (hero headline / post title) | text paints from the inline CSS; images and fonts do not |
| No thumbnails in post lists | list pages stay text-only → instant, and no image requests |
| CLS 0: `color-scheme:light`, no `@font-face`, `width`/`height` on images | no swap, no reflow |
| ≤ 400 rendered elements per page | small DOM = cheap style/layout |
| Every palette pair passes WCAG AA (4.5:1 text, 3:1 large) | Accessibility 100 |
| ≥ 44 px touch targets (48 px tabs on mobile) | usable on a phone, and Lighthouse checks it |
| Content rule: post images ≤ 1280 px wide, ≤ ~120 KB, `loading='lazy'`, alt text | content, not the theme, is what usually breaks LCP |

> Trade-off to remember: `b:js='false'` disables Blogger's own comment form, image lightbox and
> Contact Form gadget. Set it back to `true` if the blog ever needs real comments (cost: ~120 KB JS).

## When it changes

- A **new brand detail** (colour, font, element) → update [`BRAND.md`](BRAND.md) first, then the theme.
- A **layout request** (new tab, a downloads strip, another widget) → change only the theme.
- After any edit: `python3 theme/tools/build.py all` must finish with **0 failures**, and every
  `WARN` cleared or explained (a warning is usually a post image over budget). Then re-upload
  `ams-blogger-theme.xml` to Blogger and re-run PageSpeed Insights on one post.

## Update checklist

- [ ] `python3 theme/tools/build.py all` → `RESULT: … 0 failures` (it renders index, post and topic pages)
- [ ] Valid Blogger XML (layouts v3): `b:skin` + `Header`, `Blog`, `PageList`, `Label`, `BlogSearch`, `BlogArchive`
- [ ] `b:css='false' b:js='false' b:responsive='true' b:defaultwidgetversion='2' b:layoutsVersion='3'`
- [ ] One `<h1>` per page, no skipped heading levels, unique ids, labelled form fields
- [ ] Mobile: tab strip scrolls, single column under 1000 px, tap targets ≥ 44 px
- [ ] Contrast of any new colour checked against **both** `#FFFFFF` and `#EDF2FA`
- [ ] Install + tweak notes in [`../theme/README.md`](../theme/README.md) still correct

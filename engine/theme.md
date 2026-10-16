# Engine spec — blog theme

How the engine produces / updates the AMS blog theme. Brand rules: [`BRAND.md`](BRAND.md).

## What the theme is

The visual theme of the **AMS blog on Blogger (Google)**: one installable XML file that makes every
post look like AMS — dark glass surfaces, accent blue, Inter font, the same feel as the software and videos.

→ Lives in [`../theme/`](../theme): `ams-blogger-theme.xml` (the installable theme) + `README.md` (install steps).

## Rules (taken from [`BRAND.md`](BRAND.md))

| Item | Value |
|---|---|
| Background | `#06080F` (dark base) |
| Cards / panels | `#282A30 → #18191D` glass, thin white 18% border, soft shadow, radius 16–26 |
| Accent | gradient `#409CFF → #005CD6`, text accent `#8CD1FF` |
| Headlines | Inter Display / Inter ExtraBold |
| Body | Inter Regular / Medium |
| Buttons | pill-shaped, accent gradient primary ("Download now"), red `#FF2626 → #CC0000` for "Subscribe" |
| Footer | `© 2026 AMS` + YouTube link |
| Feel | premium, dark, minimal — matches the app UI and the videos |

## When it changes

- A **new brand detail** (color, font, element) → update [`BRAND.md`](BRAND.md) first, then apply it to the theme.
- A **layout request** (e.g. "add a downloads page section") → change only the theme, log it in [`instructions.md`](instructions.md).

## Update checklist

- [ ] Valid Blogger XML (Layouts v3): `b:skin` CSS + `Header`, `Blog`, `PageList`, `Label`, `Attribution` widgets
- [ ] Mobile-responsive (viewport meta, single-column below 800px)
- [ ] Post typography matches the brand table above
- [ ] Install steps in [`../theme/README.md`](../theme/README.md) still correct

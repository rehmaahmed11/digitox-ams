# AMS Brand Kit

## Identity
| Item | Value |
|---|---|
| Brand | **AMS** |
| Product naming | `AMS <Tool Name>` (e.g. *AMS Caps Lock OSD*) |
| Publisher / Company | AMS |
| Copyright | © 2026 AMS |
| YouTube | https://www.youtube.com/channel/UCW5b5zJ1MW35P1x9--ExMvg |

## Colors
| Role | Hex | Use |
|---|---|---|
| Accent blue (light) | `#409CFF` | gradients (top), highlights, glows |
| Accent blue (deep) | `#005CD6` | gradients (bottom), buttons |
| Accent text light | `#8CD1FF` | gradient ends on headlines |
| Background (video) | `#06080F` | dark base with blue/violet light blobs |
| Card / OSD dark | `#28 2A 30` → `#18 19 1D` | glass cards, 94% opacity |
| Problem red | `#FF545C` | the "pain" scenes only |
| YouTube red | `#FF2626` → `#CC0000` | Subscribe button |

### Blog (light theme)

The blog is **light** (readability + PageSpeed); the apps, videos and OSD stay dark. Same brand blues.

| Role | Hex | Use |
|---|---|---|
| Page / card / tint | `#F6F8FC` · `#FFFFFF` · `#EDF2FA` | light surfaces |
| Text | `#0B1220`, muted `#3D4757` | body / meta — fixed contrast floors, never lighten |
| Link + active tab | `#0050BC` (hover `#003E99`) | AA-checked on white and on the tint |
| Brand gradient | `#409CFF → #005CD6` | the mark, the 2 px hairline under the bar, glows |
| Button gradient | `#0B63D6 → #0047B3` | Download / primary |
| Subscribe gradient | `#C42B25 → #8E1414` | YouTube only |

**Contrast rule (brand-wide for the blog):** every text/background pair must pass WCAG AA (4.5:1,
3:1 for large text) on *both* white and `#EDF2FA`. `theme/tools/build.py audit` checks the table.
**Never** put white text on `#409CFF` (2.6:1) and never use gradient-filled text on the blog.

## Typography
- **Inter Display Black**: headlines.
- **Inter** (Regular / Medium / SemiBold / Bold): body text and UI.
- Small labels in capitals with wide letter-spacing (e.g. `F E A T U R E S`).
- Inside the apps on Windows: Segoe UI.
- **On the blog:** `'Inter'` first in the stack but *no webfont file* — a visitor with Inter installed
  sees Inter, everyone else sees the system UI font. Same look, one less render-blocking request.

## App UI style
- Dark rounded "glass" card (radius 26), soft shadow, thin white 18% border, top highlight.
- Blue gradient circle badge for "ON/active", grey outline for "OFF/inactive".
- Small **A M S** footer on popups (blue when active, grey when inactive).
- Motion: fade in 170 ms (ease-out), hold, fade out 420 ms (ease-in-out), slight zoom 0.94→1 and a 14 px upward slide.
- Click-through, never takes focus, adapts to screen scaling (DPI-aware), shows on the monitor where the mouse is.

## Blog style (light)
- Flat white cards on `#F6F8FC`, 1 px `#E2E8F2` border, radius 14 (cards) / 22 (article), soft
  low-shadow. No glass, no blur, no glow on the blog.
- Sticky top bar: mark + `AMS` wordmark left, **tabs** right (2 px brand underline on the active tab,
  scrollable strip on phones — never a hamburger menu).
- Headline first, always: the hero on the homepage and the post title on a post are the largest
  painted elements (that is what makes LCP fast).
- Buttons: pill, 46 px tall, one primary per block; Subscribe in brand red.
- © 2026 AMS + YouTube link + Back to top in the footer.

## App icon
Rounded square (radius 22%) with a blue gradient `#409CFF → #005CD6` and a white glyph. Tray icon: blue when active, grey when inactive.

## Installer rules
Per-user (no admin) · AMS banner + header images · title "‹Tool› Setup – by AMS" · Start menu folder **AMS** · Apps & Features publisher **AMS** + YouTube help link · **opens the YouTube channel once after install and once after uninstall**.

## Voice
- Official AMS voice: **masculine, confident advertising narrator, English**.
- Reference clips: [`voice/ams-voice-reference.wav`](voice/ams-voice-reference.wav), [`voice/ams-voice-sample-demo.wav`](voice/ams-voice-sample-demo.wav).
- Tone: friendly, punchy, short sentences, with a pause before the product name ("Introducing… AMS ‹Tool›.").

## Video signature
- Opens on a relatable problem, the product name is revealed with a flash + boom at 0:18, and it ends on **Download now** + **Subscribe to AMS**.
- AMS corner logo (top-right) from the demo through the install scene.
- Tagline pattern: *"Know your ‹thing›. Every time."*

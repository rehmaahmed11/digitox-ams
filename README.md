# digitox-ams — AMS production system

AMS's factory for small software tools and everything that promotes them:
**one engine** (all the logic, branding and rules) → **four output areas** (software, videos, posts, theme).

```
                 ┌──────────────────────────────────────────────┐
   you give a    │                  E N G I N E                 │   the product
   task ───────► │  brand · workflow · instructions · specs     │ ─────────────► appears in
                 │  (engine/ — updated whenever you instruct)   │   the right folder
                 └──────────────────────────────────────────────┘
        │                    │                    │                    │
        ▼                    ▼                    ▼                    ▼
 software/pc         software/mobile      promotional-video/        blogger/  +  theme/
 (apps for           (apps for            (65s AMS-style            (Google posts +
  Windows)            Android/iOS)          commercials)             the blog look)
```

## The parts

| Folder | What lives there | Produced so far |
|---|---|---|
| [`engine/`](engine) | **All production logic**: brand kit, workflow, instruction log, specs for software / video / posts / theme, build environment, official voice | — (it produces the rest) |
| [`software/pc/`](software/pc) | Windows apps: source, installer, assets, ready `release/` | [`ams-capslock-osd`](software/pc/ams-capslock-osd) — AMS Caps Lock OSD |
| [`software/mobile/`](software/mobile) | Android / iOS apps | *(next)* |
| [`promotional-video/`](promotional-video) | Promo videos + the code that renders them | [`ams-capslock-osd`](promotional-video/ams-capslock-osd) — 65s commercial |
| [`blogger/`](blogger) | Ready-to-publish Blogger / Google posts | [`ams-capslock-osd`](blogger/ams-capslock-osd/post.md) |
| [`theme/`](theme) | The AMS blog theme (Blogger XML) + its preview / audit kit | **AMS Editorial v3** — [`ams-blogger-theme.xml`](theme/ams-blogger-theme.xml) |
| [`archive/`](archive) | Original uploads, kept unchanged | — |

## How it works

1. **A task comes in** — e.g. *"Make a PC tool: …"*, *"Make the promo video for …"*, *"Write the blog post for …"*.
   A task may ask for **one part alone** — only that part is produced.
2. **The engine produces** — it follows [`engine/WORKFLOW.md`](engine/WORKFLOW.md),
   [`engine/BRAND.md`](engine/BRAND.md) and the matching spec (`engine/software/pc.md`, `engine/video.md`, …).
3. **The product lands** in the matching folder under its own name (e.g. `ams-capslock-osd`), so the
   software, video and post of one product always match up.
4. **New instructions** ("make headers bigger", "always add a donate button", …) are recorded in
   [`engine/instructions.md`](engine/instructions.md) and folded into the rule files — from then on
   every product follows them. That is the engine's job: producing, and staying current.

## Products

| # | Product | What it does | Software | Video | Post |
|---|---|---|---|---|---|
| 1 | **AMS Caps Lock OSD** | Clean popup fades in/out whenever Caps Lock turns ON/OFF. Starts with Windows. | [Setup.exe](software/pc/ams-capslock-osd/release/AMS-CapsLockOSD-Setup.exe) · [portable](software/pc/ams-capslock-osd/release/CapsLockOSD.exe) | [65s promo](promotional-video/ams-capslock-osd) | [post](blogger/ams-capslock-osd/post.md) |

▶ **AMS on YouTube:** https://www.youtube.com/channel/UCW5b5zJ1MW35P1x9--ExMvg

## Build everything

```bash
./engine/setup/setup_linux.sh                       # once: compilers, NSIS, ffmpeg, fonts, Python libs

./software/pc/ams-capslock-osd/build_linux.sh       # -> software/pc/ams-capslock-osd/release/*.exe
./promotional-video/ams-capslock-osd/build_video.sh # -> promotional-video/ams-capslock-osd/output/*.mp4
python3 theme/tools/build.py all                    # -> theme/preview/*.html + the 100/100 audit
```

## Ask for the next product

> Make a **PC tool** for the digitox-ams repo following engine/WORKFLOW.md and engine/BRAND.md: *‹describe it›*.
>
> Make the promo video for **‹tool›** following engine/WORKFLOW.md.
>
> Write the Blogger post for **‹tool›** following engine/blogger.md.
>
> Redesign / tune the blog theme following engine/theme.md (it must keep the audit at 0 failures).
>
> New instruction: *‹rule›* — update the engine.

Full sequence and templates: [`engine/WORKFLOW.md`](engine/WORKFLOW.md).

© 2026 AMS

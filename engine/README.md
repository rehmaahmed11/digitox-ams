# Engine — the production brain

The **engine** holds every rule, brand detail and build tool used to *produce* AMS products.
It does not contain products itself — it **makes** them.

```
A task comes in  →  engine reads its rules  →  a product appears in the right folder
```

| Task given | What the engine produces | Where it lands |
|---|---|---|
| "Make a PC tool: …" | Windows software (source + installer + release) | [`../software/pc/`](../software/pc) |
| "Make a mobile app: …" | Mobile software | [`../software/mobile/`](../software/mobile) |
| "Make the promo video for …" | 65s AMS-style promo video | [`../promotional-video/`](../promotional-video) |
| "Write the blog post for …" | Blogger / Google post | [`../blogger/`](../blogger) |
| "Update the theme: …" | Blog theme | [`../theme/`](../theme) |

A task may ask for **one part alone** (software only, video only, …) — produce only that part.
Every produced part is named after its product (e.g. `ams-capslock-osd`), so the software,
video, and post of one product always match up.

## What lives in this folder

| File / folder | What it is |
|---|---|
| [`BRAND.md`](BRAND.md) | The AMS brand kit — identity, colors, fonts, voice, UI style, installer rules. **All branding details live here.** |
| [`WORKFLOW.md`](WORKFLOW.md) | The production sequence — the order every product is made in. |
| [`instructions.md`](instructions.md) | **The instruction log.** New guidance from the user is recorded here first, then folded into the right rule file. |
| [`voice/`](voice) | Reference clips of the official AMS voice (used to match AI narration). |
| [`setup/`](setup) | One-time install of the build environment (Linux): compilers, NSIS, ffmpeg, fonts, Python libs. |
| [`software/pc.md`](software/pc.md) | How to produce PC (Windows) software. |
| [`software/mobile.md`](software/mobile.md) | How to produce mobile software. |
| [`video.md`](video.md) | How to produce a promotional video. |
| [`blogger.md`](blogger.md) | How to produce a Blogger / Google post. |
| [`theme.md`](theme.md) | How to produce / update the blog theme. |

## How the engine updates (important)

When you give a **new instruction** (a rule change, a new brand detail, a new preference):

1. Add it to [`instructions.md`](instructions.md) with the date and what it changes.
2. Update the matching rule file (`BRAND.md`, `WORKFLOW.md`, `software/pc.md`, `video.md`, …).
3. From then on, **every** production run follows the updated rules — old products are only touched when you ask.

The engine's whole job is producing; keeping these files correct is what keeps every product consistent.

## Produce in one line

```bash
# after the engine has produced a product, rebuild it any time with:
./engine/setup/setup_linux.sh                    # once, on a fresh machine

./software/pc/<tool>/build_linux.sh              # -> software/pc/<tool>/release/*.exe
./promotional-video/<tool>/build_video.sh        # -> promotional-video/<tool>/output/*.mp4
```

# AMS Workflow — the sequence for every product

Every AMS product is made in the **same order**, so all software, videos and posts look and feel like one brand.

```
 PHASE 1: SOFTWARE          PHASE 2: VIDEO               PHASE 3: PUBLISH
 ─────────────────          ──────────────               ────────────────
 1. Idea / request          6. Storyboard + script       11. Push to GitHub
 2. Build software          7. Voice-over (AMS voice)    12. Update README product table
 3. AMS branding            8. Images / assets           13. Upload video to YouTube
 4. Installer               9. Music + SFX + mix         14. Publish the blog post
 5. Test + release         10. Render + review
```

> Rule: **the software comes first**, then (in a separate request) the video and the post.
> The video and the post always show the *real* product's UI and real download link.

A task may cover only one phase — produce only what was asked.

---

## Phase 1 — Make the software (`software/pc/<tool>/` or `software/mobile/<tool>/`)

Details: [`software/pc.md`](software/pc.md) · [`software/mobile.md`](software/mobile.md) · brand rules: [`BRAND.md`](BRAND.md)

| Step | What happens | Output |
|---|---|---|
| 1. Idea | You describe the tool in one or two sentences (what it does, when it shows up). | — |
| 2. Build | Simple, light app. On PC: **C# / WinForms, .NET Framework 4.x** (built into Windows 10/11, so no runtime to install). Lives in the tray, one instance only, uses very little CPU. | `src/` |
| 3. Branding | Name format **"AMS ‹Tool Name›"**, publisher **AMS**, © AMS, AMS label in the UI, tray menu with **"AMS on YouTube"**. See [BRAND.md](BRAND.md). | icons, `assets/` |
| 4. Installer | Per-user install (**no admin needed**), Start menu folder **AMS**, starts with Windows, appears in Apps & Features, **opens the AMS YouTube channel once when install finishes and once when uninstall finishes.** | `installer/installer.nsi` |
| 5. Release | Build with `build_linux.sh` (Linux) or `build.bat` (Windows). Test, then commit the release files. | `release/` |

### Folder template (produced software)

```
software/pc/<tool>/
├── README.md               overview, install, decisions
├── src/                    source code
├── installer/              installer.nsi
├── assets/                 app.ico, icon PNGs, wizard.bmp (164x314), header.bmp (150x57), preview image
├── tools/                  helper code (e.g. icon generator)
├── build_linux.sh          cross-build on Linux (mono + nsis)
├── build.bat               build on Windows (built-in csc.exe)
└── release/                ‹Tool›.exe + AMS-‹Tool›-Setup.exe
```

---

## Phase 2 — Make the video (`promotional-video/<tool>/`)

Details: [`video.md`](video.md)

**Fixed format (same for every tool):** 65 seconds · 16:9 · 1920×1080 · 30 fps · H.264 + AAC 48 kHz · loudness −14 LUFS.

### 6. Storyboard: the 7-scene AMS structure
| # | Scene | Time | Purpose |
|---|---|---|---|
| 1 | **Hook** | 0–8s | Show the everyday pain in action (a relatable moment), ending on a short question in big text. |
| 2 | **Problem** | 8–18s | Lifestyle photo + 3 problem "chips" + a punchline in two lines (white + accent gradient). Builds up to the reveal. |
| 3 | **Reveal** | 18–24s | Flash + boom; app icon springs in, then light rays, "INTRODUCING", **AMS ‹Tool›** title and a one-line tagline. |
| 4 | **Demo** | 24–36s | Realistic Windows desktop showing the **real UI** of the tool, labels pointing at key features, then a zoomed beauty shot with a caption. |
| 5 | **Features** | 36–50s | Title plus 6 feature cards (3×2) appearing in time with the voice-over. |
| 6 | **Install** | 50–56s | "Up and running in seconds." 3 steps getting checkmarks, an AMS installer mock, and badges. |
| 7 | **CTA** | 56–65s | Icon, title, tagline, **Download now** and **Subscribe to AMS** buttons, YouTube URL, © AMS, fade out. |

### 7–10. Voice-over, images, audio, render
- **Voice-over**: always the **official AMS voice** (masculine, advertising style, English). Reference clips: [`voice/`](voice). One clip per scene (`s1`–`s7`), about 45 s of speech in total.
- **Images**: 3 AI images, 16:9, no text or logos (problem photo, abstract wallpaper, premium desk).
- **Audio**: music **synthesized in code** (no copyright issues): 120 BPM, A minor → Am–F–C–G. SFX: key clicks, chimes, whooshes, boom, pops, dings. Music ducks under the voice; master normalised to −14 LUFS.
- **Render + review**: `render.py still <times>` → review frames, fix anything off, then `build_video.sh` → final mp4.

### Folder template (produced video)

```
promotional-video/<tool>/
├── README.md           storyboard, script, prompts, decisions
├── timeline.py         all timings (scenes, VO starts, key moments) — single source of truth
├── audio.py            music + SFX synthesis + voice-over mix
├── render.py           motion-graphics renderer (one function per scene)
├── build_video.sh      one command to rebuild the mp4
├── vo/                 voice-over clips s1..s7.wav
├── img/                AI-generated photos/backgrounds
├── stills/             preview frames used for review
└── output/             final mp4
```

---

## Phase 3 — Publish

Details: [`blogger.md`](blogger.md) · [`theme.md`](theme.md)

11. Commit the product to this repo (software + video + post).
12. Add the product to the table in the root `README.md`.
13. Upload the mp4 to YouTube; put the Setup.exe link in the description.
14. Publish the post on the AMS blog (Blogger/Google) using [`../theme/`](../theme).

---

## How to ask for the next product (copy and paste)

**Step A — software:**
> Make a **PC tool** for the digitox-ams repo following engine/WORKFLOW.md and engine/BRAND.md: *‹describe the tool›*.

**Step B — video (after the software is done):**
> Make the promo video for **‹tool›** following engine/WORKFLOW.md — same 7-scene style, same AMS voice (match `engine/voice/ams-voice-reference.wav`), 65s 16:9. Push to `promotional-video/<tool>/`.

**Step C — post (after the video is done):**
> Write the Blogger post for **‹tool›** following engine/blogger.md. Push to `blogger/<tool>/`.

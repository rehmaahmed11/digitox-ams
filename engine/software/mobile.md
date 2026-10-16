# Engine spec — mobile software

How the engine produces mobile software. Brand rules: [`../BRAND.md`](../BRAND.md). Order: [`../WORKFLOW.md`](../WORKFLOW.md).

> No mobile tool has been produced yet. This spec fixes the **brand and structure** in advance;
> the technology is chosen per task (see below).

## Stack (chosen per task)

| Task type | Default choice |
|---|---|
| Android app | **Kotlin + Jetpack Compose** (or Flutter, if one codebase for Android + iOS is asked) |
| iOS app | SwiftUI (needs a Mac/Xcode to build the release) |
| Both stores | Flutter |

The choice is made when the task arrives and then recorded in the product's `README.md`.

## Rules every mobile tool follows

1. **Name**: `AMS ‹Tool Name›` (store title), same identity as PC: publisher **AMS**, © 2026 AMS.
2. **Behavior**: light, quiet, no login, no ads; the tool does exactly what the task says.
3. **UI style**: follows [`../BRAND.md`](../BRAND.md) — dark "glass" surfaces, accent blue `#409CFF → #005CD6`, small **A M S** credit in the About screen.
4. **Store presence**: app icon from the same glyph system as PC (rounded square, blue gradient, white glyph); screenshots and listing text written in the AMS voice.
5. **Release**: commit source + a `release/` folder with the built artifact (`.apk` / `.aab` / `.ipa`) and the store listing draft.

## Output

→ [`../../software/mobile/<tool>/`](../../software/mobile)

## Folder template

```
software/mobile/<tool>/
├── README.md          what it does, tech chosen, how to build
├── src/               the app project
├── assets/            icon, screenshots, store graphics
├── release/           built artifact + store listing draft
```

## New tool checklist

- [ ] Tech choice recorded in README
- [ ] Branding: AMS name, © AMS, About credit
- [ ] Builds from source, release artifact committed
- [ ] Store listing draft (title, short + full description, screenshots)
- [ ] Added to the root `README.md` product table

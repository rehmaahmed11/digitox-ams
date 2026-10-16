# Engine spec — PC (Windows) software

How the engine produces PC software. Brand rules: [`../BRAND.md`](../BRAND.md). Order: [`../WORKFLOW.md`](../WORKFLOW.md).

## Stack (fixed)

| Choice | Why |
|---|---|
| **C# / WinForms on .NET Framework 4.x** | Built into every Windows 10/11 PC: no runtime download, small exe (~130 KB). |
| Built on Linux with **Mono `mcs`** | No Windows machine needed to build; `build.bat` also rebuilds on Windows with the built-in `csc.exe`. |
| **NSIS** installer, per-user (HKCU, `%LOCALAPPDATA%`) | **No admin rights**, no UAC prompt. |
| Cross-build entry point: `build_linux.sh` | One command → `release/` (exe + Setup.exe). Requires [`../setup/setup_linux.sh`](../setup/setup_linux.sh). |

## Rules every PC tool follows

1. **Name**: `AMS ‹Tool Name›`. Publisher **AMS**, © 2026 AMS, version in the assembly and installer.
2. **Behavior**: lives in the **system tray**, **single instance** (named mutex), **very low CPU**, DPI-aware.
3. **UI style**: dark rounded "glass" card (see [`../BRAND.md`](../BRAND.md) "App UI style") with the small **A M S** footer; motion timings 170 ms fade-in / hold / 420 ms fade-out by default.
4. **Tray menu**: tool title (disabled) → **Start with Windows** (checkable, HKCU Run key) → **Show preview** → **AMS on YouTube** → Exit.
5. **Installer** (see [`../BRAND.md`](../BRAND.md) "Installer rules"): AMS banner + header images, Start menu folder **AMS**, Apps & Features publisher **AMS** + YouTube help link, **opens the AMS YouTube channel exactly once after install and once after uninstall**.
6. **Assets** generated from code where possible (`tools/Gen.cs` style), so icons and previews can be regenerated: `app.ico`, icon PNGs 16–256, `wizard.bmp` 164×314, `header.bmp` 150×57, one preview image.
7. **Release**: commit `release/‹Tool›.exe` + `release/AMS-‹Tool›-Setup.exe`. Note SmartScreen warning (unsigned exe) in the README.

## Output

→ [`../../software/pc/<tool>/`](../../software/pc) — folder template in [`../WORKFLOW.md`](../WORKFLOW.md).

## New tool checklist

- [ ] `src/` builds clean with `build_linux.sh`
- [ ] Branding: name, © AMS, AMS footer, tray "AMS on YouTube"
- [ ] Installer: per-user, AMS Start menu, YouTube opens once on install/uninstall
- [ ] `release/` committed, README written (install / use / uninstall / tunables)
- [ ] Added to the root `README.md` product table

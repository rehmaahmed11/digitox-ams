# Software — produced applications

Every AMS application lands here, split by platform:

| Folder | Platform | Produced so far |
|---|---|---|
| [`pc/`](pc) | Windows (10 & 11) | [`ams-capslock-osd`](pc/ams-capslock-osd) — AMS Caps Lock OSD |
| [`mobile/`](mobile) | Android / iOS | *(none yet)* |

Each product folder contains source, branding assets, installer, build scripts and the ready `release/` files.
The production rules live in the engine: [`engine/software/pc.md`](../engine/software/pc.md) · [`engine/software/mobile.md`](../engine/software/mobile.md).

## Rebuild a PC product
```bash
./engine/setup/setup_linux.sh          # once, on a fresh machine
./software/pc/<tool>/build_linux.sh    # -> software/pc/<tool>/release/
```

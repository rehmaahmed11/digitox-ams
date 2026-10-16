# Promotional videos — produced commercials

Every AMS product gets a **65s promo video** in the fixed AMS 7-scene style. Each video lives in its own folder with the full code pipeline that generates it:

| Folder | Product | Output |
|---|---|---|
| [`ams-capslock-osd/`](ams-capslock-osd) | AMS Caps Lock OSD | `output/AMS_CapsLockOSD_Promo.mp4` |

The production rules live in the engine: [`engine/video.md`](../engine/video.md).
Everything is code-generated (pycairo motion graphics + synthesized music + ffmpeg) — rebuildable, editable, no licensing issues.

## Rebuild a video
```bash
./engine/setup/setup_linux.sh                 # once, on a fresh machine
./promotional-video/<tool>/build_video.sh     # -> promotional-video/<tool>/output/*.mp4
```

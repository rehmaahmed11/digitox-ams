#!/usr/bin/env bash
# Builds the 65s AMS Caps Lock OSD promo: audio mix -> frames -> mp4.
# Requires: engine/setup/setup_linux.sh ; voice-over clips in vo/ ; images in img/
set -e
cd "$(dirname "$0")"
python3 audio.py                         # music + SFX + voice-over -> mix.wav
python3 render.py still 5.9 15.5 20.8 26.4 35.0 47.5 52.6 59.0   # preview frames -> stills/
rm -rf /tmp/chunks
python3 render.py video 2                # render frames with 2 workers -> /tmp/chunks
mkdir -p output
ffmpeg -v error -y -f concat -safe 0 -i /tmp/chunks/list.txt -i mix.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 256k -af "loudnorm=I=-14:TP=-1.0:LRA=11" -ar 48000 -t 65 \
  -movflags +faststart output/AMS_CapsLockOSD_Promo.mp4
echo "Done: output/AMS_CapsLockOSD_Promo.mp4"

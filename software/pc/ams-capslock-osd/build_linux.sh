#!/usr/bin/env bash
# Builds AMS Caps Lock OSD on Linux (cross-compiles a Windows exe + installer).
# Requires: engine/setup/setup_linux.sh
set -e
cd "$(dirname "$0")"
mkdir -p release

# 1) (optional) regenerate icon PNGs + app.ico from the same drawing code as the app
mcs -sdk:4.5 -main:CapsLockOSD.Gen -r:System.Drawing.dll -r:System.Windows.Forms.dll -out:/tmp/gen.exe src/Program.cs tools/Gen.cs
mono /tmp/gen.exe assets
convert assets/icon_16.png assets/icon_24.png assets/icon_32.png assets/icon_48.png assets/icon_64.png assets/icon_128.png assets/icon_256.png assets/app.ico
rm -f assets/preview_on.png assets/preview_off.png

# 2) installer banners (AMS branding)
convert -size 164x314 gradient:'#1e2a44'-'#0b0d14' \
 \( assets/icon_256.png -resize 92x92 \) -gravity north -geometry +0+46 -composite \
 -font DejaVu-Sans-Bold -fill white -pointsize 34 -gravity north -annotate +0+158 'AMS' \
 -fill '#78b9ff' -pointsize 11 -annotate +0+204 'C A P S   L O C K   O S D' \
 -fill '#2a3550' -draw 'rectangle 40,232 124,233' \
 -font DejaVu-Sans -fill '#8a93a8' -pointsize 10 -annotate +0+246 'by AMS' \
 -alpha off -type TrueColor BMP3:assets/wizard.bmp
convert -size 150x57 xc:white \( assets/icon_64.png -resize 40x40 \) -gravity east -geometry +8+0 -composite \
 -font DejaVu-Sans-Bold -fill '#0b5fd6' -pointsize 22 -gravity west -annotate +8-6 'AMS' \
 -font DejaVu-Sans -fill '#667' -pointsize 9 -annotate +9+14 'Caps Lock OSD' \
 -alpha off -type TrueColor BMP3:assets/header.bmp

# 3) the app (Windows GUI exe, .NET Framework 4.x - built into Windows 10/11)
mcs -sdk:4.5 -target:winexe -optimize+ -win32icon:assets/app.ico \
    -r:System.Drawing.dll -r:System.Windows.Forms.dll -out:release/CapsLockOSD.exe src/Program.cs

# 4) the installer
(cd installer && makensis -V2 installer.nsi)
ls -la release

#!/usr/bin/env bash
# One-time setup of the AMS build machine (Debian/Ubuntu Linux).
# Installs everything used to build AMS tools (C#/.NET exe + NSIS installer) and AMS promo videos.
set -e
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  mono-devel      `# C# compiler (mcs) -> builds Windows .NET Framework 4.x .exe files` \
  nsis            `# makensis -> builds the Windows Setup.exe installer` \
  imagemagick     `# icons (.ico), installer banners (.bmp), contact sheets` \
  ffmpeg          `# video encoding + audio mixing/loudness` \
  libcairo2-dev pkg-config `# vector graphics engine for the video renderer` \
  fonts-inter     `# Inter / Inter Display = AMS brand fonts`
pip install -r "$(dirname "$0")/requirements.txt"
echo "AMS build environment ready."

#!/usr/bin/env bash
# Download eBL's period-specific cuneiform fonts into tmp/periodfonts/ (git-ignored).
# The fonts are NOT committed; only the derived vector data (docs/js/signs-*.js) is.
# Fonts: Assurbanipal (S. Vanseveren, Neo-Assyrian), Esagil (C. Ziegeler, Neo-Babylonian),
# Santakku/SantakkuM (S. Vanseveren, Old/Middle Babylonian), UllikummiA (Hittite).
# Source: the public eBL frontend repository.
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/tmp/periodfonts"
mkdir -p "$OUT"
BASE="https://raw.githubusercontent.com/ElectronicBabylonianLiterature/ebl-frontend/master/src"
for f in \
  "Assurbanipal.ttf" \
  "signs/ui/display/fonts/Santakku.woff" \
  "signs/ui/display/fonts/SantakkuM.woff" \
  "signs/ui/display/fonts/OBFreie.woff" \
  "signs/ui/display/fonts/Esagil.woff" \
  "signs/ui/display/fonts/UllikummiA.woff" ; do
  curl -fsSL --max-time 60 -o "$OUT/$(basename "$f")" "$BASE/$f" && echo "got $(basename "$f")"
done

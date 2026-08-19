#!/bin/bash
# Pre-crop sources to the exact target aspect ratio BEFORE uploading to Higgsfield.
# Without this, image-to-image non-uniformly scales the source to fill the requested
# aspect_ratio, which squishes the geometry. Feeding a source already at the target
# ratio means the model has no reshaping to do.
#
# Mirrors the folder structure from Input_Images/ into Input_Prepared/.
#
# Usage: ./prepare_sources.sh <subpath> [target_w] [target_h] [anchor]
#   e.g. ./prepare_sources.sh Prod01_IMG/Sports 16 9 center
#   anchor: center (default) | left | right | top | bottom

set -euo pipefail

SUBPATH="${1:-}"
TW="${2:-16}"
TH="${3:-9}"
ANCHOR="${4:-center}"

SRC_DIR="Input_Images/$SUBPATH"
OUT_DIR="Input_Prepared/$SUBPATH"

[ -d "$SRC_DIR" ] || { echo "No such folder: $SRC_DIR"; exit 1; }
mkdir -p "$OUT_DIR"

shopt -s nullglob nocaseglob
for f in "$SRC_DIR"/*.{jpg,jpeg,png,heic}; do
  name=$(basename "$f")
  base="${name%.*}"

  W=$(sips -g pixelWidth  "$f" | awk '/pixelWidth/{print $2}')
  H=$(sips -g pixelHeight "$f" | awk '/pixelHeight/{print $2}')

  # Largest region of target ratio that fits inside the source
  CW=$(python3 -c "print(min($W, round($H*$TW/$TH)))")
  CH=$(python3 -c "print(min($H, round($W*$TH/$TW)))")

  if [ "$CW" -eq "$W" ] && [ "$CH" -eq "$H" ]; then
    echo "$name: already ${TW}:${TH} (${W}x${H}), copying"
    sips -s format png "$f" --out "$OUT_DIR/${base}.png" >/dev/null
    continue
  fi

  OFF_X=0; OFF_Y=0
  case "$ANCHOR" in
    left)   OFF_X=$(python3 -c "print(-($W-$CW)//2)") ;;
    right)  OFF_X=$(python3 -c "print(($W-$CW)//2)")  ;;
    top)    OFF_Y=$(python3 -c "print(-($H-$CH)//2)") ;;
    bottom) OFF_Y=$(python3 -c "print(($H-$CH)//2)")  ;;
  esac

  sips -c "$CH" "$CW" --cropOffset "$OFF_Y" "$OFF_X" "$f" \
       --setProperty format png --out "$OUT_DIR/${base}.png" >/dev/null

  LOSS=$(python3 -c "print(round((1-($CW*$CH)/($W*$H))*100))")
  echo "$name: ${W}x${H} -> ${CW}x${CH} (${ANCHOR}, ${LOSS}% dropped)"
done

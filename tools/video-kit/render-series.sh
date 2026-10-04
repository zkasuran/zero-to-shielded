#!/usr/bin/env bash
# Render Zero to Shielded episodes end to end: preflight (captures every stage frame), build
# (paint, encode, mix with the original music), upload package, then copy the master into the
# episode folder. Usage: ./render-series.sh e1 e2 ...   Logs: artifacts/render-<id>.log
set -uo pipefail
cd "$(dirname "$0")"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/opt/playwright}"
export STAGE_SCREENSHOT="${STAGE_SCREENSHOT:-fast}"
REPO="$(cd ../.. && pwd)"
declare -A DIR=([e0]=E0-trailer [e1]=E1-wallet-setup [e2]=E2-getting-zec [e3]=E3-shielding-unshielding [e4]=E4-sending-receiving [e5]=E5-stay-private)
mkdir -p artifacts
for ep in "$@"; do
  id="zts-$ep"; n="${ep#e}"; dir="$REPO/episodes/${DIR[$ep]}"
  log="artifacts/render-$id.log"
  music="$REPO/music/zts-bed.wav"; [ "$ep" = e0 ] && music="$REPO/music/zts-trailer.wav"
  {
    echo "== $id start $(date -u +%H:%M:%S)"
    python3 preflight.py "projects/$id.json" || { echo "PREFLIGHT FAILED $id"; continue; }
    echo "== $id preflight done $(date -u +%H:%M:%S)"
    MUSIC="$music" python3 build.py "projects/$id.json" || { echo "BUILD FAILED $id"; continue; }
    echo "== $id build done $(date -u +%H:%M:%S)"
    python3 upload.py "projects/$id.json"; echo "upload exit $?"
    cp "out/$id.mp4" "$dir/DEMO-E$n.mp4" && echo "copied $dir/DEMO-E$n.mp4"
    echo "== $id end $(date -u +%H:%M:%S)"
  } > "$log" 2>&1
  tail -3 "$log"
done

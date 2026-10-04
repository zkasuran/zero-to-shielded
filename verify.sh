#!/usr/bin/env bash
# One release gate. Prints ALL GREEN only when every check passes.
set -euo pipefail
cd "$(dirname "$0")"
step() { printf '\n== %s\n' "$1"; }

step "video kit tests"
( cd tools/video-kit && python3 -m pytest -q tests )

step "voice gate on outward words"
# Prunes are grouped: without the parentheses the name tests bind to the last -prune
# branch only and the gate silently matched nothing.
mapfile -t OUT < <(find . \( -path ./tools -o -path ./.git -o -path ./.kiro -o -path '*/node_modules' \) -prune -o \
  \( -name 'BRIEF.md' -o -name 'THREAD.md' -o -name 'README.md' -o -name '*.srt' -o -name '*.html' \) -type f -print || true)
if [ "${#OUT[@]}" -gt 0 ]; then node tools/voice-gate.mjs "${OUT[@]}"; else echo "no outward files yet"; fi

step "narration in project files"
for p in episodes/*/zts-*.json; do
  [ -e "$p" ] || continue
  python3 - "$p" <<'EOF' | node tools/voice-gate.mjs
import json,sys
d=json.load(open(sys.argv[1]))
for s in d.get("segments",[]):
    for n in s.get("narration",[]):
        print(n["text"] if isinstance(n,dict) else n)
EOF
done

step "episode files"
for mp4 in episodes/*/DEMO-*.mp4; do
  [ -e "$mp4" ] || continue
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$mp4")
  python3 -c "import sys; d=float('$d'); sys.exit(0 if d<=140 else f'$mp4 is {d:.1f}s > 140s')"
  ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$mp4" | grep -q audio || { echo "$mp4 has no audio"; exit 1; }
  echo "ok $mp4 ${d}s"
done

step "site tests"
if [ -d site/test ]; then node --test site/test/; else echo "no site tests yet"; fi

step "secrets and private data not tracked"
if git rev-parse --git-dir >/dev/null 2>&1; then
  git check-ignore -q submit/ || { echo "submit/ not ignored"; exit 1; }
  git check-ignore -q footage/raw/x.mp4 || { echo "footage/raw not ignored"; exit 1; }
  if git ls-files | grep -E '(^|/)\.env|\.mp4$|(^|/)submit/' ; then echo "tracked private file"; exit 1; fi
fi

printf '\nALL GREEN\n'

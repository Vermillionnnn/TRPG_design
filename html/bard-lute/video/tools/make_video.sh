#!/usr/bin/env bash
# Builds the promo video for the bard lute page end to end.
# usage: html/bard-lute/video/tools/make_video.sh [path/to/bard-lute.html]
#   default page: html/bard-lute/bard-lute.html next to this folder
#   WORK (default html/bard-lute/video/.work) holds every intermediate file; the result is $WORK/bard_ad_1080p.mp4
# needs: node + playwright (with Chromium), python3 + numpy + scipy, ffmpeg, curl
set -euo pipefail
TOOLS="$(cd "$(dirname "$0")" && pwd)"
export WORK="${WORK:-$TOOLS/../.work}"
mkdir -p "$WORK"
export WORK="$(cd "$WORK" && pwd)"
JOBS="${JOBS:-4}"

echo "== page"
if [ $# -ge 1 ]; then cp "$1" "$WORK/bard-lute.html"
else cp "$TOOLS/../../bard-lute.html" "$WORK/bard-lute.html"; fi
# expose the game state and the audio context so the bot can play and the clock can be read
sed 's/^\(  const G = {.*\)$/\1\n  window.__G = G; window.__ctx = () => ctx;/' "$WORK/bard-lute.html" > "$WORK/bard-cap.html"
grep -q '__G = G' "$WORK/bard-cap.html" || { echo "could not patch the page (game state not found)"; exit 1; }

echo "== fonts"
mkdir -p "$WORK/fonts"
if [ ! -s "$WORK/fonts/NotoSerifSC-900.ttf" ]; then
  # an old user agent makes Google Fonts serve plain TTFs; the URLs come back in request order
  curl -sS -A "Mozilla/4.0" "https://fonts.googleapis.com/css2?family=ZCOOL+XiaoWei&family=Noto+Serif+SC:wght@500;700;900&family=Uncial+Antiqua" > "$WORK/fonts/g.css"
  i=0
  for n in NotoSerifSC-500 NotoSerifSC-700 NotoSerifSC-900 UncialAntiqua ZCOOLXiaoWei; do
    i=$((i + 1))
    u=$(grep -o 'url([^)]*)' "$WORK/fonts/g.css" | sed -n "${i}p" | sed 's/^url(//;s/)$//')
    curl -sSf -o "$WORK/fonts/$n.ttf" "$u"
  done
fi

echo "== audio (real time)"
for r in song:greensleeves:green song:scarborough:scar song:tempus:tempus pad::pad game::game sting::sting; do
  IFS=: read -r kind arg name <<< "$r"
  node "$TOOLS/audio_capture.js" "$WORK/bard-cap.html" "$WORK/audio/$name" "$kind${arg:+:$arg}"
done
python3 "$TOOLS/mix.py"
I=$(ffmpeg -nostats -i "$WORK/mix_raw.wav" -af ebur128 -f null - 2>&1 | sed -n '/Summary/,$p' | awk '/ I:/{print $2; exit}')
ffmpeg -v error -y -i "$WORK/mix_raw.wav" -af "volume=$(python3 -c "print(-14 - ($I))")dB" -ar 48000 "$WORK/mix.wav"

echo "== footage (virtual time)"
python3 "$TOOLS/vplan.py"
rm -rf "$WORK/frames"
printf '%s\n' game green pad idle sting scar tempus | xargs -P "$JOBS" -I{} node "$TOOLS/vrun.js" {}
python3 "$TOOLS/build_manifest.py"

echo "== compose"
rm -rf "$WORK/video_frames"
N=1290; STEP=$(( (N + JOBS - 1) / JOBS ))
for ((a = 0; a < N; a += STEP)); do
  z=$(( a + STEP < N ? a + STEP : N ))
  node "$TOOLS/render.js" frames "$a" "$z" &
done
wait
ffmpeg -v error -y -framerate 30 -i "$WORK/video_frames/%05d.jpg" -i "$WORK/mix.wav" \
  -c:v libx264 -preset slow -crf 16 -tune animation -pix_fmt yuv420p -profile:v high -movflags +faststart \
  -c:a aac -b:a 192k -shortest "$WORK/bard_ad_1080p.mp4"
echo "done: $WORK/bard_ad_1080p.mp4"

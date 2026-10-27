#!/bin/sh
# Run a Blender script headless, keeping Blender's user files inside the repo
# (.blender/) so it also works in a sandbox that cannot read ~/Library.
#
#     scenes/blender.sh scenes/homebase/build_scene.py --render out.png --shot wide
#
# Blender is found via $BLENDER, then `blender` on PATH, then the default macOS
# install at /Applications/Blender.app.
set -e
if [ $# -lt 1 ]; then
  echo "usage: $0 script.py [script args...]" >&2
  exit 2
fi
ROOT=$(cd "$(dirname "$0")/.." && pwd)
if [ -z "$BLENDER" ]; then
  if command -v blender >/dev/null 2>&1; then
    BLENDER=blender
  else
    BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
  fi
fi
SCRIPT=$1
shift
mkdir -p "$ROOT/.blender/user"
BLENDER_USER_RESOURCES="$ROOT/.blender/user" \
  exec "$BLENDER" -b --factory-startup --disable-autoexec -P "$SCRIPT" -- "$@"

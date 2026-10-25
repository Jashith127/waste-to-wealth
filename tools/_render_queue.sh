#!/usr/bin/env bash
# Tonight's render queue (not shipped): one job at a time on the one GPU, half samples (--fast).
# Usage: bash tools/_render_queue.sh <job> [<job> ...]   jobs: s02 s04 roof s03 s05 s06 s07
cd "$(dirname "$0")/.."
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
R=art/scripts/render_station.py
run() { "$B" -b "$1" --python $R -- --fast "${@:2}" 2>&1 | grep -E "^\[render\]|Error|Traceback"; }
for job in "$@"; do
  echo "== $job start $(date +%H:%M)"
  case $job in
    s02) rm -rf art/build/renders/s02; run art/blender/s02_walk.blend ;;
    s04) rm -rf art/build/renders/s04; run art/blender/s04_cold.blend
         run art/blender/s04_cold.blend --preset night --power-cut --only bg_night,riyaz_idle_night,door_a_night,door_b_night,door_a_open_night,door_b_open_night ;;
    roof) rm -rf art/build/renders/s04roof; run art/blender/s04_roof.blend --only bg
          run art/blender/s04_roof.blend --preset dusk --only bg_dusk
          run art/blender/s04_roof.blend --preset night --power-cut --only bg_night ;;
    s03) run art/blender/s03_weighin.blend --only bg,riyaz_idle,attendant_idle,attendant_type ;;
    s05) rm -rf art/build/renders/s05; run art/blender/s05_pickup.blend ;;
    s06) rm -rf art/build/renders/s06; run art/blender/s06_renderer.blend ;;
    s07) rm -rf art/build/renders/s07; run art/blender/s07_loop.blend ;;
    s02fix) run art/blender/s02_walk.blend --only bg,litter,litter_shadow ;;
  esac
  echo "== $job done $(date +%H:%M)"
done

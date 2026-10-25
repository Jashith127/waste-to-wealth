#!/usr/bin/env bash
# Second render queue tonight (not shipped): the power-cut fix and the swapped models.
cd "$(dirname "$0")/.."
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
R=art/scripts/render_station.py
run() { "$B" -b "$1" --python $R -- --fast "${@:2}" 2>&1 | grep -E "^\[render\]|Error|Traceback"; }
echo "== q2 start $(date +%H:%M)"
run art/blender/s02_walk.blend --only bg,kilo,cart,cart_shadow,litter,litter_shadow; echo "== s02 done $(date +%H:%M)"
run art/blender/s04_roof.blend --preset night --power-cut --only bg_night; echo "== roof done $(date +%H:%M)"
run art/blender/s04_cold.blend --preset night --power-cut --only bg_night,riyaz_idle_night,door_a_night,door_b_night,door_a_open_night,door_b_open_night; echo "== s04 done $(date +%H:%M)"
run art/blender/s01_stall.blend --preset night --power-cut --only bg_night,bg_fx_fridge_glow_night,riyaz_idle_night,leftovers_night,leftovers_shadow_night; echo "== s01 done $(date +%H:%M)"
rm -rf art/build/renders/s06; run art/blender/s06_renderer.blend; echo "== s06 done $(date +%H:%M)"
run art/blender/s07_loop.blend --only bg; echo "== s07 done $(date +%H:%M)"

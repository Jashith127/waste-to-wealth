"""Builds art/blender/template.blend: the locked camera, light rig, every kit material and a
sample street slice at true scale, for people to open and look at.

Run:  blender -b --python art/scripts/make_template.py

Station sets are never edited by hand from this file: each station has its own build script
that calls the same lib functions (docs/patterns.md). The template is the visual reference.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import bpy  # noqa: E402

import geo  # noqa: E402
import kit  # noqa: E402
import people  # noqa: E402
import rig  # noqa: E402
import safety  # noqa: E402

README = """WASTE TO WEALTH: station template

Camera  : orthographic, rotation (60, 0, 45), ortho scale 11 m (rig.py). Never change it per station.
Lights  : rig.PRESETS morning / midday / night. Sun travels toward +Y so shopfronts (facing -Y) are lit.
Scale   : 1 unit = 1 m. People 1.6 m, 6 heads, hands 1.3x. Touched props 1.3x. Bevel every edge.
Street  : street slice, wall at y = 3, pavement y 0..3, frontage x -5..5 (kit.Street).
Overhang: an overhang at height H projecting p hides the wall below down to H - 0.82p.
Layers  : collections SET, PROPS, PROP_<name>, FX_<name>, CHAR_<name>_<pose> (station.py).
Palette : docs/art-bible.md section 3. Check renders with tools/check_palette.py.

Build stations with art/scripts/sNN_build.py, never by hand in this file.
"""


def build():
    safety.fresh_scene()
    scene = bpy.context.scene
    scene.name = "TEMPLATE"
    m = kit.materials()
    for mat in m.values():
        mat.use_fake_user = True            # keep the whole library in the file
    st = kit.Street()
    col = geo.collection("SET")
    kit.plinth(st, m, col)
    kit.pier(st, "FACADE_pier_L", st.x0, -3.0, m["cream"], col)
    kit.shutter_bay(st, "FACADE_bay", -3.0, -0.8, m, col, m["board_faded_a"])
    kit.pier(st, "FACADE_pillar", -0.8, -0.4, m["orange"], col, proud=0.05)
    kit.shop_opening(st, "FACADE_shop", -0.4, 1.9, m, col)
    kit.awning(st, "SHOP_awning", -0.95, 2.45, m, col)
    kit.pier(st, "FACADE_pier_R", 1.9, st.x1, m["cream"], col)
    kit.upper_storey(st, m, col)
    kit.building_mass(st, m, col, rooms=[(-0.65, 2.15, 5.7, 3.05)])
    kit.facade_wires(st, m, col)
    ref = geo.collection("SCALE_REFERENCE")
    geo.box("REF_1m_cube", (2.6, 1.0, 0), (3.6, 2.0, 1.0), m["grey"], ref, 0.01)
    mats = people.costume_materials("scale_person", shirt="#8F877C", cap=None)
    people.figure("REF_person_1m60", (1.6, 1.5, 0), 0, mats, (-0.3, -0.25, 1.0), (0.3, -0.25, 1.0), ref, moustache=False)
    geo.box("REF_kilo_1p3x", (0.5, 1.4, 0), (0.85, 1.7, 0.28), m["bag"], ref, 0.02)
    rig.camera((0.0, 3.0, 1.0))
    rig.lights("morning")
    rig.render_settings()
    text = bpy.data.texts.new("README")
    text.write(README)
    text.use_fake_user = True
    safety.save(safety.ART / "blender" / "template.blend")


if __name__ == "__main__":
    build()

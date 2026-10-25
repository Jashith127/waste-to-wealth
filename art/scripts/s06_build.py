"""Station 6 · Renderer (example), Run 2. Builds art/blender/s06_renderer.blend.

Run:  blender -b --python art/scripts/s06_build.py
Then: blender -b art/blender/s06_renderer.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s06

Re-runnable. Destructive only to art/blender/s06_renderer.blend (backed up by lib/safety).

A fictional plant, labelled "Renderer (example)" in the game; the steps are a typical process
(truth rules). No real company, logo or place (task 06). Five simplified machines left to right:
hopper and shredder (size reduction), a jacketed cooker drum (cooking), a screw press (pressing out
oil), a rotary dryer (drying), a hammer mill with its cyclone (milling); then meal in sacks and oil
in drums. PROP_material is the heap the game moves from step to step.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import people  # noqa: E402
import rig  # noqa: E402
import s03_art_build as s03  # noqa: E402

SET_DATA = {"id": "s06", "set": {"blend": "art/blender/s06_renderer.blend", "lighting": "midday", "street": {"x0": -4.5, "x1": 5.0}}, "signs": []}
TARGET = (0.4, 2.4, 1.2)
X = (-3.2, -1.6, -0.1, 1.5, 3.0)        # machine centres along the line
Y = 2.3


def materials(m):
    m.update(
        plant_floor=M.plaster("MAT_plant_floor", "#8E8A82", 0.25),
        machine=M.steel("MAT_machine", "#7E8A8E", 0.45),
        machine_dark=M.steel("MAT_machine_dark", "#4E5558", 0.5),
        machine_paint=M.plastic("MAT_machine_paint", "#6E7F86", 0.5),
        corrugated=M.shutter("MAT_corrugated", "#8C9296"),
        belt=M.matte("MAT_belt", "#2A2826", 0.7),
        heap=M.matte("MAT_heap", "#7A5A44", 0.85),
        meal=M.matte("MAT_meal", "#9C8160", 0.9),
        coverall=M.matte("MAT_coverall", "#4F5E6E", 0.8),
        stain=M.matte("MAT_stain", "#3E352F", 0.25),
        meal_sack=M.matte("MAT_meal_sack", "#CFC6B0", 0.9),
        oil_drum=M.steel("MAT_oil_drum", "#5E6670", 0.5),
    )


def plant(st):
    s, m, col = st.street, st.m, st.set
    geo.box("FLOOR", (s.x0, 0, -0.25), (s.x1, 6.0, 0), m["plant_floor"], col, geo.BEVEL_ARCH)
    geo.box("WALL_back", (s.x0, 3.6, 0), (s.x1, 3.8, 5.0), m["corrugated"], col, 0)
    geo.box("WALL_kick", (s.x0, 3.55, 0), (s.x1, 3.6, 0.6), m["concrete"], col, 0.01)
    for i, x in enumerate((-4.2, -1.0, 2.2, 4.7)):
        geo.box(f"COLUMN_{i}", (x - 0.12, 3.35, 0), (x + 0.12, 3.6, 5.0), m["steel_dark"], col, 0.01)
    geo.box("BEAM", (s.x0, 3.3, 4.6), (s.x1, 3.6, 4.9), m["steel_dark"], col, 0.01)
    for i, (x0, x1) in enumerate(((-3.9, -2.4), (2.6, 4.2))):
        geo.box(f"SKYLIGHT_{i}", (x0, 3.55, 3.4), (x1, 3.58, 4.4), m["window_glass"], col, 0)
    # pipe runs along the back wall
    for i, z in enumerate((3.0, 3.25)):
        geo.cylinder(f"PIPE_{i}", (s.x0, 3.45, z), 0.06, s.x1 - s.x0, m["machine_dark"], col, axis="X", bevel=0)
    for i, (x, y, r) in enumerate(((-2.2, 1.0, 0.7), (2.4, 1.3, 0.5), (0.4, 0.8, 0.4))):
        p = geo.cylinder(f"STAIN_{i}", (x, y, 0.0), r, 0.004, m["stain"], col, segments=24, bevel=0)
        p.scale = (1.6, 0.8, 1)


def machines(st):
    m, col = st.m, st.set
    tops = []
    # 1 size reduction: a hopper over a shredder box
    x = X[0]
    geo.box("SHRED_body", (x - 0.45, Y - 0.45, 0), (x + 0.45, Y + 0.45, 1.0), m["machine_paint"], col, 0.03)
    geo.cylinder("SHRED_hopper", (x, Y, 1.0), 0.32, 0.55, m["machine"], col, radius2=0.62, segments=4)
    geo.box("SHRED_motor", (x + 0.45, Y - 0.2, 0.2), (x + 0.75, Y + 0.2, 0.6), m["machine_dark"], col, 0.03)
    tops.append((x, Y, 1.6))
    # 2 cooking: a horizontal jacketed drum on legs, with gauges
    x = X[1]
    geo.cylinder("COOK_drum", (x - 0.65, Y, 1.0), 0.5, 1.3, m["machine"], col, axis="X", segments=32)
    for k in (-0.5, 0.5):
        geo.box(f"COOK_leg{k}", (x + k - 0.06, Y - 0.35, 0), (x + k + 0.06, Y + 0.35, 0.6), m["machine_dark"], col, 0.01)
    geo.cylinder("COOK_gauge", (x + 0.3, Y - 0.52, 1.25), 0.06, 0.03, m["window_glass"], col, axis="Y", bevel=0)
    tops.append((x, Y, 1.55))
    # 3 pressing out oil: a screw press, a long box with a feed screw housing and an oil trough
    x = X[2]
    geo.box("PRESS_base", (x - 0.55, Y - 0.35, 0), (x + 0.55, Y + 0.35, 0.7), m["machine_paint"], col, 0.03)
    geo.cylinder("PRESS_barrel", (x - 0.55, Y, 0.9), 0.18, 1.1, m["machine"], col, axis="X", segments=24)
    geo.box("PRESS_trough", (x - 0.4, Y - 0.45, 0.62), (x + 0.4, Y - 0.32, 0.72), m["machine_dark"], col, 0.01)
    tops.append((x, Y, 1.15))
    # 4 drying: a long rotary dryer on rollers
    x = X[3]
    geo.cylinder("DRY_drum", (x - 0.75, Y, 0.95), 0.55, 1.5, m["machine"], col, axis="X", segments=32)
    for k in (-0.55, 0.55):
        geo.cylinder(f"DRY_ring{k}", (x + k - 0.05, Y, 0.95), 0.6, 0.1, m["machine_dark"], col, axis="X", segments=32)
        geo.box(f"DRY_roller{k}", (x + k - 0.12, Y - 0.4, 0), (x + k + 0.12, Y + 0.4, 0.45), m["machine_dark"], col, 0.01)
    tops.append((x, Y, 1.55))
    # 5 milling: a hammer mill and a cyclone on a frame
    x = X[4]
    geo.box("MILL_body", (x - 0.35, Y - 0.35, 0), (x + 0.35, Y + 0.35, 0.9), m["machine_paint"], col, 0.03)
    geo.cylinder("MILL_cyclone", (x + 0.1, Y + 0.3, 1.6), 0.3, 0.7, m["machine"], col, segments=24)
    geo.cylinder("MILL_cone", (x + 0.1, Y + 0.3, 0.95), 0.06, 0.65, m["machine"], col, segments=24, radius2=0.3)
    geo.limb("MILL_duct", (x, Y, 0.9), (x + 0.1, Y + 0.3, 2.2), 0.08, 0.08, m["machine_dark"], col)
    tops.append((x, Y - 0.1, 1.0))
    # conveyors between the machines
    for i in range(4):
        a, b = X[i] + 0.5, X[i + 1] - 0.5
        geo.box(f"BELT_{i}", (a, Y - 0.15, 0.55), (b, Y + 0.15, 0.6), m["belt"], col, 0.01)
        for k in (a + 0.1, b - 0.1):
            geo.box(f"BELT_{i}_leg{k:.1f}", (k - 0.03, Y - 0.12, 0), (k + 0.03, Y + 0.12, 0.55), m["steel_dark"], col, 0)
    for i, t in enumerate(tops):
        st.anchor(f"step_{i}", t)


def outputs(st):
    """Meal in sacks and oil in drums, at the end of the line (CC0 sacks and barrels)."""
    m, col = st.m, st.set
    for i, (dx, dy, z) in enumerate(((0, 0, 0), (0.5, 0.1, 0), (0.25, 0.05, 0.3))):      # plain woven sacks of meal
        geo.box(f"MEAL_sack{i}", (4.0 + dx - 0.22, 1.1 + dy - 0.32, z), (4.0 + dx + 0.22, 1.1 + dy + 0.32, z + 0.3), m["meal_sack"], col, 0.04, subsurf=2)
    for i, dx in enumerate((0, 0.65)):                                                  # plain steel drums of oil
        geo.cylinder(f"OIL_drum{i}", (4.2 + dx, 2.95, 0), 0.29, 0.88, m["oil_drum"], col, segments=28)
        for z in (0.3, 0.6):
            geo.cylinder(f"OIL_drum{i}_rib{z}", (4.2 + dx, 2.95, z), 0.295, 0.03, m["oil_drum"], col, segments=28, bevel=0)
    st.anchor("out_meal", (4.2, 1.3, 0.6))
    st.anchor("out_oil", (4.3, 2.95, 1.0))


def material(st):
    """The heap the game moves through the steps."""
    col = st.prop("material")
    geo.sphere("MATERIAL_heap", (0, 0, 0.06), 0.16, (1.3, 1.0, 0.55), st.m["heap"], col)
    for i in range(4):
        a = i * 1.6
        geo.sphere(f"MATERIAL_lump{i}", (math.cos(a) * 0.1, math.sin(a) * 0.08, 0.1), 0.06, (1.2, 1, 0.8), st.m["heap"], col)
    st.anchor("material_centre", (0, 0, 0.1))


def people_and_kit(st):
    m, col = st.m, st.props
    mats = people.costume_materials("worker", shirt="#4F5E6E", trousers="#4F5E6E", cap="#C9C6BC")
    people.figure("WORKER", (0.8, 1.2, 0), 60, mats, (-0.3, -0.18, 0.95), (0.32, -0.1, 0.85), col, moustache=False)
    kit.ph("HAND_truck", "hand_truck", (-4.0, 1.2, 0), 30, 1.0, col)
    kit.ph("JERRYCAN", "plastic_jerrycan", (4.6, 3.3, 0), -20, 1.0, col)
    light = rig.point_light("LIGHT_plant", (0.0, 2.0, 4.2), (0.96, 0.97, 0.93), 300, 1.0, col)
    light["practical"] = True


def build():
    st = s03.ArtStation(SET_DATA)
    s03.set_materials(st.m)
    kit.kit_materials(st.m)
    materials(st.m)
    plant(st)
    machines(st)
    outputs(st)
    material(st)
    people_and_kit(st)
    st.anchor("exit", (4.8, 1.0, 0.0))
    st.finish(TARGET)


if __name__ == "__main__":
    build()

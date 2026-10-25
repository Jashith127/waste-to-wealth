"""Station 7 · Farm → back to the stall, "How it could close" (Run 2). Builds art/blender/s07_loop.blend.

Run:  blender -b --python art/scripts/s07_build.py
Then: blender -b art/blender/s07_loop.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s07

Re-runnable. Destructive only to art/blender/s07_loop.blend (backed up by lib/safety).

Two halves on one plinth, rendered as a 3200x1920 plate (as s02) that Station07 pans across: a
poultry farm (open-sided shed, feeders with meal, a flock, a farmer scattering feed, meal sacks)
and a chicken-and-mutton stall like Riyaz's (awning, chicken hung at the door, tiled counter, the
vendor behind it). No farm name, place or numbers (task 07); the station is labelled "How it could
close" in the game and its only precedent is Kannur.
"""
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import bpy  # noqa: E402

import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import people  # noqa: E402
import rig  # noqa: E402
import s03_art_build as s03  # noqa: E402
import safety  # noqa: E402
from mathutils import Vector  # noqa: E402

SET_DATA = {"id": "s07", "set": {"blend": "art/blender/s07_loop.blend", "lighting": "midday", "street": {"x0": -7.0, "x1": 8.5}}, "signs": []}
PLATE_W, PLATE_H = 3200, 1920
TARGET = (-2.4, 2.4, 0.5)                  # the start frame: the farm
PLATE_TARGET = (3.6, 1.59, 0.5)            # 640 px right and 420 px down of TARGET (as s02)
PPM = 1920 / 11.0


def plate_to_screen(point, _target=None):
    r = rig._rot().to_matrix()
    right, up = r @ Vector((1, 0, 0)), r @ Vector((0, 1, 0))
    d = Vector(point) - Vector(PLATE_TARGET)
    return PLATE_W / 2 + d.dot(right) * PPM, PLATE_H / 2 - d.dot(up) * PPM


def materials(m):
    m.update(
        ground=M.plaster("MAT_farm_ground", "#9C8C72", 0.3),
        mesh=M.matte("MAT_wire_mesh", "#6E6A65", 0.6),
        hen_white=M.matte("MAT_hen_white", "#E2DCCF", 0.8),
        hen_brown=M.matte("MAT_hen_brown", "#9A6A48", 0.8),
        comb=M.matte("MAT_comb", "#A04A40", 0.6),
        beak=M.matte("MAT_beak_hen", "#C9A25A", 0.6),
        meal=M.matte("MAT_meal", "#9C8160", 0.9),
        dressed=M.meat("MAT_dressed_chicken"),
    )


def farm(st):
    m, col = st.m, st.set
    geo.box("FARM_ground", (-7.0, 0.0, -0.25), (0.5, 6.0, 0.0), m["ground"], col, geo.BEVEL_ARCH)
    # the open-sided shed: posts, a corrugated roof, a low mesh wall at the back
    for i, x in enumerate((-6.5, -4.5, -2.5, -0.5)):
        for j, y in enumerate((1.4, 4.4)):
            geo.box(f"SHED_post{i}{j}", (x - 0.07, y - 0.07, 0), (x + 0.07, y + 0.07, 2.6 if j == 0 else 3.1), m["steel_dark"], col, 0.01)
    roof = geo.box("SHED_roof", (-6.8, 1.2, 2.6), (-0.2, 4.6, 2.66), m["shutter"], col, 0.01)
    roof.rotation_euler = (math.radians(-8), 0, 0)
    geo.box("SHED_mesh_back", (-6.5, 4.38, 0), (-0.5, 4.42, 1.1), m["mesh"], col, 0)
    geo.box("SHED_kerb_back", (-6.5, 4.3, 0), (-0.5, 4.5, 0.25), m["concrete"], col, 0.01)
    # feeders full of meal
    for i, x in enumerate((-5.4, -3.4)):
        geo.box(f"FEEDER{i}", (x - 0.7, 1.85, 0), (x + 0.7, 2.15, 0.25), m["steel"], col, 0.01)
        geo.box(f"FEEDER{i}_meal", (x - 0.66, 1.88, 0.2), (x + 0.66, 2.12, 0.23), m["meal"], col, 0)
    geo.cylinder("WATER_drum", (-1.2, 3.8, 0), 0.3, 0.85, m["drum"], col)
    for i in range(3):
        geo.box(f"MEAL_sack{i}", (-6.5 + i * 0.5, 3.35, 0), (-6.1 + i * 0.5, 3.85, 0.3), m["meal"], col, 0.04, subsurf=2)
    # the flock
    rnd = random.Random(7)
    for i in range(16):
        x, y = rnd.uniform(-6.2, -0.8), rnd.uniform(1.6, 4.0)
        hen(f"HEN_{i}", Vector((x, y, 0)), rnd.uniform(0, 360), m["hen_white"] if i % 4 else m["hen_brown"], m, col)
    farmer = people.costume_materials("farmer", shirt="#8C7E68", trousers="#3A3633", cap=None)
    people.figure("FARMER", (-2.3, 2.9, 0), -50, farmer, (-0.4, -0.3, 1.05), (0.3, -0.1, 0.8), col, grip=("flat", "loose"))   # behind the feeder, throwing
    st.anchor("feed", (-3.4, 2.0, 0.4))
    st.anchor("flock", (-1.6, 2.8, 0.4))


def hen(name, at, rot, body, m, col):
    r = math.radians(rot)
    fwd = Vector((math.cos(r), math.sin(r), 0))
    geo.sphere(f"{name}_body", at + Vector((0, 0, 0.16)), 0.12, (1.35, 0.95, 0.95), body, col, rot=(0, 0, r))
    geo.sphere(f"{name}_head", at + fwd * 0.15 + Vector((0, 0, 0.28)), 0.06, (1, 1, 1), body, col)
    geo.sphere(f"{name}_comb", at + fwd * 0.15 + Vector((0, 0, 0.34)), 0.025, (1.4, 0.5, 1), m["comb"], col, rot=(0, 0, r))
    geo.limb(f"{name}_beak", at + fwd * 0.2 + Vector((0, 0, 0.28)), at + fwd * 0.25 + Vector((0, 0, 0.27)), 0.015, 0.003, m["beak"], col, segments=6)
    geo.limb(f"{name}_tail", at - fwd * 0.12 + Vector((0, 0, 0.18)), at - fwd * 0.2 + Vector((0, 0, 0.32)), 0.05, 0.02, body, col, segments=8)
    for i, s_ in enumerate((-1, 1)):
        side = Vector((-fwd.y, fwd.x, 0)) * 0.04 * s_
        geo.limb(f"{name}_leg{i}", at + side + Vector((0, 0, 0.08)), at + side, 0.008, 0.008, m["beak"], col, segments=5)


def stall(st):
    """Back on the counter at a stall like Riyaz's, on a Cockburn Road frontage (F04, V04)."""
    s, m, col = st.street, st.m, st.set
    geo.box("STREET_paving", (0.5, 0.0, -0.06), (8.5, 6.0, 0.0), m["paving"], col, geo.BEVEL_ARCH)
    geo.box("STREET_bed", (0.5, 0.0, -0.25), (8.5, 6.0, -0.06), m["soil"], col, 0)
    kit.pier(s, "STALL_pier_L", 1.5, 4.2, m["cream"], col)
    kit.pier(s, "STALL_pillar", 4.2, 4.6, m["orange"], col, proud=0.05)
    kit.shop_opening(s, "STALL_shop", 4.6, 6.8, m, col)
    kit.pier(s, "STALL_pier_R", 6.8, 8.5, m["cream_yellow"], col, proud=0.03)
    kit.upper_storey(s, m, col, windows=((2.0, 3.6), (5.0, 6.6)), ac_at=7.2)
    kit.building_mass(s, m, col, rooms=[(4.6, 6.8, s.wall_y + 2.4, 3.0)])
    geo.box("STALL_floor", (4.6, s.wall_y, 0), (6.8, s.wall_y + 2.4, 0.15), m["floor"], col, 0.01)
    geo.box("STALL_back", (4.6, s.wall_y + 2.4, 0), (6.8, s.wall_y + 2.6, 3.0), m["tiles_in"], col, 0)
    kit.awning(s, "STALL_awning", 4.3, 7.0, m, col)
    geo.box("STALL_counter", (4.8, 2.25, 0.06), (6.6, 2.85, 0.96), m["tiles_checker"], col)
    geo.box("STALL_top", (4.78, 2.23, 0.96), (6.62, 2.87, 1.0), m["steel"], col, 0.008)
    for i, x in enumerate((5.2, 5.55, 5.9)):
        geo.limb(f"STALL_hook{i}", (x, 2.7, 2.35), (x, 2.7, 2.15), 0.006, 0.006, m["steel"], col)
        geo.sphere(f"STALL_chicken{i}", (x, 2.7, 1.95), 0.11, (0.85, 0.75, 1.4), m["dressed"], col)
    geo.limb("STALL_rail", (4.95, 2.7, 2.35), (6.2, 2.7, 2.35), 0.015, 0.015, m["steel"], col)
    mats = people.costume_materials("vendor", apron="#D6CFC0", cap="#E6E2D8")
    people.figure("VENDOR", (6.1, 3.1, 0.15), 0, mats, (-0.3, -0.45, 1.0), (0.3, -0.45, 1.0), col)
    kit.kit_materials(m)
    kit.road(s, m, col, x0=0.5, x1=8.5)
    kit.two_wheeler_row("BIKE", 2.0, 2.8, 2.2, m, col, step=0.8, heading=180)
    kit.two_wheeler_row("BIKE_kerb", 3.8, 7.0, -0.6, m, col, step=2.1, heading=90, z=kit.ROAD_Z)
    kit.flex_board("FLEX_0", 4.4, 3.4, 1.0, s, m, m["flex_red"], col)
    kit.ph("CHAIR", "plastic_monobloc_chair_01", (7.4, 1.9, 0), 160, 1.0, col)
    kit.autorickshaw("AUTO_0", (2.0, -1.3, kit.ROAD_Z), 0, m, col)
    st.anchor("stall", (5.7, 2.6, 1.2))


def build():
    st = s03.ArtStation(SET_DATA)
    s03.set_materials(st.m)
    materials(st.m)
    farm(st)
    stall(st)
    st.anchor("exit", (8.0, 1.0, 0.0))
    rig.ORTHO_SCALE = 11.0 * PLATE_W / 1920
    rig.to_screen = plate_to_screen
    st.finish(PLATE_TARGET)
    bpy.context.scene.render.resolution_x = PLATE_W
    bpy.context.scene.render.resolution_y = PLATE_H
    safety.save(st.blend)


if __name__ == "__main__":
    build()

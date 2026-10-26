"""Station 7 · The meal in use, "How it could close" (Run 2). Builds art/blender/s07_loop.blend.

Run:  blender -b --python art/scripts/s07_build.py
Then: blender -b art/blender/s07_loop.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s07

Re-runnable. Destructive only to art/blender/s07_loop.blend (backed up by lib/safety).

One small farm in one frame, so the product's use is the whole picture: on the left a poultry run in
front of a low shed, with an empty feeder; on the right two vegetable beds; between them the sacks
from the renderer (the same green-banded sacks as s06) and the farmer. The game plays two uses as
before/after layer pairs, all in place (nothing moves, so the set's holdouts stay right):
  hens_a -> hens_b       the flock scattered -> crowded at the feeder, pecking   (+ feed: meal in it)
  plants_a -> plants_b   thin, pale seedlings -> full plants, meal worked in round their bases
No farm name, place or numbers; the station is labelled "How it could close" in the game, and its
only precedent is Kannur.
"""
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import human  # noqa: E402  (low-poly rigged people, s02 on; s01 keeps lib/people)
import people  # noqa: E402
import s03_art_build as s03  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

SET_DATA = {"id": "s07", "set": {"blend": "art/blender/s07_loop.blend", "lighting": "morning", "street": {"x0": -5.0, "x1": 5.0}}, "signs": []}
TARGET = (-0.4, 2.3, 0.7)
RUN = (-4.7, -0.7, 1.0, 3.7)                 # the poultry run: x0, x1, y0 (front fence), y1 (shed front)
TROUGH = Vector((-2.7, 2.35, 0.0))          # the feeder, in the middle of the run
BEDS = ((1.0, 4.4, 1.15, 1.95), (1.0, 4.4, 2.55, 3.35))
SACKS = Vector((0.0, 3.6, 0.0))


def materials(m):
    m.update(
        ground=M.plaster("MAT_farm_ground", "#9C8C72", 0.3),
        soil_bed=M.matte("MAT_bed_soil", "#5A4334", 0.95),
        plank=M.matte("MAT_plank", "#8A6A48", 0.8),
        fence=M.matte("MAT_fence", "#6E6A65", 0.6),
        roof=M.shutter("MAT_shed_roof", "#8C9296"),
        hen_white=M.matte("MAT_hen_white", "#E2DCCF", 0.8),
        hen_brown=M.matte("MAT_hen_brown", "#9A6A48", 0.8),
        comb=M.matte("MAT_comb", "#A04A40", 0.6),
        beak=M.matte("MAT_beak_hen", "#C9A25A", 0.6),
        meal=M.matte("MAT_meal", "#B89A6E", 0.95),
        sack=M.matte("MAT_meal_sack", "#D8CFB6", 0.9),
        sack_band=M.matte("MAT_sack_band", "#2E6B34", 0.8),
        pallet=M.matte("MAT_pallet", "#9C7A52", 0.8),
        leaf_pale=M.matte("MAT_leaf_pale", "#A6A05A", 0.7),
        leaf=M.matte("MAT_leaf", "#3F6B34", 0.6),
        leaf_dark=M.matte("MAT_leaf_dark", "#2F5229", 0.6),
        stem=M.matte("MAT_stem", "#5E6E3A", 0.7),
        fruit=M.plastic("MAT_tomato", "#B8402E", 0.3),
        canopy=M.matte("MAT_canopy", "#5C7046", 0.8),
        bark=M.matte("MAT_bark", "#5C4A3C", 0.9),
        brick=M.plaster("MAT_brick_wall", "#B07A5E", 0.3),
    )


def yard(st):
    """The ground, a low shed along the back of the run, a boundary wall and a tree behind the beds."""
    m, col = st.m, st.set
    geo.box("GROUND", (-5.0, -0.4, -0.25), (5.0, 5.6, 0.0), m["ground"], col, geo.BEVEL_ARCH)
    x0, x1, y0, y1 = RUN
    # the shed: a back wall, posts and a flat roof, open to the run
    geo.box("SHED_back", (x0, y1 + 1.3, 0), (x1, y1 + 1.45, 2.3), m["concrete"], col, 0.02)
    for i, x in enumerate((x0, (x0 + x1) / 2, x1)):
        geo.box(f"SHED_post{i}", (x - 0.07, y1 - 0.07, 0), (x + 0.07, y1 + 0.07, 2.2), m["steel_dark"], col, 0.01)
    geo.box("SHED_roof", (x0 - 0.15, y1 - 0.25, 2.2), (x1 + 0.15, y1 + 1.5, 2.28), m["roof"], col, 0.01)
    geo.box("SHED_floor", (x0, y1, 0), (x1, y1 + 1.3, 0.06), m["concrete"], col, 0.01)
    for i in range(3):
        geo.box(f"SHED_nest{i}", (x0 + 0.4 + i * 0.9, y1 + 0.9, 0.06), (x0 + 1.1 + i * 0.9, y1 + 1.3, 0.55), m["plank"], col, 0.01)
    # the boundary wall behind the beds, and a shade tree
    geo.box("WALL", (0.3, 4.8, 0), (5.0, 5.0, 1.4), m["brick"], col, 0.02)
    kit.rain_tree("TREE", 3.6, 4.4, m, col, height=5.2)


def fence(st):
    """A low wire fence round the run: posts and two rails, open enough to see the hens through."""
    m, col = st.m, st.set
    x0, x1, y0, y1 = RUN
    runs = (((x0, y0), (x1, y0)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1 - 1.0)))
    for i, ((ax, ay), (bx, by)) in enumerate(runs):
        n = max(1, int(math.hypot(bx - ax, by - ay) / 0.8))
        for k in range(n + 1):
            t = k / n
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            geo.box(f"FENCE{i}_post{k}", (x - 0.03, y - 0.03, 0), (x + 0.03, y + 0.03, 0.72), m["plank"], col, 0.005)
        for z in (0.3, 0.66):
            geo.limb(f"FENCE{i}_rail{z}", (ax, ay, z), (bx, by, z), 0.01, 0.01, m["fence"], col, segments=6)


def feeder(st):
    """The empty feeder, and its fill (a PROP the game shows once the meal is poured in)."""
    m, col = st.m, st.set
    t = TROUGH
    geo.box("TROUGH", (t.x - 0.9, t.y - 0.16, 0), (t.x + 0.9, t.y + 0.16, 0.2), m["steel"], col, 0.01)
    geo.box("TROUGH_rail", (t.x - 0.9, t.y - 0.01, 0.2), (t.x + 0.9, t.y + 0.01, 0.34), m["steel_dark"], col, 0)
    geo.box("FEED_meal", (t.x - 0.86, t.y - 0.13, 0.19), (t.x + 0.86, t.y + 0.13, 0.25), m["meal"], st.prop("feed"), 0)
    st.anchor("feeder", (t.x, t.y, 0.3))


def hen(name, at, rot, body, m, col, peck=False):
    """A hen; `peck` puts her head down in the feeder."""
    r = math.radians(rot)
    fwd = Vector((math.cos(r), math.sin(r), 0))
    up = Vector((0, 0, 1))
    head = at + fwd * (0.2 if peck else 0.15) + up * (0.14 if peck else 0.28)
    geo.sphere(f"{name}_body", at + up * 0.16, 0.12, (1.35, 0.95, 0.95), body, col, rot=(0, math.radians(18) if peck else 0, r))
    geo.sphere(f"{name}_head", head, 0.06, (1, 1, 1), body, col)
    geo.sphere(f"{name}_comb", head + up * 0.06, 0.025, (1.4, 0.5, 1), m["comb"], col, rot=(0, 0, r))
    geo.limb(f"{name}_beak", head + fwd * 0.05, head + fwd * 0.1 - up * (0.03 if peck else 0.01), 0.015, 0.003, m["beak"], col, segments=6)
    geo.limb(f"{name}_tail", at - fwd * 0.12 + up * 0.18, at - fwd * 0.2 + up * (0.36 if peck else 0.32), 0.05, 0.02, body, col, segments=8)
    for i, s_ in enumerate((-1, 1)):
        side = Vector((-fwd.y, fwd.x, 0)) * 0.04 * s_
        geo.limb(f"{name}_leg{i}", at + side + up * 0.08, at + side, 0.008, 0.008, m["beak"], col, segments=5)


def flock(st):
    """Two layers of the same nine hens: scattered round the run, then crowded at the feeder."""
    m = st.m
    rnd = random.Random(7)
    x0, x1, y0, y1 = RUN
    a, b = st.prop("hens_a"), st.prop("hens_b")
    for i in range(9):
        body = m["hen_white"] if i % 3 else m["hen_brown"]
        hen(f"HEN_A{i}", Vector((rnd.uniform(x0 + 0.4, x1 - 0.4), rnd.uniform(y0 + 0.4, y1 - 0.3), 0)), rnd.uniform(0, 360), body, m, a)
        side = 1 if i % 2 else -1                               # alternate sides of the trough, facing it
        x = TROUGH.x - 0.75 + (i // 2) * 0.38 + rnd.uniform(-0.05, 0.05)
        y = TROUGH.y + side * (0.36 + rnd.uniform(0, 0.08))
        hen(f"HEN_B{i}", Vector((x, y, 0)), -90 * side + rnd.uniform(-15, 15), body, m, b, peck=True)
    st.anchor("flock", (TROUGH.x, TROUGH.y, 0.6))


def beds(st):
    """Two raised beds; the same plants twice: thin and pale, then full and fruiting with the meal
    worked into the soil round each one."""
    m, col = st.m, st.set
    a, b = st.prop("plants_a"), st.prop("plants_b")
    for j, (x0, x1, y0, y1) in enumerate(BEDS):
        geo.box(f"BED{j}_frame", (x0, y0, 0), (x1, y1, 0.28), m["plank"], col, 0.01)
        geo.box(f"BED{j}_soil", (x0 + 0.06, y0 + 0.06, 0.2), (x1 - 0.06, y1 - 0.06, 0.27), m["soil_bed"], col, 0)
        yc, z = (y0 + y1) / 2, 0.27
        for k in range(6):
            x = x0 + 0.35 + k * 0.6
            plant(f"PA{j}_{k}", Vector((x, yc, z)), 0.45, m["leaf_pale"], m, a, fruit=False)
            geo.cylinder(f"PB{j}_{k}_meal", (x, yc, z), 0.17, 0.008, m["meal"], b, segments=24, bevel=0)
            plant(f"PB{j}_{k}", Vector((x, yc, z)), 1.0, m["leaf"] if k % 2 else m["leaf_dark"], m, b, fruit=True)
    st.anchor("beds", ((BEDS[0][0] + BEDS[0][1]) / 2, (BEDS[0][2] + BEDS[1][3]) / 2, 0.9))


def plant(name, base, k, leaf, m, col, fruit):
    """A vegetable plant, `k` its size: a stem and lumps of leaves; tomatoes when grown."""
    rnd = random.Random(name)
    h = 0.55 * k
    geo.limb(f"{name}_stem", base, base + Vector((0, 0, h)), 0.02 * k + 0.008, 0.012, m["stem"], col, segments=8)
    for i in range(5 if k > 0.6 else 3):
        a = i * 2.3
        r = 0.12 * k
        c = base + Vector((math.cos(a) * r, math.sin(a) * r * 0.8, h * (0.45 + 0.13 * i)))
        geo.sphere(f"{name}_leaf{i}", c, 0.11 * k + 0.02, (1.3, 1.1, 0.7), leaf, col, segments=12, rings=8)
    if fruit:
        for i in range(3):
            a = rnd.uniform(0, 6.28)
            geo.sphere(f"{name}_fruit{i}", base + Vector((math.cos(a) * 0.14, math.sin(a) * 0.1, h * rnd.uniform(0.35, 0.6))), 0.045, (1, 1, 0.9), m["fruit"], col)


def sacks(st):
    """The renderer's sacks on a pallet by the gate; one open, a scoop of meal in it."""
    m, col = st.m, st.set
    s = SACKS
    geo.box("SACKS_pallet", (s.x - 0.55, s.y - 0.45, 0), (s.x + 0.55, s.y + 0.45, 0.13), m["pallet"], col, 0.01)
    for i, (dx, dy, z) in enumerate(((-0.25, 0.18, 0.13), (0.25, 0.18, 0.13), (0.0, 0.2, 0.43))):
        geo.box(f"SACK{i}", (s.x + dx - 0.24, s.y + dy - 0.17, z), (s.x + dx + 0.24, s.y + dy + 0.17, z + 0.3), m["sack"], col, 0.05, subsurf=2)
        geo.box(f"SACK{i}_band", (s.x + dx - 0.22, s.y + dy - 0.185, z + 0.12), (s.x + dx + 0.22, s.y + dy - 0.16, z + 0.19), m["sack_band"], col, 0)
    # the open sack, standing at the front of the pallet
    geo.cylinder("SACK_open", (s.x, s.y - 0.22, 0.13), 0.2, 0.42, m["sack"], col, segments=20, bevel=0.02)
    geo.cylinder("SACK_open_band", (s.x, s.y - 0.22, 0.3), 0.203, 0.07, m["sack_band"], col, segments=20, bevel=0)
    geo.cylinder("SACK_open_meal", (s.x, s.y - 0.22, 0.5), 0.17, 0.08, m["meal"], col, segments=20, radius2=0.05, bevel=0.01)
    st.anchor("sacks", (s.x, s.y - 0.22, 0.6))


def farmer(st):
    """The farmer between the run and the beds, a scoop of meal in hand."""
    m, col = st.m, st.props
    mats = people.costume_materials("farmer", shirt="#8C7E68", trousers="#3A3633", cap=None)
    origin = (-0.1, 2.2, 0)
    human.figure("FARMER", origin, 20, mats, (-0.32, -0.32, 0.95), (0.28, -0.12, 0.82), col, grip=("fist", "loose"))
    hand = Vector(origin) + Matrix.Rotation(math.radians(20), 3, "Z") @ Vector((-0.32, -0.32, 0.95))
    geo.cylinder("SCOOP", hand + Vector((0, -0.06, -0.05)), 0.07, 0.1, m["steel"], col, segments=16, bevel=0.005)
    geo.cylinder("SCOOP_meal", hand + Vector((0, -0.06, 0.04)), 0.065, 0.03, m["meal"], col, segments=16, radius2=0.03, bevel=0)
    st.anchor("farmer_hand", hand)


def build():
    st = s03.ArtStation(SET_DATA)
    s03.set_materials(st.m)
    kit.kit_materials(st.m)
    materials(st.m)
    yard(st)
    fence(st)
    feeder(st)
    flock(st)
    beds(st)
    sacks(st)
    farmer(st)
    st.finish(TARGET)


if __name__ == "__main__":
    build()

"""Station 2 · The walk, Market street to Russell Market. 20 m of frontage, final art pass.

Run:  blender -b --python art/scripts/s02_build.py
Then: blender -b art/blender/s02_walk.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s02

Re-runnable. Destructive only to art/blender/s02_walk.blend, which lib/safety backs up
before every save. Content: src/data/stations/s02.json.

Street slice: pavement y 0..3, wall at y 3.0, frontage x -5..15. The walk needs more street than
one 1920 frame holds, so this station renders a 3200x1920 plate at the same 174.5 px/m as every
other station, with the same camera (only the canvas is wider). The plate's top-left is the
normal start frame; Station02 shows a 1920x1080 window and slides it across the plate. Anchors
are in plate pixels.

Layering: Riyaz walks the footpath freely; a clear lane down its middle (LANE_Y) keeps the way
open. Riyaz, the bag and the handcart are ["free"] layers: rendered with no set in front of them,
because they move. Every set piece standing on or by the footpath is also rendered alone as
occ_<name> (occluders()), and Station02 draws it over Riyaz when he is behind it, sorting by the
ground footprints this script stores in scene["world"].

Sources: shopfronts, shutters, awnings, signboards, scooter, chairs after F04 and F02 (Tier A);
the steel pushcart and tarp after F01; red crates and the blue drum after F03; overhead wires and
the leaning pole after F02/R19; Russell Market's white masonry with the pink ghost, pointed arches
and cornice after X04/R24 and X03/R23; the back-lane pile after the concept note (waste dumped
behind Russell Market, SPEC-journey) and the deck's Five senses: Smell (p. 34), drawn as sacks,
bone, cardboard and stains with no gore (art bible §4). Signboards are the s01 composite trades
(no real shop names, §7).
"""
import json
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
import s03_art_build as s03  # noqa: E402  (Russell Market masonry, arches, posters, as at the hub)
import safety  # noqa: E402
import station  # noqa: E402
import street_life  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

TARGET = (0.0, 3.0, 1.0)                 # camera focal point: the start of the walk
PLATE_W, PLATE_H = 3200, 1920             # the street plate: 1920x1080 start frame plus the pan
PLATE_TARGET = (6.0, 2.19, 1.0)           # plate centre; 640 px right and 420 px down of TARGET
PPM = 1920 / 11.0                         # keep the 11 m / 1920 px camera scale
LANE_Y = 1.7                              # a clear line down the footpath; nothing stands in it
RIYAZ_AT = (0.6, LANE_Y, 0.0)             # where the walk starts; every Riyaz frame is rendered here
HAND_R = (-0.32, 0.02, 0.6)               # local: the right arm hanging at his side, carrying the bag
REST = ((-0.3, 0.02, 0.6), (0.3, 0.02, 0.6))   # local: both arms hanging relaxed
# Riyaz's frames face along the axes: e +X (on down the street), w -X, n +Y (the shops), s -Y (the road)
DIRS = {"e": 90, "w": 270, "n": 180, "s": 0}
WALK_FRAMES = 8                           # one walk cycle: right contact, down, passing, up, left contact...
ANTHONY_AT = (3.15, 2.85, 0.0)            # behind his counter, against the wall
ARIF_AT = (7.0, 2.85, 0.0)                # in his doorway
LITTER_AT = Vector((13.0, 1.95, 0.0))      # against the market's boundary wall (V05)
PILE_TOP = 0.42
CART_AT = Vector((6.1, 1.95, 0.0))        # the handcart that rolls down across the walk (the mini-game)

# Shopfront rhythm along 20 m: piers, then a bay between each pair.
PIERS = ((-5.0, -4.7), (-1.7, -1.4), (1.7, 2.0), (4.8, 5.1), (8.0, 8.3), (10.7, 11.0))
BAYS = ((-4.7, -1.7), (-1.4, 1.7), (2.0, 4.8), (5.1, 8.0), (8.3, 10.7))
OPEN_BAYS = {0: "provisions", 1: "sweets", 2: "fruits"}   # open shops: their sign id and their stock


def plate_to_screen(point, _target=None):
    """World point -> plate pixel (3200x1920). Same 174.5 px/m and iso axes as rig.to_screen,
    but measured from the plate centre, whose top-left is the normal 1920x1080 start frame."""
    r = rig._rot().to_matrix()
    right, up = r @ Vector((1, 0, 0)), r @ Vector((0, 1, 0))
    d = Vector(point) - Vector(PLATE_TARGET)
    return PLATE_W / 2 + d.dot(right) * PPM, PLATE_H / 2 - d.dot(up) * PPM


def materials(m):
    s03.set_materials(m)                  # masonry_faint, posters, water, crate blue etc.
    signs = kit.SIGNS
    m.update(
        paving=M.paving("MAT_paving_s02", wet_centre=(12.6, 1.8), wet_radius=2.2),   # wet by the pile
        sign_a=M.image("MAT_s02_sign_a", signs / "s01-neighbour_left.png", box_uv=True) if (signs / "s01-neighbour_left.png").exists() else m["board_faded_a"],
        sign_b=M.image("MAT_s02_sign_b", signs / "s01-neighbour_right.png", box_uv=True) if (signs / "s01-neighbour_right.png").exists() else m["board_faded_b"],
        sack_white=M.plastic("MAT_sack_dirty_white", "#BDB5A6", 0.5),
        sack_black=M.plastic("MAT_sack_black", "#1F1D1C", 0.22),         # garbage-bag plastic: dark, with a sheen
        sack_grey=M.plastic("MAT_sack_grey", "#4A4E52", 0.25),
        bone=M.matte("MAT_bone", "#E3D2BE", 0.6),
        cardboard=M.matte("MAT_cardboard", "#8C7558", 0.85),
        leaf=M.matte("MAT_leaf_dry", "#6E6A45", 0.7),
        stain=M.matte("MAT_stain", "#3E352F", 0.25),
        crow=M.matte("MAT_crow", "#25221F", 0.5),
        beak=M.matte("MAT_beak", "#4A4440", 0.4),
        bag_waste=waste_bag("MAT_bag_waste"),
        pole=M.plaster("MAT_pole", "#9C978E", 0.2),
        cart_steel=M.steel("MAT_cart_steel", "env.steel", 0.45),
        tyre=M.matte("MAT_tyre", "#22201E", 0.8),
    )


def waste_bag(name):
    """The kilo, on the street: the same translucent carry bag as s01, but the bone and offal show
    through darker and a wet, stained base (it reads as waste, without gore)."""
    n = M.Nodes(name)
    contents = n.maprange(n.noise(3.5, 4, 0.6), 0.4, 0.7, 0.0, 0.55)
    base = n.mix(contents, M.rgb("#E6E2D8"), M.rgb("#7E4A3C"))
    wet = n.height_mask(0.3, 0.42)
    m = n.add("ShaderNodeMath", operation="MULTIPLY")
    n.link(wet, m.inputs[0])
    m.inputs[1].default_value = 0.6
    n.link(n.mix(m.outputs[0], base, M.rgb("#6E5048")), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.3)
    n.set("Subsurface Weight", 0.3)
    n.set("Coat Weight", 0.4)
    n.bump(n.noise(18, 6, 0.7), 0.35, 0.006)
    return n.mat


def facade(st):
    s, m, col = st.street, st.m, st.set
    for i, (x0, x1) in enumerate(PIERS):
        mat = (m["cream"], m["orange"], m["concrete"], m["cream_yellow"], m["cream"], m["concrete"])[i]
        kit.pier(s, f"FACADE_pier_{i}", x0, x1, mat, col, proud=0.03 if i % 2 else 0.0)
    rooms = []
    for i, (x0, x1) in enumerate(BAYS):
        if i in OPEN_BAYS:
            kit.shop_opening(s, f"FACADE_bay_{i}", x0, x1, m, col)
            kit.awning(s, f"SHOP_awning_{i}", x0 - 0.1, x1 + 0.1, m, col)
            kit.fascia(s, st.data, OPEN_BAYS[i], (x0 + x1) / 2, 3.18, m, col)     # its name, above the awning
            rooms.append((x0, x1, s.wall_y + 2.4, 3.0))
            shop_interior(st, i, x0, x1, OPEN_BAYS[i])
        elif i == 3:
            door_bay(st, x0, x1)
        else:
            kit.shutter_bay(s, f"FACADE_bay_{i}", x0, x1, m, col, m["sign_b"])        # the saree wholesaler, shut
    kit.upper_storey(s, m, col, windows=((-4.2, -2.6), (-1.2, 0.4), (1.6, 3.2), (4.4, 6.0), (7.2, 8.8)), ac_at=0.4)
    kit.building_mass(s, m, col, rooms=rooms)
    kit.facade_wires(s, m, col)


def shop_interior(st, i, x0, x1, kind):
    """A shallow, lit, stocked shop behind an open bay (R09, F05 density): a tiled back wall, shelves
    packed to the ceiling, a tube light, and the trade's own front display (see `stock`)."""
    s, m, col = st.street, st.m, st.set
    back = s.wall_y + 2.4
    geo.box(f"SHOP{i}_floor", (x0, s.wall_y, 0), (x1, back, 0.12), m["floor"], col, 0.01)
    geo.box(f"SHOP{i}_back", (x0, back, 0), (x1, back + 0.2, 3.0), m["tiles_in"], col, 0)
    geo.box(f"SHOP{i}_ceiling", (x0, s.wall_y, 2.95), (x1, back + 0.2, 3.05), m["ceiling"], col, 0)
    for side, x in (("L", x0), ("R", x1 - 0.05)):                    # side walls, so it reads as a room
        geo.box(f"SHOP{i}_side{side}", (x, s.wall_y + 0.25, 0), (x + 0.05, back, 2.95), m["tiles_in"], col, 0)
    # shelves packed to the top along the left side wall: the one wall the camera sees into
    sx = x0 + 0.05
    for k in range(4):
        z = 0.5 + k * 0.55
        geo.box(f"SHOP{i}_shelf{k}", (sx, s.wall_y + 0.3, z), (sx + 0.4, back - 0.1, z + 0.03), m["steel"], col, 0.004)
        rnd = random.Random(i * 10 + k)
        yy = s.wall_y + 0.35
        while yy < back - 0.3:
            w, h = rnd.uniform(0.14, 0.26), rnd.uniform(0.22, 0.42)
            tint = goods_tint(kind, rnd)
            geo.box(f"SHOP{i}_goods{k}_{yy:.2f}", (sx + 0.03, yy, z + 0.03), (sx + 0.37, yy + w, z + 0.03 + h),
                    M.plastic(f"MAT_goods_{kind}_{tint}", tint, 0.5), col, 0.01)
            yy += w + 0.02
    geo.box(f"SHOP{i}_tube", ((x0 + x1) / 2 - 0.6, s.wall_y + 0.5, 2.88), ((x0 + x1) / 2 + 0.6, s.wall_y + 0.56, 2.92), m["tube"], col, 0)
    light = rig.point_light(f"LIGHT_shop{i}", ((x0 + x1) / 2, s.wall_y + 1.0, 2.6), (1.0, 0.92, 0.8), 140, 0.4, col)
    light["practical"] = True
    stock(st, i, x0, x1, kind)


def goods_tint(kind, rnd):
    palettes = {
        "provisions": ("#C9A66B", "#B5452E", "#E6D9B8", "#3E6B8C", "#D9A93A", "#7A8C3E", "#A33A3F"),
        "sweets": ("#D9447A", "#E6C24A", "#F0E6D2", "#C9562E", "#7A3E8C", "#2E7A6B"),
        "fruits": ("#8C6A44", "#B89A6E", "#6E5A3E"),
    }
    return rnd.choice(palettes[kind])


def heap(name, centre, w, d, colour, r, col, rough=0.45, layers=3):
    """A pyramid of round goods (fruit, laddoos), stacked as they are on a stall."""
    mat = M.plastic(f"MAT_heap_{colour}", colour, rough)
    cx, cy, cz = centre
    nx, ny = max(1, int(w / (2 * r))), max(1, int(d / (2 * r)))
    for layer in range(layers):
        for a in range(nx - layer):
            for b in range(ny - layer):
                x = cx - (nx - layer - 1) * r + a * 2 * r
                y = cy - (ny - layer - 1) * r + b * 2 * r
                geo.sphere(f"{name}_{layer}_{a}_{b}", (x, y, cz + r + layer * r * 1.5), r, (1, 1, 0.92), mat, col, segments=12, rings=8)


def stock(st, i, x0, x1, kind):
    """The trade's front display, just inside the opening, where the street sees it."""
    s, m, col = st.street, st.m, st.set
    y = s.wall_y + 0.45
    if kind == "provisions":
        # open grain sacks with rolled tops: rice, dal, chilli, wheat, jaggery (F05)
        for k, colour in enumerate(("#EDE6D6", "#D9A93A", "#9C2B1E", "#C9A66B", "#8C5A2E")):
            x = x0 + 0.4 + k * ((x1 - x0 - 0.8) / 4)
            geo.cylinder(f"SHOP{i}_sack{k}", (x, y + 0.1, 0.12), 0.22, 0.48, m["sack_white"], col, segments=20, bevel=0.03)
            geo.cylinder(f"SHOP{i}_sack{k}_roll", (x, y + 0.1, 0.56), 0.235, 0.06, m["sack_white"], col, segments=20, bevel=0.02)
            geo.sphere(f"SHOP{i}_sack{k}_grain", (x, y + 0.1, 0.58), 0.2, (1, 1, 0.35), M.matte(f"MAT_grain_{colour}", colour, 0.85), col, segments=20, rings=10)
            geo.cylinder(f"SHOP{i}_scoop{k}", (x + 0.08, y + 0.05, 0.62), 0.04, 0.05, m["steel"], col, segments=12, bevel=0.004)
        geo.box(f"SHOP{i}_counter", (x1 - 1.2, y + 1.1, 0.12), (x1 - 0.2, y + 1.5, 0.95), m["steel_dark"], col, 0.02)
        geo.box(f"SHOP{i}_scale", (x1 - 0.9, y + 1.15, 0.95), (x1 - 0.55, y + 1.4, 1.02), m["steel"], col, 0.01)
    elif kind == "sweets":
        # an open, stepped display counter across the front: trays of laddoo, barfi, jalebi, mysore pak
        geo.box(f"SHOP{i}_case_base", (x0 + 0.2, y, 0.12), (x1 - 0.2, y + 0.3, 0.76), m["steel_dark"], col, 0.02)
        geo.box(f"SHOP{i}_case_step", (x0 + 0.2, y + 0.3, 0.12), (x1 - 0.2, y + 0.65, 1.0), m["steel_dark"], col, 0.02)
        n = 4
        tw = (x1 - x0 - 0.6) / n
        for tier, (z, ty) in enumerate(((0.76, 0.0), (1.0, 0.3))):
            for k in range(n):
                tx = x0 + 0.3 + k * tw
                geo.box(f"SHOP{i}_tray{tier}_{k}", (tx, y + ty + 0.02, z), (tx + tw - 0.06, y + ty + 0.3, z + 0.02), m["steel"], col, 0.004)
                kind_k = (k + tier * 2) % 4
                cx, cy = tx + (tw - 0.06) / 2, y + ty + 0.16
                if kind_k == 0:
                    heap(f"SHOP{i}_laddoo{tier}{k}", (cx, cy, z + 0.02), tw - 0.12, 0.24, "#E8932E", 0.035, col, 0.6, 2)
                elif kind_k == 2:
                    heap(f"SHOP{i}_jalebi{tier}{k}", (cx, cy, z + 0.02), tw - 0.12, 0.24, "#E07A1F", 0.03, col, 0.2, 2)
                else:
                    colour = "#E8E0C8" if kind_k == 1 else "#D9A93A"
                    for a in range(int((tw - 0.12) / 0.07)):
                        for b in range(4):  # noqa: B007
                            bx, by = tx + 0.04 + a * 0.07, y + ty + 0.04 + b * 0.06
                            geo.box(f"SHOP{i}_barfi{tier}{k}_{a}{b}", (bx, by, z + 0.02), (bx + 0.06, by + 0.065, z + 0.05),
                                    M.matte(f"MAT_barfi_{colour}", colour, 0.6), col, 0.004)
        # the sweet-seller behind the counter
        mats = people.costume_materials("sweets", shirt="#E2DED4", trousers="#D8D4CA", cap="#EAE6DC")
        people.figure("SWEETS_seller", ((x0 + x1) / 2 + 0.3, y + 1.0, 0.12), 0, mats, *REST, col)
    elif kind == "fruits":
        # stepped crates of fruit rising to the back, bananas hung on a rail (F05)
        for step, z in enumerate((0.12, 0.45, 0.78)):
            yy = y + 0.25 + step * 0.45
            geo.box(f"SHOP{i}_step{step}", (x0 + 0.2, yy - 0.2, 0), (x1 - 0.2, yy + 0.2, z), m["crate_dusty"], col, 0.01)
            for k, colour in enumerate(("#E07A1F", "#A8282E", "#7FA33A", "#C9A12E", "#7A2E3A")):
                fx = x0 + 0.45 + k * ((x1 - x0 - 0.9) / 4)
                if (k + step) % 2 == 0 or step == 0:
                    heap(f"SHOP{i}_fruit{step}_{k}", (fx, yy, z), 0.4, 0.3, colour, 0.045, col, 0.35, 2)
        geo.limb(f"SHOP{i}_rail", (x0 + 0.3, y + 0.15, 2.4), (x1 - 0.3, y + 0.15, 2.4), 0.015, 0.015, m["steel"], col)
        for k in range(5):
            bx = x0 + 0.5 + k * ((x1 - x0 - 1.0) / 4)
            geo.limb(f"SHOP{i}_banana_stalk{k}", (bx, y + 0.15, 2.4), (bx, y + 0.15, 1.9), 0.02, 0.02, m["stem"] if "stem" in m else m["cable"], col)
            for j in range(6):
                a = j * 1.05
                geo.sphere(f"SHOP{i}_banana{k}_{j}", (bx + math.cos(a) * 0.07, y + 0.15 + math.sin(a) * 0.07, 2.25 - (j % 3) * 0.12), 0.035,
                           (1, 1, 3.2), M.plastic("MAT_banana", "#D9C23A", 0.4), col, segments=10, rings=6, rot=(0.35 * math.cos(a), 0.35 * math.sin(a), 0))


def door_bay(st, x0, x1):
    """Arif's doorway: a recessed dark door between half-shutters (task 11 needs him in a doorway)."""
    s, m, col = st.street, st.m, st.set
    geo.box("DOOR_recess", (6.35, 2.975, 0), (7.65, 3.02, 2.15), m["window_glass"], col, 0)
    for name, lo, hi in (("lintel", (6.28, 2.96, 2.12), (7.72, 3.10, 2.24)), ("jamb_L", (6.28, 2.96, 0), (6.38, 3.10, 2.16)),
                         ("jamb_R", (7.62, 2.96, 0), (7.72, 3.10, 2.16))):
        geo.box(f"DOOR_{name}", lo, hi, m["window_frame"], col, geo.BEVEL_PROP)
    for name, a, b in (("L", x0, 6.28), ("R", 7.72, x1)):
        geo.box(f"DOOR_shutter_{name}", (a, s.wall_y + 0.08, 0), (b, s.wall_y + 0.12, 2.6), m["shutter"], col, 0.005)
    geo.box("DOOR_lintel_wall", (x0, s.wall_y, 2.24), (x1, s.wall_y + s.wall_t, s.chajja_z), m["cream"], col, geo.BEVEL_ARCH)
    geo.box("DOOR_board", (x0 + 0.05, s.wall_y - 0.06, 3.1), (x1 - 0.05, s.wall_y, 3.85), m["board_faded_b"], col)


def market_corner(st):
    """Russell Market's side, where the lane turns behind it: white masonry with the pink ghost,
    pilasters, a pointed blind arch and the bracketed cornice (X04/R24, X03/R23), posters."""
    s, m, col = st.street, st.m, st.set
    w = s.wall_y - 0.06
    geo.box("MARKET_front", (11.0, w, 0), (15.0, w + 0.3, 7.4), m["masonry"], col, geo.BEVEL_ARCH)
    geo.box("MARKET_mass", (11.0, w + 0.3, 0), (15.0, 5.9, 7.4), m["concrete"], col, 0)
    geo.box("MARKET_base", (11.0, w - 0.08, 0), (15.0, w, 0.42), m["masonry"], col, geo.BEVEL_ARCH)
    for i, (x0, x1) in enumerate(((11.0, 11.45), (14.55, 15.0))):
        geo.box(f"MARKET_pilaster{i}", (x0, w - 0.14, 0), (x1, w, 7.4), m["masonry"], col, geo.BEVEL_ARCH)
    s03.arch_band("MARKET_blind_arch", 13.0, 2.6, 2.1, 1.0, 0.42, 0.12, w - 0.04, m["masonry"], col)
    geo.box("MARKET_cornice", (11.0, w - 0.32, 4.3), (15.0, w, 4.45), m["masonry"], col, geo.BEVEL_ARCH)
    for k in range(6):
        x = 11.3 + k * 0.6
        geo.box(f"MARKET_bracket{k}", (x - 0.05, w - 0.26, 4.05), (x + 0.05, w, 4.3), m["masonry"], col, geo.BEVEL_PROP)
    for i, (x0, x1, z0, z1, mat) in enumerate(((11.05, 11.4, 1.2, 1.7, "poster_a"), (11.08, 11.38, 1.78, 2.1, "poster_b"),
                                               (14.6, 14.95, 1.1, 1.55, "poster_b"))):
        geo.box(f"MARKET_poster{i}", (x0, w - 0.146, z0), (x1, w - 0.14, z1), m[mat], col, 0)
    # the drain along the kerb, wet where the lane is hosed
    geo.box("DRAIN_channel", (9.0, 0.42, -0.04), (15.0, 0.66, 0.002), m["cable"], col, 0)
    geo.box("DRAIN_grate", (9.02, 0.44, 0.0), (14.98, 0.64, 0.006), m["grate"], col, 0)


def street_props(st):
    """What lines the shop side of the walk (F01-F04): red crates and a blue drum by the shutters,
    a plastic chair at a shop door, Anthony's stall against the wall. All of it behind the lane."""
    m, col = st.m, st.props
    for i, (x, y, z, r) in enumerate(((1.0, 2.62, 0, 0), (1.02, 2.62, 0.3, 8), (1.5, 2.66, 0, -6), (9.3, 2.62, 0, 12))):
        kit.ph(f"PROP_crate{i}", "plastic_crate_01", (x, y, z), r, 1.0, col)                       # F03, R13
    geo.cylinder("PROP_drum", (9.85, 2.68, 0), 0.28, 0.85, m["drum"], col)                      # F03 blue drum
    kit.ph("PROP_chair_a", "plastic_monobloc_chair_01", (4.5, 2.55, 0), 200, 1.0, col)           # R08, at the shop door

    # Anthony's stall: a steel counter against the wall with crates of produce (F05 density, muted)
    geo.box("STALL_counter", (2.45, 2.3, 0), (3.85, 2.65, 0.88), m["steel_dark"], col, 0.02)
    geo.box("STALL_top", (2.42, 2.26, 0.88), (3.88, 2.68, 0.94), m["steel"], col, 0.01)
    for k, x in enumerate((2.6, 3.05, 3.5)):
        geo.box(f"STALL_tray{k}", (x - 0.18, 2.32, 0.94), (x + 0.18, 2.62, 1.02), m["crate_dusty"], col, 0.01)
        for j in range(5):
            geo.sphere(f"STALL_fruit{k}_{j}", (x - 0.12 + j * 0.06, 2.44 + (j % 2) * 0.06, 1.05), 0.04, (1, 1, 1),
                       M.plastic(f"MAT_fruit{k}", ("#A8823F", "#8E5A3C", "#9A8F4E")[k], 0.5), col)


def kerb_side(st):
    """In front of the lane, at the kerb (FG): the leaning lamp pole with its transformer and wires
    (R19, V03), one passer-by. The game draws these over Riyaz."""
    s, m, col = st.street, st.m, st.fg
    kit.lamp_pole("POLE", 10.85, 0.35, m, col, height=7.2, transformer=True)
    for i, z in enumerate((6.4, 6.6)):
        kit.wire(f"POLE_wire{i}", (11.1, 0.3, z), (4.0, s.wall_y - 0.1, 4.75 + i * 0.08), 0.3, m["cable"], col)
    kit.pedestrian("PED_kerb", (-2.2, 0.55, 0), 95, col, kind=1, stride=0.15)


def dress(st):
    """The Shivajinagar kit along the walk (V01-V05), thinned so the footpath reads as a footpath:
    two-wheelers and autos on the road (none on the footpath), projecting flex boards and banners,
    the shops' own displays, one shopper; at the market end the pink-over-
    stone boundary wall, and the rain tree and bollards at the kerb."""
    s, m, col = st.street, st.m, st.props
    for i, x in enumerate((-3.6, 1.2, 12.2)):                                     # a few along the kerb, on the road
        kit.two_wheeler_row(f"BIKE_kerb_{i}", x, x, -0.6, m, col, heading=90, z=kit.ROAD_Z)
    for i, (x, y) in enumerate(((4.6, -1.3), (9.4, -2.2))):                      # autos on the road (V02, V03)
        kit.autorickshaw(f"AUTO_{i}", (x, y, kit.ROAD_Z), 0, m, col)
    prints = ("flex_biryani", "flex_chai", "flex_falooda", "flex_kebab")
    for i, (x, z, mat) in enumerate(((-1.55, 3.35, "flex_red"), (1.85, 3.45, "flex_yellow"), (4.95, 3.3, "flex_blue"), (8.15, 3.45, "flex_red"))):
        kit.flex_board(f"FLEX_{i}", x, z, 1.1, s, m, m[mat], col, sign=kit.sign_material(st.data, prints[i], m[mat], box_uv=False))
    for i, x in enumerate((-1.55, 4.95)):                    # the UPI QR on the piers, as at Riyaz's stall (F04)
        kit.sticker(s, st.data, "upi_sticker", x, 1.35, 0.03, col)
    kit.banner("BANNER_0", 0.4, 4.6, 6.6, 0.9, s, m["flex_yellow"], col)
    kit.banner("BANNER_1", 6.2, 4.5, 6.2, 0.8, s, m["flex_blue"], col)
    kit.ph("MANHOLE", "water_manhole_cover", (8.2, 1.6, 0.002), 0, 1.0, col)        # flat: the lane walks over it
    kit.pedestrian("PED_shop", (8.75, 2.55, 0), 200, col, kind=2)                    # at the shops, looking in
    # the market end (V05): boundary wall, pink plaster over a stone base; the tree and bollards at the kerb
    geo.box("BWALL_base", (11.45, 2.55, 0), (15.0, 2.8, 0.7), m["stone_base"], col, 0.02)
    geo.box("BWALL", (11.45, 2.57, 0.7), (15.0, 2.78, 2.3), m["pink_wall"], col, 0.02)
    geo.box("BWALL_coping", (11.4, 2.52, 2.3), (15.0, 2.83, 2.4), m["stone_base"], col, 0.02)
    kit.rain_tree("TREE", 14.3, 0.7, m, st.fg)
    kit.bollards("BOLLARD", (11.6, 12.4, 13.9), 0.6, m, st.fg)


def life(st):
    """Street life (V01, V03, V05): cable bundles and meter boxes along the facade, AC units with their
    drip stains, crows on the sunshade, marigolds over the sweet shop, a dog asleep by the drum, a
    pavement vendor at the market end, and people on both sides of the lane (never in it)."""
    s = st.street
    street_life.wires(st, s.x0, 11.0)
    street_life.ac_units(st, (-2.45, 3.3, 6.1), z=5.0)
    street_life.crows(st, (-0.8, 1.1, 5.5, 9.6), s.chajja_z)
    street_life.marigolds(st, -1.3, 1.6)
    street_life.dog(st, (8.05, 2.42, 0), 5)
    street_life.vendors(st, (14.35,), 2.1, side=-1)
    street_life.people(st, [("PED_kurta", (3.6, 0.6), 100, "kurta", 0.15), ("PED_porter", (7.9, 0.75), -80, "porter", 0.14)], col=st.fg)
    street_life.people(st, [("PED_lungi", (0.4, 2.42), 170, "lungi", 0.0)])


def lane_check(st):
    """Stop the build if anything that stands up sits in Riyaz's lane (why this set was rebuilt)."""
    bad = []
    for col in (st.set, st.props, st.fg):
        for o in col.all_objects:
            if o.type != "MESH":
                continue
            pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo_y, hi_y = min(p.y for p in pts), max(p.y for p in pts)
            lo_x, hi_x = min(p.x for p in pts), max(p.x for p in pts)
            lo_z, hi_z = min(p.z for p in pts), max(p.z for p in pts)
            if hi_z > 0.05 and lo_z < 2.0 and lo_y < LANE_Y + 0.3 and hi_y > LANE_Y - 0.3 and hi_x > -1.0 and lo_x < 10.6:
                bad.append(o.name)
    if bad:
        raise SystemExit(f"[s02] in Riyaz's lane: {', '.join(sorted(bad)[:20])}")


def cart(st):
    """PROP_cart: a steel handcart with a blue tarp bundle (F01). It rolls straight down from the
    shopfront across the footpath to the road mid-walk, so it is built lengthwise along Y with its
    handle trailing (+Y, toward the shops). Its own free layer, so Station02 can roll it."""
    m, col = st.m, st.prop("cart", free=True)
    c = CART_AT
    root = geo.empty("CART", (0, 0, 0), col)
    before = set(col.objects)
    geo.box("CART_bed", (-0.75, -0.4, 0.55), (0.75, 0.4, 0.62), m["cart_steel"], col, 0.01)
    for name, lo, hi in (("rail_f", (-0.75, -0.42, 0.62), (0.75, -0.38, 0.75)),
                         ("rail_b", (-0.75, 0.38, 0.62), (0.75, 0.42, 0.75))):
        geo.box(f"CART_{name}", lo, hi, m["cart_steel"], col, 0.005)
    for i, x in enumerate((-0.45, 0.45)):
        geo.cylinder(f"CART_wheel{i}", (x, -0.44, 0.28), 0.28, 0.06, m["tyre"], col, axis="Y", segments=28, bevel=0.01)
        geo.cylinder(f"CART_wheel{i}b", (x, 0.38, 0.28), 0.28, 0.06, m["tyre"], col, axis="Y", segments=28, bevel=0.01)
    geo.limb("CART_handle", (-0.75, 0, 0.6), (-1.15, 0, 0.95), 0.02, 0.02, m["cart_steel"], col)
    geo.box("CART_tarp", (-0.6, -0.32, 0.62), (0.55, 0.32, 1.05), m["tarp"], col, 0, subsurf=2)
    catcher = kit.shadow_catcher("CART_shadow_catcher", (0, 0, 0.003), (2.2, 1.4), m, col)
    for o in set(col.objects) - before:
        if o.parent is None and o is not root:
            o.parent = root
    root.location = c
    root.rotation_euler = (0, 0, -math.pi / 2)         # its length along Y, the handle (-X when built) to +Y
    catcher["shadow_catcher"] = True
    st.anchor("cart_centre", (c.x, c.y, 0.6))
    st.anchor("cart_shadow_extent", (c.x + 0.7, c.y - 1.1, 0.0))     # pack_layers: keep the long shadow whole


def litter(st):
    """The Run 1 pile behind Russell Market: split sacks of bone and offal, a sack of rubbish,
    cardboard, a dry leaf, wet stains, two crows. It is a PROP so Run 2 can show the clean pavement."""
    m, col = st.m, st.prop("litter")
    c = LITTER_AT
    sacks = ((-0.5, 0.05, "sack_black", 1.5), (0.05, -0.2, "sack_black", 1.6), (0.5, 0.1, "sack_grey", 1.4),
             (0.0, 0.35, "sack_grey", 1.3), (-0.75, -0.3, "bag_waste", 1.0), (0.75, -0.35, "bag_waste", 0.9))
    for i, (dx, dy, mat, k) in enumerate(sacks):
        root = geo.empty(f"LITTER_sack{i}_root", (c.x + dx, c.y + dy, 0), col)
        objs, _ = kit.kilo_bag(f"LITTER_sack{i}", (c.x + dx, c.y + dy, 0.12), 0.0, {"bag": m[mat]}, col)
        for o in objs:                               # scale about the sack's base, not the world origin
            o.parent = root
            o.matrix_parent_inverse = Matrix.Translation(-root.location)
        root.scale = (k, k, k)                    # sacks, not carry bags: scaled about their base
    # the split sack spills bone and offal onto the paving
    for i in range(7):
        a = i * 0.9
        geo.sphere(f"LITTER_bone{i}", (c.x - 0.2 + math.cos(a) * 0.35, c.y - 0.55 + math.sin(a) * 0.12, 0.03), 0.035,
                   (2.2, 0.8, 0.7), m["bone"], col, rot=(0, 0, a))
    for i in range(4):
        geo.sphere(f"LITTER_offal{i}", (c.x + 0.25 + i * 0.12, c.y - 0.45 - (i % 2) * 0.08, 0.03), 0.05, (1.3, 1.0, 0.45), m["meat"], col)
    kit.ph("LITTER_cardboard", "cardboard_box_01", (c.x + 0.95, c.y - 0.3, 0), 18, 1.0, col)
    kit.ph("LITTER_rat", "street_rat", (c.x - 1.2, c.y - 0.8, 0), -60, 1.0, col)
    geo.box("LITTER_leaf", (c.x - 1.1, c.y - 0.1, 0.0), (c.x - 0.6, c.y + 0.25, 0.008), m["leaf"], col, 0)
    for i, (dx, dy, r) in enumerate(((0.0, -0.4, 0.75), (-0.9, 0.2, 0.4), (0.9, -0.6, 0.35))):
        p = geo.cylinder(f"LITTER_stain{i}", (c.x + dx, c.y + dy, 0.0), r, 0.004, m["stain"], col, segments=28, bevel=0)
        p.scale = (1.6, 0.9, 1.0)
    for i, (dx, dy, z, rot) in enumerate(((-1.25, -0.45, 0.0, 20), (1.2, -0.75, 0.0, -50))):
        crow(f"LITTER_crow{i}", Vector((c.x + dx, c.y + dy, z)), rot, m, col)
    kit.shadow_catcher("LITTER_shadow_catcher", (c.x, c.y, 0.002), (2.6, 1.7), m, col)
    st.anchor("litter_centre", (c.x, c.y, PILE_TOP))
    st.anchor("dump", (c.x, c.y, PILE_TOP))


def crow(name, at, rot, m, col):
    """A house crow on the pile, simple and dark: body, head, beak, tail."""
    r = math.radians(rot)
    fwd = Vector((math.cos(r), math.sin(r), 0))
    geo.sphere(f"{name}_body", at + Vector((0, 0, 0.1)), 0.08, (1.5, 0.9, 0.9), m["crow"], col, rot=(0, 0, r))
    geo.sphere(f"{name}_head", at + fwd * 0.12 + Vector((0, 0, 0.18)), 0.05, (1, 1, 1), m["crow"], col)
    geo.limb(f"{name}_beak", at + fwd * 0.16 + Vector((0, 0, 0.18)), at + fwd * 0.23 + Vector((0, 0, 0.165)), 0.015, 0.003, m["beak"], col, segments=6)
    geo.limb(f"{name}_tail", at - fwd * 0.1 + Vector((0, 0, 0.11)), at - fwd * 0.24 + Vector((0, 0, 0.07)), 0.03, 0.012, m["crow"], col, segments=6)
    for i, s_ in enumerate((-1, 1)):
        side = Vector((-fwd.y, fwd.x, 0)) * 0.03 * s_
        geo.limb(f"{name}_leg{i}", at + side + Vector((0, 0, 0.05)), at + side, 0.006, 0.006, m["beak"], col, segments=5)


def riyaz(st):
    """Riyaz with the kilo in his right hand, in each of the four directions: an eight-frame walk and a
    stand, plus a stand with empty hands for after the dump. All rendered at RIYAZ_AT; the kilo rides
    in each frame (it swings with the hand), and is also its own free prop so Run 1 can throw it."""
    m = st.m
    mats = people.costume_materials("riyaz", wet_hands=True)
    bag_mat = {"bag": m["bag_waste"]}

    def frame(pose, heading, right, left, grip, carry, **kw):
        c = st.char("riyaz", pose, free=True)
        root = people.figure(f"RIYAZ_{pose}", RIYAZ_AT, heading, mats, right, left, c, grip=grip, **kw)
        if not carry:
            return None, None
        bpy.context.view_layer.update()
        w = Vector(root["wrist"])                      # the bag hangs just outside and below the fist
        centre = root.matrix_world @ Vector((w.x - 0.05, w.y, w.z - 0.22))
        _, knot = kit.kilo_bag(f"KILO_{pose}", centre, centre.z - 0.13, bag_mat, c)
        return centre, knot

    for d, heading in DIRS.items():
        for i in range(WALK_FRAMES):
            g = people.gait(i / WALK_FRAMES, stride=0.24, carry=True)
            frame(f"walk_{d}{i}", heading, g["right_hand"], g["left_hand"], ("fist", "loose"), True, **g["pose"])
        centre, knot = frame(f"stand_{d}", heading, HAND_R, REST[1], ("fist", "loose"), True)
        st.anchor(f"riyaz_hand_{d}", knot)
        frame(f"empty_{d}", heading, *REST, ("loose", "loose"), False)
        if d == "e":                                   # the throwable kilo, where the east stand holds it
            kilo = st.prop("kilo", free=True)
            _, bag_knot = kit.kilo_bag("KILO_bag", centre, centre.z - 0.13, bag_mat, kilo)
            st.anchor("kilo_knot", bag_knot)
            st.anchor("kilo_centre", centre)
    st.anchor("riyaz_hand", st.anchors["riyaz_hand_e"])
    st.anchor("riyaz_feet", RIYAZ_AT)
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], 1.75))
    st.world["chars"]["riyaz"] = RIYAZ_AT[:2]


def stakeholders(st):
    """Anthony behind his stall and Arif in his doorway (task 11), standing easy."""
    for name, origin, heading, anchor in (("anthony", ANTHONY_AT, 10, "anthony_head"), ("arif", ARIF_AT, -10, "arif_head")):
        mats = people.costume_materials(name)
        people.figure(f"{name.upper()}_idle", origin, heading, mats, *REST, st.char(name, "idle"))
        st.anchor(anchor, (origin[0], origin[1], 1.75))
        st.world["chars"][name] = origin[:2]


def footprint(objs, below=0.5):
    """World XY box of what stands on the ground: mesh bounds whose bottom is below `below` m (a tree's
    trunk, not its canopy; a pole, not its wires)."""
    bpy.context.view_layer.update()
    xs, ys = [], []
    for o in objs:
        if o.type not in {"MESH", "CURVE"}:
            continue
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if min(p.z for p in pts) > below or (max(p.x for p in pts) - min(p.x for p in pts)) > 4.0:
            continue                                     # (a stray import with wild bounds is not ground)
        xs += [p.x for p in pts]
        ys += [p.y for p in pts]
    return [round(min(xs), 3), round(max(xs), 3), round(min(ys), 3), round(max(ys), 3)] if xs else None


def piece(o):
    """Which set piece an object belongs to: its top parent (a model, a figure, a vehicle), else its
    name's first word (STALL_counter -> STALL), or first two for PROP_/PED_ names."""
    while o.parent is not None:
        o = o.parent
    n = o.name.removesuffix("_root")
    words = n.split("_")
    if o.children or len(words) == 1:
        return n
    return "_".join(words[:2]) if words[0] in ("PROP", "PED") else words[0]


def occluders(st):
    """Every set piece standing on or by the footpath (in PROPS or FG, at least 25 cm tall) gets its
    objects tagged ["occ"] = name, so render_station renders it alone as occ_<name>; its ground
    footprint goes in scene["world"] for Station02 to sort and collide by. Then the litter and cart
    footprints, and four reference points for turning world metres into plate pixels."""
    groups = {}
    for col in (st.props, st.fg):
        for o in col.all_objects:
            groups.setdefault(piece(o), []).append(o)
    for name, objs in groups.items():
        fp = footprint(objs)
        tall = max((max((o.matrix_world @ Vector(c)).z for c in o.bound_box) for o in objs if o.type == "MESH"), default=0)
        if not fp or tall < 0.25 or fp[3] < -3.0 or fp[2] > 2.95 or fp[1] < -6 or fp[0] > 16:
            continue
        key = name.lower()
        for o in objs:
            o["occ"] = key
        st.world["occ"][key] = fp
    litter = [o for o in bpy.data.collections["PROP_litter"].all_objects       # (near the pile: the rat import
              if not o.get("shadow_catcher") and abs(o.matrix_world.translation.x - LITTER_AT.x) < 2.5]   # carries a stray part)
    st.world["litter"] = footprint(litter)
    cart = [o for o in bpy.data.collections["PROP_cart"].all_objects if not o.get("shadow_catcher")]
    st.world["cart"] = footprint(cart, below=1.0)
    for k, p in (("o", (0, 0, 0)), ("x", (1, 0, 0)), ("y", (0, 1, 0)), ("z", (0, 0, 1))):
        st.anchor(f"proj_{k}", p)


def build():
    st = station.begin("s02")
    st.world = {"occ": {}, "chars": {}}
    materials(st.m)
    kit.plinth(st.street, st.m, st.set)
    kit.road(st.street, st.m, st.set)
    facade(st)
    market_corner(st)
    kit.kit_materials(st.m)
    street_props(st)
    kerb_side(st)
    dress(st)
    life(st)
    lane_check(st)
    cart(st)
    litter(st)
    riyaz(st)
    stakeholders(st)
    occluders(st)

    st.anchor("street_start", (0.0, 3.0, 1.0))
    st.anchor("street_end", (10.0, 3.0, 1.0))
    st.anchor("street_hub", (13.2, 3.0, 1.0))     # the short approach that frames the pile

    # Same camera, wider canvas: widen the ortho scale in proportion so the pixels-per-metre
    # stays 174.5, and write anchors in plate pixels. The game crops a 1920x1080 window.
    rig.ORTHO_SCALE = 11.0 * PLATE_W / 1920
    rig.to_screen = plate_to_screen
    bpy.context.scene["world"] = json.dumps(st.world)
    st.finish(PLATE_TARGET)
    bpy.context.scene.render.resolution_x = PLATE_W
    bpy.context.scene.render.resolution_y = PLATE_H
    safety.save(st.blend)


if __name__ == "__main__":
    build()

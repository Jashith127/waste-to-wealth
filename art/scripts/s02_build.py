"""Station 2 · The walk, Market street to Russell Market. Grey box, 20 m of frontage.

Run:  blender -b --python art/scripts/s02_build.py
Then: blender -b art/blender/s02_walk.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s02

Re-runnable. Destructive only to art/blender/s02_walk.blend, which lib/safety backs up
before every save. Content: src/data/stations/s02.json. Set is grey-box: every shared kit
piece is re-materialled to m["grey"] / m["grey_dark"]; the one exception is the market
corner's masonry pier, which marks where the final art goes (art-bible §0).

Street slice: pavement y 0..3, wall at y 3.0, frontage x -5..15. Riyaz, his bag, the two
placeholder figures and the market corner are placed so the scene can pan along the street:
the world slides by the screen delta between anchors street_start (x 0) and street_end (x 10).

The walk needs more street than one 1920 frame holds, so this station renders a 3200x1920 plate
at the same 174.5 px/m as every other station, with the same camera (only the canvas is wider).
The plate's top-left is the normal start frame; Station02 shows a 1920x1080 window and slides it
right/down across the plate. Anchors are in plate pixels.
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
import station  # noqa: E402
from mathutils import Vector  # noqa: E402

TARGET = (0.0, 3.0, 1.0)                 # camera focal point: the start of the walk
PLATE_W, PLATE_H = 3200, 1920             # the street plate: 1920x1080 start frame plus the pan
PLATE_TARGET = (6.0, 2.19, 1.0)           # plate centre; 640 px right and 420 px down of TARGET
PPM = 1920 / 11.0                         # keep the 11 m / 1920 px camera scale
RIYAZ_AT = (0.2, 2.8, 0.0)               # on the pavement, near the shopfronts
BAG_CENTRE = Vector((-0.12, 2.68, 0.79))
ANTHONY_AT = (3.0, 2.4, 0.0)
ARIF_AT = (7.0, 2.8, 0.0)
LITTER_AT = Vector((13.0, 2.7, 0.0))
PILE_TOP = 0.30

# Shopfront rhythm along 20 m: piers, then a shutter bay or a doorway between them.
PIERS = ((-5.0, -4.7), (-1.7, -1.4), (1.7, 2.0), (4.8, 5.1), (8.0, 8.3), (10.7, 11.0))
BAYS = ((-4.7, -1.7), (-1.4, 1.7), (2.0, 4.8), (5.1, 8.0), (8.3, 10.7))


def plate_to_screen(point, _target=None):
    """World point -> plate pixel (3200x1920). Same 174.5 px/m and iso axes as rig.to_screen,
    but measured from the plate centre, whose top-left is the normal 1920x1080 start frame."""
    r = rig._rot().to_matrix()
    right, up = r @ Vector((1, 0, 0)), r @ Vector((0, 1, 0))
    d = Vector(point) - Vector(PLATE_TARGET)
    return PLATE_W / 2 + d.dot(right) * PPM, PLATE_H / 2 - d.dot(up) * PPM


def grey_kit(m):
    """The shared kit, re-materialled for the blockout. Masonry stays real: it marks the corner."""
    dark = {"kerb", "bedding", "soil", "section", "shutter", "shutter_box", "window_frame",
            "window_glass", "floor", "cable", "ac", "chair_navy", "drum", "crate_dusty", "catcher"}
    g = dict(m)
    for key in ("paving", "kerb", "bedding", "soil", "section", "cream", "cream_yellow", "orange",
                "upper", "concrete", "shutter", "shutter_box", "window_frame", "window_glass",
                "tiles_in", "tiles_checker", "floor", "ceiling", "awning", "tarp",
                "board_faded_a", "board_faded_b", "chair_navy", "chair_cream", "crate_dusty",
                "drum", "scooter", "seat", "ac", "cable"):
        g[key] = m["grey_dark"] if key in dark else m["grey"]
    return g


def facade(st, gm):
    s, m, col = st.street, st.m, st.set
    for i, (x0, x1) in enumerate(PIERS):
        kit.pier(s, f"FACADE_pier_{i}", x0, x1, m["grey"], col)
    for i, (x0, x1) in enumerate(BAYS):
        kit.shutter_bay(s, f"FACADE_bay_{i}", x0, x1, gm, col, m["grey"])

    # The market corner: a plain grey block, with the masonry pier marking where the real
    # Russell Market front goes for task 13.
    geo.box("MARKET_front", (11.0, 2.94, 0), (15.0, 3.24, 7.4), m["grey"], col, geo.BEVEL_ARCH)
    geo.box("MARKET_mass", (11.0, 3.24, 0), (15.0, 5.9, 7.4), m["grey_dark"], col, 0)
    kit.pier(s, "MARKET_pier_masonry", 11.0, 11.6, m["masonry"], col, proud=0.07)
    geo.box("MARKET_cornice", (11.0, 2.9, 4.2), (15.0, 3.26, 4.34), m["grey_dark"], col, 0.02)

    # A grey stall for Anthony (task 11), and a recessed doorway for Arif.
    geo.box("STALL_counter", (2.45, 2.62, 0), (3.55, 2.92, 0.88), m["grey_dark"], col, 0.02)
    geo.box("STALL_top", (2.42, 2.58, 0.88), (3.58, 2.96, 0.95), m["grey"], col, 0.015)
    geo.box("DOOR_recess", (6.35, 2.975, 0), (7.65, 3.02, 2.15), m["grey_dark"], col, 0)
    for name, lo, hi in (
        ("lintel", (6.28, 2.96, 2.12), (7.72, 3.10, 2.24)),
        ("jamb_L", (6.28, 2.96, 0), (6.38, 3.10, 2.16)),
        ("jamb_R", (7.62, 2.96, 0), (7.72, 3.10, 2.16)),
    ):
        geo.box(f"DOOR_{name}", lo, hi, m["grey_dark"], col, geo.BEVEL_PROP)


def litter(st):
    """The Run 1 pile: four oversized grey sacks on the pavement, with a contact shadow layer."""
    m, col = st.m, st.prop("litter")
    root = geo.empty("LITTER_root", LITTER_AT, col)
    offsets = ((-0.40, 0.00), (0.05, -0.16), (0.42, 0.03), (0.02, 0.22))
    for i, (dx, dy) in enumerate(offsets):
        objs, _ = kit.kilo_bag(f"LITTER_sack{i}", (dx, dy, 0.12), 0.0,
                               {"bag": m["grey_dark"]}, col)
        for o in objs:
            geo.parent_keep(o, root)
    root.scale = (1.6, 1.6, 1.6)              # task 02: kilo_bag shapes at 1.6x
    kit.shadow_catcher("LITTER_shadow_catcher", (LITTER_AT.x, LITTER_AT.y, 0.002),
                       (2.3, 1.5), m, col)
    st.anchor("litter_centre", (LITTER_AT.x, LITTER_AT.y, PILE_TOP))
    st.anchor("dump", (LITTER_AT.x, LITTER_AT.y, PILE_TOP))


def riyaz(st):
    """Riyaz carries the kilo in his right hand. The bag is its own prop layer so Run 1 can
    leave it on the pile without needing a second character pose."""
    m, col = st.m, st.set
    mats = people.costume_materials("riyaz02", apron="#D6CFC0", cap="#E6E2D8", wet_hands=True)
    knot = Vector((BAG_CENTRE.x, BAG_CENTRE.y, BAG_CENTRE.z + 0.21))
    right = people.local(knot, RIYAZ_AT)
    left = (0.24, 0.02, 0.90)
    people.figure("RIYAZ_walk", RIYAZ_AT, 0, mats, right, left, st.char("riyaz", "walk"),
                  moustache=True)

    kilo = st.prop("kilo")
    _, bag_knot = kit.kilo_bag("KILO_bag", BAG_CENTRE, BAG_CENTRE.z - 0.13, m, kilo)
    st.anchor("riyaz_hand", bag_knot)
    st.anchor("kilo_knot", bag_knot)
    st.anchor("kilo_centre", BAG_CENTRE)
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], 1.56))


def placeholder_figures(st):
    """Two plain grey figures for the stakeholder cards (task 11)."""
    m, col = st.m, st.set
    for name, origin, anchor in (("anthony", ANTHONY_AT, "anthony_head"),
                                 ("arif", ARIF_AT, "arif_head")):
        mats = people.costume_materials(name, shirt="#9A958E", cap=None)
        people.figure(f"{name.upper()}_idle", origin, 0, mats,
                      (-0.26, -0.02, 0.90), (0.26, -0.02, 0.90),
                      st.char(name, "idle"), moustache=True)
        st.anchor(anchor, (origin[0], origin[1], 1.56))


def build():
    st = station.begin("s02")
    m = st.m
    gm = grey_kit(m)
    kit.plinth(st.street, gm, st.set)
    facade(st, gm)
    kit.upper_storey(st.street, gm, st.set,
                     windows=((-4.2, -2.6), (-1.2, 0.4), (1.6, 3.2), (4.4, 6.0),
                              (7.2, 8.8), (10.0, 11.6), (12.8, 14.4)), ac_at=0.4)
    kit.building_mass(st.street, gm, st.set)
    kit.facade_wires(st.street, gm, st.set)
    litter(st)
    riyaz(st)
    placeholder_figures(st)

    st.anchor("street_start", (0.0, 3.0, 1.0))
    st.anchor("street_end", (10.0, 3.0, 1.0))
    st.anchor("street_hub", (13.2, 3.0, 1.0))     # the short approach that frames the pile

    # Same camera, wider canvas: widen the ortho scale in proportion so the pixels-per-metre
    # stays 174.5, and write anchors in plate pixels. The game crops a 1920x1080 window.
    rig.ORTHO_SCALE = 11.0 * PLATE_W / 1920
    rig.to_screen = plate_to_screen
    st.finish(PLATE_TARGET)
    bpy.context.scene.render.resolution_x = PLATE_W
    bpy.context.scene.render.resolution_y = PLATE_H
    safety.save(st.blend)


if __name__ == "__main__":
    build()

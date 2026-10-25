"""Station 3 · Weigh-in and payment, the hub's front counter. Grey box.

Run:  blender -b --python art/scripts/s03_build.py
Then: blender -b art/blender/s03_weigh.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s03

Re-runnable. Destructive only to art/blender/s03_weigh.blend, which lib/safety backs up
before every save. Content: src/data/stations/s03.json. Grey box: everything is
m["grey"] / m["grey_dark"] except the masonry pier carried over from s02 (art-bible §0).

The set is the hub front as an open bay: two grey neighbours flanking a 4.8 m opening, a back
wall with the (blank) rate board, and the counter across the front. Riyaz stands on the
pavement; the attendant works behind the counter. The crate starts on the counter so the
whole drag stays above the blueprint line (y 660).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import geo  # noqa: E402
import kit  # noqa: E402
import people  # noqa: E402
import station  # noqa: E402
from mathutils import Vector  # noqa: E402

SCALE = Vector((0.20, 3.20, 1.32))        # platform top centre; the camera's focal point
COUNTER_TOP = 1.20
COUNTER = dict(x0=-1.20, x1=0.80, y0=2.75, y1=3.55)
CRATE = Vector((-0.65, 3.20, COUNTER_TOP))  # base centre, on the counter's left half
CRATE_SIZE = (0.55, 0.36, 0.30)
RIYAZ_AT = (-1.60, 1.40, 0.0)             # on the pavement, in front of the counter's left end
ATTENDANT_AT = (0.55, 4.15, 0.0)          # behind the counter, in front of the back wall
BAY = (-2.40, 2.40)                       # the open front, between the neighbouring units
TARGET = tuple(SCALE)


def hub(st):
    """The hub front: neighbours, an open bay, a back wall and the market's masonry pier."""
    m, col, s = st.m, st.set, st.street
    for name, x0, x1 in (("HUB_block_L", -6.0, BAY[0]), ("HUB_block_R", BAY[1], 8.0)):
        geo.box(name, (x0, s.wall_y, 0), (x1, 6.0, 7.4), m["grey"], col, geo.BEVEL_ARCH)
    geo.box("HUB_upper", (BAY[0], 4.70, 4.20), (BAY[1], 6.0, 7.4), m["grey"], col, geo.BEVEL_ARCH)
    geo.box("HUB_back_wall", (BAY[0], 4.55, 0), (BAY[1], 4.70, 4.22), m["grey_dark"], col, 0.01)
    geo.box("HUB_back_wainscot", (BAY[0], 4.53, 0), (BAY[1], 4.55, 1.05), m["grey"], col, 0.008)
    geo.box("HUB_kerb_step", (BAY[0], 2.95, 0), (BAY[1], 3.05, 0.05), m["grey_dark"], col, 0.006)
    kit.pier(s, "HUB_pier_masonry", BAY[0], BAY[0] + 0.60, m["masonry"], col, proud=0.06, top=4.3)

    # The rate board: a blank panel. Its text is drawn by Phaser from s03.json params.
    geo.box("RATEBOARD_frame", (-1.25, 4.50, 1.95), (1.85, 4.55, 3.15), m["grey"], col, 0.01)
    geo.box("RATEBOARD_panel", (-1.20, 4.46, 2.00), (1.80, 4.50, 3.10), m["grey_dark"], col, 0.004)
    st.anchor("rate_board", (0.30, 4.46, 2.55))


def counter(st):
    """A 2 m counter, 1.2 m high: body, top slab, kick rail and the small terminal."""
    m, col = st.m, st.set
    x0, x1, y0, y1 = COUNTER["x0"], COUNTER["x1"], COUNTER["y0"], COUNTER["y1"]
    geo.box("COUNTER_body", (x0, y0, 0.05), (x1, y1, COUNTER_TOP - 0.04), m["grey_dark"], col, geo.BEVEL_PROP)
    geo.box("COUNTER_top", (x0 - 0.03, y0 - 0.03, COUNTER_TOP - 0.04), (x1 + 0.03, y1 + 0.03, COUNTER_TOP),
            m["grey"], col, 0.012)
    geo.box("COUNTER_kick", (x0 + 0.06, y0 - 0.01, 0.12), (x1 - 0.06, y0, 0.24), m["grey"], col, 0.006)
    for i, x in enumerate((x0 + 0.22, x1 - 0.22)):
        geo.cylinder(f"COUNTER_leg{i}", (x, y0 + 0.10, 0.0), 0.045, 0.05, m["grey_dark"], col, axis="Y", bevel=0)

    # The attendant's terminal: a low tablet on the counter's right, clear of the scale.
    geo.box("TERMINAL_base", (0.55, 3.36, COUNTER_TOP), (0.73, 3.50, COUNTER_TOP + 0.025), m["grey_dark"], col, 0.004)
    geo.box("TERMINAL_screen", (0.57, 3.38, COUNTER_TOP + 0.025), (0.71, 3.48, COUNTER_TOP + 0.035),
            m["grey"], col, 0.002)


def scale(st):
    """Platform scale, 0.6 x 0.6 m and 0.12 m high, on the counter top."""
    m, col = st.m, st.set
    x, y = SCALE.x, SCALE.y
    geo.box("SCALE_base", (x - 0.30, y - 0.30, COUNTER_TOP), (x + 0.30, y + 0.30, COUNTER_TOP + 0.06),
            m["grey_dark"], col, 0.008)
    geo.box("SCALE_platform", (x - 0.29, y - 0.29, COUNTER_TOP + 0.06), (x + 0.29, y + 0.29, SCALE.z),
            m["grey"], col, 0.01)
    geo.box("SCALE_lip", (x - 0.31, y - 0.31, SCALE.z - 0.015), (x + 0.31, y + 0.31, SCALE.z),
            m["grey"], col, 0.004)
    st.anchor("scale_pan", tuple(SCALE))


def crate(st):
    """PROP_crate, 0.55 x 0.36 x 0.30 m, with two darker slat bands so it reads as a crate."""
    m, col = st.m, st.prop("crate")
    w, d, h = CRATE_SIZE
    x, y, z = CRATE.x, CRATE.y, CRATE.z
    geo.box("CRATE_body", (x - w / 2, y - d / 2, z), (x + w / 2, y + d / 2, z + h), m["grey"], col, geo.BEVEL_PROP)
    for i, z0 in enumerate((0.06, 0.20)):
        geo.box(f"CRATE_slat{i}", (x - w / 2, y - d / 2 - 0.006, z + z0),
                (x + w / 2, y - d / 2, z + z0 + 0.035), m["grey_dark"], col, 0.004)
    geo.box("CRATE_lid", (x - w / 2 + 0.02, y - d / 2 + 0.02, z + h), (x + w / 2 - 0.02, y + d / 2 - 0.02, z + h + 0.018),
            m["grey_dark"], col, 0.006)
    st.anchor("crate_centre", (x, y, z + h / 2))
    st.anchor("crate_knot", (x, y, z + h + 0.02))
    st.anchor("crate_start", (x, y, z))


def attendant(st):
    """Grey hub attendant: idle, and the type pose used while the number is entered."""
    mats = people.costume_materials("attendant", shirt="#9A958E", cap=None)
    idle_r, idle_l = (0.26, -0.02, 0.90), (-0.26, -0.02, 0.90)
    type_r, type_l = (0.18, -0.30, 1.02), (-0.18, -0.30, 1.02)
    people.figure("ATTENDANT_idle", ATTENDANT_AT, 0, mats, idle_r, idle_l, st.char("attendant", "idle"))
    people.figure("ATTENDANT_type", ATTENDANT_AT, 0, mats, type_r, type_l, st.char("attendant", "type"))
    st.anchor("attendant_head", (ATTENDANT_AT[0], ATTENDANT_AT[1], 1.56))


def riyaz(st):
    """Riyaz waits in front of the counter. No cleaver, no phone (task 03)."""
    mats = people.costume_materials("riyaz03", apron="#D6CFC0", cap="#E6E2D8", wet_hands=True)
    people.figure("RIYAZ_idle", RIYAZ_AT, 0, mats, (0.26, -0.02, 0.90), (-0.26, -0.02, 0.90),
                  st.char("riyaz", "idle"))
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], 1.56))


def build():
    st = station.begin("s03")
    kit.plinth(st.street, st.m, st.set)
    hub(st)
    counter(st)
    scale(st)
    crate(st)
    attendant(st)
    riyaz(st)
    st.finish(TARGET)


if __name__ == "__main__":
    build()

"""Station 1 · The stall, Cockburn Road. Builds art/blender/s01_stall.blend from scratch.

Run:  blender -b --python art/scripts/s01_build.py
Then: blender -b art/blender/s01_stall.blend --python art/scripts/render_station.py
      python tools/pack_layers.py s01

Re-runnable. Destructive only to art/blender/s01_stall.blend, which lib/safety backs up to
art/blender/backups/ before every save. Sources per element: docs/art-bible.md §10.

This is the worked example for every station (docs/patterns.md): shared pieces come from
lib/kit.py and lib/people.py; only what is particular to this stall is written here.
Street slice: pavement y 0..3, wall at y 3.0, the shop opening centred on x = 0.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import geo  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import people  # noqa: E402
import rig  # noqa: E402
import station  # noqa: E402
from mathutils import Vector  # noqa: E402

TARGET = (0.0, 3.0, 1.0)                 # camera focal point: the counter in the doorway
OPEN_X = (-1.15, 1.15)                   # shop opening, 2.3 m (F04, estimated against a figure)
FLOOR_IN = 0.15                          # the shop floor is one step up (F04)
COUNTER_TOP = 1.0
COUNTER = dict(x0=-0.95, x1=0.85, y0=2.25, y1=2.85)
KILO_CENTRE = Vector((-0.5, 2.55, 1.12))
BLOCK = Vector((0.42, 2.6, COUNTER_TOP))
# The night beat's tray: between the kilo spot and the block, clear of both (kilo r ~0.20,
# block r 0.24, so the tray's right edge stops at x 0.17).
LEFTOVERS = Vector((-0.04, 2.40, COUNTER_TOP))
RIYAZ_AT = (0.55, 3.12, FLOOR_IN)        # in the doorway, so the awning never hides him (overhang rule)


def facade(st):
    s, m, col, d = st.street, st.m, st.set, st.data
    kit.pier(s, "FACADE_pier_L_end", s.x0, -4.3, m["cream"], col)
    kit.shutter_bay(s, "FACADE_bayL", -4.3, -2.1, m, col, kit.sign_material(d, "neighbour_left", m["board_faded_a"]))
    geo.box("FACADE_padlock", (-3.22, s.wall_y + 0.03, 0.08), (-3.14, s.wall_y + 0.08, 0.17), m["steel_dark"], col, 0.01)
    kit.pier(s, "FACADE_pier_L", -2.1, -1.6, m["cream"], col)
    kit.pier(s, "FACADE_pillar_orange", -1.6, OPEN_X[0], m["orange"], col, proud=0.05)          # R04
    kit.shop_opening(s, "FACADE_shop", *OPEN_X, m, col)                                          # R06
    kit.pier(s, "FACADE_pillar_cream", OPEN_X[1], 1.5, m["cream_yellow"], col, proud=0.03)       # R05
    kit.pier(s, "FACADE_pier_R", 1.5, 1.8, m["cream"], col)
    kit.shutter_bay(s, "FACADE_bayR", 1.8, 4.2, m, col, kit.sign_material(d, "neighbour_right", m["board_faded_b"]))
    kit.pier(s, "FACADE_pier_R_end", 4.2, s.x1, m["cream"], col)
    kit.upper_storey(s, m, col)
    kit.building_mass(s, m, col, rooms=[(OPEN_X[0] - 0.25, OPEN_X[1] + 0.25, 5.7, 3.05)])
    kit.facade_wires(s, m, col)
    kit.awning(s, "SHOP_awning", -1.7, 1.65, m, col)                                             # R01
    kit.fascia(s, d, "fascia", 0.0, 3.08, m, col)                                               # F04 layout
    kit.sticker(s, d, "upi_sticker", 1.32, 1.52, 0.03, col)                                      # F04, persona UPI
    kit.hung_meat(s, m, col)                                                                     # F04, X05


def shop_room(st, m):
    """The tiled room behind the opening: floor, walls, ceiling, rail and practical lights (R09)."""
    s, col = st.street, st.set
    x0, x1, back = *OPEN_X, 5.5
    geo.box("SHOP_floor", (x0, s.wall_y, 0), (x1, back, FLOOR_IN), m["floor"], col, 0.01)
    geo.box("SHOP_wall_L", (x0 - 0.25, s.wall_y + s.wall_t, 0), (x0, back, 3.0), m["tiles_in"], col, 0)
    geo.box("SHOP_wall_R", (x1, s.wall_y + s.wall_t, 0), (x1 + 0.25, back, 3.0), m["tiles_in"], col, 0)
    geo.box("SHOP_wall_back", (x0 - 0.25, back, 0), (x1 + 0.25, back + 0.2, 3.0), m["tiles_in"], col, 0)
    geo.box("SHOP_ceiling", (x0 - 0.25, s.wall_y, 2.95), (x1 + 0.25, back + 0.2, 3.05), m["ceiling"], col, 0)
    geo.cylinder("SHOP_rail", (x0, 4.3, 2.4), 0.02, x1 - x0, m["steel"], col, axis="X", bevel=0)
    practical = [                                   # mains-powered: off in --power-cut renders
        geo.cylinder("SHOP_tube", (x0 + 0.04, 3.7, 2.55), 0.02, 1.2, m["tube"], col, axis="Y", bevel=0),
        rig.point_light("LIGHT_tube", (x0 + 0.2, 4.3, 2.5), (0.95, 0.96, 0.91), 60, 0.3, col),
        geo.sphere("SHOP_bulb", (-0.2, 3.35, 2.28), 0.05, (1, 1, 1.25), m["bulb"], col),
        rig.point_light("LIGHT_bulb", (-0.2, 3.35, 2.2), (1.0, 0.79, 0.54), 30, 0.05, col),
    ]
    for o in practical:
        o["practical"] = True
    geo.cylinder("SHOP_bulb_cord", (-0.2, 3.35, 2.32), 0.004, 0.63, m["cable"], col, bevel=0)


def counter(st, m):
    """Cabinet counter straddling the doorway (F04): steel top, photo-menu board, the block."""
    col = st.set
    x0, x1, y0, y1 = COUNTER["x0"], COUNTER["x1"], COUNTER["y0"], COUNTER["y1"]
    geo.box("COUNTER_body", (x0, y0, 0.06), (x1, y1, COUNTER_TOP - 0.04), m["steel_dark"], col)
    geo.box("COUNTER_top", (x0 - 0.02, y0 - 0.02, COUNTER_TOP - 0.04), (x1 + 0.02, y1 + 0.02, COUNTER_TOP), m["steel"], col, 0.008)
    geo.box("COUNTER_board_frame", (x0 + 0.02, y0 - 0.01, 0.1), (x1 - 0.02, y0, COUNTER_TOP - 0.07), m["board_frame"], col, 0.004)
    geo.box("COUNTER_board", (x0 + 0.06, y0 - 0.016, 0.14), (x1 - 0.06, y0 - 0.008, COUNTER_TOP - 0.11), m["menu_board"], col, 0.003)
    for i, x in enumerate((x0 + 0.08, x1 - 0.08)):
        geo.cylinder(f"COUNTER_wheel{i}", (x, y0 + 0.1, 0.0), 0.045, 0.06, m["cable"], col, axis="Y", bevel=0)
    geo.cylinder("COUNTER_block", BLOCK, 0.24, 0.16, m["wood"], col)                 # R09, Five senses: the cleaver on the block
    for i, (x, y) in enumerate(((BLOCK.x + 0.08, BLOCK.y + 0.04), (BLOCK.x - 0.06, BLOCK.y - 0.06))):
        geo.sphere(f"COUNTER_cut{i}", (x, y, COUNTER_TOP + 0.19), 0.055, (1.2, 0.8, 0.45), m["meat"], col)


def cooler(st, m):
    """Upright glass-door cooler against the inner left wall. Form generic (no photo: art-bible §0).
    Its light is an FX layer, so the game can flicker it (deck p. 22: power cuts)."""
    col, glow_col = st.set, st.fx("fridge_glow")
    x0, x1, y0, y1, z0, z1 = OPEN_X[0] + 0.02, -0.55, 3.3, 3.85, FLOOR_IN, 1.95
    for name, lo, hi in (("back", (x0, y0, z0), (x0 + 0.06, y1, z1)), ("front", (x0, y0, z0), (x1, y0 + 0.05, z1)),
                         ("rear", (x0, y1 - 0.05, z0), (x1, y1, z1)), ("base", (x0, y0, z0), (x1, y1, z0 + 0.2)),
                         ("top", (x0, y0, z1 - 0.2), (x1, y1, z1))):
        geo.box(f"COOLER_body_{name}", lo, hi, m["cooler"], col)
    for i, z in enumerate((0.72, 1.12, 1.5)):
        geo.box(f"COOLER_shelf{i}", (x0 + 0.06, y0 + 0.05, z), (x1 - 0.04, y1 - 0.05, z + 0.015), m["steel"], col, 0.003)
        for k in range(3):
            yy = y0 + 0.1 + k * 0.15
            geo.box(f"COOLER_pack{i}{k}", (x0 + 0.12, yy, z + 0.015), (x0 + 0.34, yy + 0.11, z + 0.13),
                    m["packs_a"] if (i + k) % 2 else m["packs_b"], col, 0.01)
    for name, lo, hi in (("L", (x1 - 0.03, y0, z0 + 0.2), (x1, y0 + 0.05, z1 - 0.2)),
                         ("R", (x1 - 0.03, y1 - 0.05, z0 + 0.2), (x1, y1, z1 - 0.2)),
                         ("B", (x1 - 0.03, y0, z0 + 0.2), (x1, y1, z0 + 0.26)),
                         ("T", (x1 - 0.03, y0, z1 - 0.26), (x1, y1, z1 - 0.2))):
        geo.box(f"COOLER_door_frame_{name}", lo, hi, m["steel_dark"], col, 0.005)
    geo.box("COOLER_door_glass", (x1 - 0.025, y0 + 0.05, z0 + 0.26), (x1 + 0.002, y1 - 0.05, z1 - 0.26), m["glass"], col, 0.002)
    geo.panel("FRIDGE_glow", (x0 + 0.08, (y0 + y1) / 2, (z0 + z1) / 2), (y1 - y0 - 0.12, z1 - z0 - 0.45), "+X", m["glow"], glow_col)
    rig.point_light("LIGHT_fridge", (x0 + 0.25, (y0 + y1) / 2, 1.3), (0.87, 0.92, 0.94), 18, 0.2, glow_col)
    st.anchor("fridge", (x1, (y0 + y1) / 2 + 0.0, 1.3))


def riyaz(st):
    """Riyaz Q. (persona, deck p. 22): white cap, checked half-sleeves, apron, wet hands (p. 23).
    Three poses for the chop: idle, cleaver up, cleaver down."""
    mats = people.costume_materials("riyaz", apron="#D6CFC0", cap="#E6E2D8", wet_hands=True)
    left = people.local((BLOCK.x + 0.2, BLOCK.y + 0.02, COUNTER_TOP + 0.2), RIYAZ_AT)
    poses = {
        "idle": (BLOCK.x - 0.08, BLOCK.y + 0.06, COUNTER_TOP + 0.2),
        "up": (BLOCK.x - 0.1, BLOCK.y + 0.2, COUNTER_TOP + 0.62),
        "down": (BLOCK.x - 0.06, BLOCK.y + 0.02, COUNTER_TOP + 0.24),
    }
    for pose, right in poses.items():
        people.figure(f"RIYAZ_{pose}", RIYAZ_AT, 0, mats, people.local(right, RIYAZ_AT), left,
                      st.char("riyaz", pose), tool="cleaver")
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], FLOOR_IN + 1.7))


def leftovers(st, m):
    """The leftovers tray for the night beat (Run 1): unsold cut meat left on the counter,
    which spoils when the power goes out (deck pp. 22-23). Steel tray form per the kitchen
    racks and trays in F03; three cut pieces in the same meat material as the block. A PROP_
    collection, so the day beats simply never place the layer."""
    col = st.prop("leftovers")
    x, y, top = LEFTOVERS.x, LEFTOVERS.y, COUNTER_TOP
    w, d, h, t = 0.42, 0.28, 0.05, 0.012
    geo.box("LEFTOVERS_tray", (x - w / 2, y - d / 2, top), (x + w / 2, y + d / 2, top + 0.018),
            m["steel"], col, 0.008)
    for name, lo, hi in (
        ("front", (x - w / 2, y - d / 2, top + 0.012), (x + w / 2, y - d / 2 + t, top + h)),
        ("back", (x - w / 2, y + d / 2 - t, top + 0.012), (x + w / 2, y + d / 2, top + h)),
        ("left", (x - w / 2, y - d / 2, top + 0.012), (x - w / 2 + t, y + d / 2, top + h)),
        ("right", (x + w / 2 - t, y - d / 2, top + 0.012), (x + w / 2, y + d / 2, top + h)),
    ):
        geo.box(f"LEFTOVERS_rim_{name}", lo, hi, m["steel"], col, 0.005)
    for i, (dx, dy, rot) in enumerate(((-0.10, -0.02, 0.0), (0.0, 0.04, 0.4), (0.10, -0.02, -0.3))):
        geo.sphere(f"LEFTOVERS_piece{i}", (x + dx, y + dy, top + 0.05), 0.055, (1.3, 1.0, 0.5),
                   m["meat"], col, rot=(0, 0, rot))
    kit.shadow_catcher("LEFTOVERS_shadow_catcher", (x, y, top + 0.001), (w + 0.08, d + 0.08), m, col)
    st.anchor("leftovers_centre", (x, y, top + 0.1))


def build():
    st = station.begin("s01")
    m = st.m
    m.update(
        menu_board=M.menu_board("MAT_cabinet_board"),
        board_frame=M.matte("MAT_board_frame", "#2F7564", 0.6),
        glow=M.emissive("MAT_fridge_glow", "#DDEBF0", 3.5),
        cooler=M.steel("MAT_cooler_body", "#6F6A63", 0.5),
        packs_a=M.plastic("MAT_packs_a", "#B9886F"),
        packs_b=M.plastic("MAT_packs_b", "#C9C6BC"),
    )
    kit.plinth(st.street, m, st.set)
    facade(st)
    shop_room(st, m)
    counter(st, m)
    cooler(st, m)
    kit.chair("PROP_chair_navy", (1.95, 2.25, 0), m["chair_navy"], 200, st.props, monoblock=False)   # R08
    kit.chair("PROP_chair_cream", (2.65, 1.75, 0), m["chair_cream"], 160, st.props)
    kit.scooter(m, st.props, (-2.35, 1.35, 0))                                                       # F04

    kilo = st.prop("kilo")
    _, knot = kit.kilo_bag("KILO_bag", KILO_CENTRE, COUNTER_TOP, m, kilo)
    kit.shadow_catcher("KILO_shadow_catcher", (KILO_CENTRE.x + 0.1, (COUNTER["y0"] + COUNTER["y1"]) / 2, COUNTER_TOP + 0.001),
                       (1.1, COUNTER["y1"] - COUNTER["y0"]), m, kilo)
    leftovers(st, m)
    riyaz(st)

    st.anchor("kilo_knot", knot)
    st.anchor("kilo_centre", KILO_CENTRE)
    st.anchor("block", BLOCK + Vector((0, 0, 0.16)))
    st.anchor("exit", (4.0, 1.2, 0.0))
    st.finish(TARGET)


if __name__ == "__main__":
    build()

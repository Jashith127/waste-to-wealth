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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib"), str(HERE)]

import bpy  # noqa: E402

import geo  # noqa: E402
import goods  # noqa: E402
import kit  # noqa: E402
import materials as M  # noqa: E402
import people  # noqa: E402
import rig  # noqa: E402
import s03_art_build as s03  # noqa: E402  (Russell Market masonry, arches, posters, as at the hub)
import safety  # noqa: E402
import station  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

TARGET = (0.0, 3.0, 1.0)                 # camera focal point: the start of the walk
PLATE_W, PLATE_H = 3200, 1920             # the street plate: 1920x1080 start frame plus the pan
PLATE_TARGET = (6.0, 2.19, 1.0)           # plate centre; 640 px right and 420 px down of TARGET
PPM = 1920 / 11.0                         # keep the 11 m / 1920 px camera scale
RIYAZ_AT = (0.6, 1.3, 0.0)               # where the walk starts; every Riyaz frame is rendered here
HAND_R = (-0.32, 0.02, 0.6)               # local: the right arm hanging at his side, carrying the bag
REST = ((-0.3, 0.02, 0.6), (0.3, 0.02, 0.6))   # local: both arms hanging relaxed (a straight arm)
ANTHONY_AT = (3.0, 2.25, 0.0)
ARIF_AT = (7.0, 2.8, 0.0)
LITTER_AT = Vector((13.0, 1.95, 0.0))      # against the market's boundary wall (V05)
PILE_TOP = 0.42
CART_AT = Vector((9.2, 1.15, 0.0))        # the handcart that comes down the pavement (the mini-game)
PUSHER_BACK = 1.78                        # its pusher walks this far behind the cart's middle

# Riyaz and the passers-by move freely, so each is rendered on its own (no set in front of it) in
# every direction they walk, and Station02 places, flips and depth-sorts them. Headings face along
# the axes: e +X (on down the street), w -X, n +Y (toward the shops), s -Y (toward the road).
DIRS = {"e": 90, "w": 270, "n": 180, "s": 0}
WALK_FRAMES = 8                           # one walk cycle: right contact, down, passing, up, left contact...
PEDS = (                                  # name, look, lane start (x, y), the way they set off
    ("ped0", "office", (-2.2, 0.38), "e"),
    ("ped1", "chef", (5.4, 2.05), "e"),
    ("ped2", "office", (9.6, 0.38), "w"),
)

# Set pieces a walker can pass behind: each is also rendered alone as occ_<name> (cut by what is in
# front of it), so Station02 can draw it over a walker it hides. Object-name prefixes per piece.
OCCLUDERS = {
    "scooter": ("PROP_scooter",), "stove": ("STOVE_cart", "STOVE_lpg"),
    "crates": ("PROP_crate0", "PROP_crate1", "PROP_crate2"), "stall": ("STALL_",),
    "chair_a": ("PROP_chair_a",), "chair_b": ("PROP_chair_b",), "drum": ("PROP_drum", "PROP_crate3"),
    "pole": ("POLE",), "bollards": ("BOLLARD",), "tree": ("TREE",),
    **{f"kerb_a{i}": (f"BIKE_kerb_a_{i}",) for i in range(3)},
    **{f"kerb_b{i}": (f"BIKE_kerb_b_{i}",) for i in range(2)},
    **{f"auto{i}": (f"AUTO_{i}",) for i in range(3)},
}
NOT_OCCLUDERS = ("POLE_wire",)            # the wires run up to the facade: never in front of a walker

# Shopfront rhythm along 20 m: piers, then a bay between each pair.
PIERS = ((-5.0, -4.7), (-1.7, -1.4), (1.7, 2.0), (4.8, 5.1), (8.0, 8.3), (10.7, 11.0))
BAYS = ((-4.7, -1.7), (-1.4, 1.7), (2.0, 4.8), (5.1, 8.0), (8.3, 10.7))
OPEN_BAYS = (0, 2)                        # open shops with awnings and dark interiors


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
        sack_black=goods.bin_plastic("MAT_sack_black"),                    # garbage-bag film: near black, crinkled
        sack_grey=M.plastic("MAT_sack_grey", "#4A4E52", 0.25),
        sack_woven=goods.woven_pp("MAT_sack_woven"),                       # the white market sack (V05)
        sack_band=M.cloth("MAT_sack_band", "#3F6F8E", rough=0.55, weave=0.22, scale=220.0),
        sack_twine=goods.rope("MAT_sack_twine"),
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
            rooms.append((x0, x1, s.wall_y + 2.4, 3.0))
            shop_interior(st, i, x0, x1)
        elif i == 3:
            door_bay(st, x0, x1)
        else:
            kit.shutter_bay(s, f"FACADE_bay_{i}", x0, x1, m, col, m["sign_a"] if i == 1 else m["sign_b"])
    kit.upper_storey(s, m, col, windows=((-4.2, -2.6), (-1.2, 0.4), (1.6, 3.2), (4.4, 6.0), (7.2, 8.8)), ac_at=0.4)
    kit.building_mass(s, m, col, rooms=rooms)
    kit.facade_wires(s, m, col)


def shop_interior(st, i, x0, x1):
    """A shallow lit shop behind an open bay (R09): floor, back wall, shelves of muted goods."""
    s, m, col = st.street, st.m, st.set
    back = s.wall_y + 2.4
    geo.box(f"SHOP{i}_floor", (x0, s.wall_y, 0), (x1, back, 0.12), m["floor"], col, 0.01)
    geo.box(f"SHOP{i}_back", (x0, back, 0), (x1, back + 0.2, 3.0), m["tiles_in"], col, 0)
    geo.box(f"SHOP{i}_ceiling", (x0, s.wall_y, 2.95), (x1, back + 0.2, 3.05), m["ceiling"], col, 0)
    for k in range(3):
        z = 0.6 + k * 0.55
        geo.box(f"SHOP{i}_shelf{k}", (x0 + 0.2, back - 0.45, z), (x1 - 0.2, back - 0.05, z + 0.03), m["steel"], col, 0.004)
        for j in range(int((x1 - x0 - 0.5) / 0.32)):
            xx = x0 + 0.3 + j * 0.32
            tint = ("#9A7B5C", "#B6A88C", "#7E8A6A", "#A8685C")[(i + j + k) % 4]
            geo.box(f"SHOP{i}_goods{k}_{j}", (xx, back - 0.4, z + 0.03), (xx + 0.24, back - 0.12, z + 0.3),
                    M.plastic(f"MAT_goods_{(i + j + k) % 4}", tint, 0.6), col, 0.01)
    light = rig.point_light(f"LIGHT_shop{i}", ((x0 + x1) / 2, s.wall_y + 1.0, 2.6), (1.0, 0.85, 0.65), 45, 0.2, col)
    light["practical"] = True


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
    """What fills the walk (F01-F04): a parked scooter, red crates and a blue drum by the shutters,
    a pushcart with a tarp, plastic chairs, Anthony's stall, a leaning pole with its wires."""
    s, m, col = st.street, st.m, st.props
    kit.scooter(m, col, (-3.0, 1.15, 0), heading=-15)
    for i, (x, y, z, r) in enumerate(((1.0, 2.55, 0, 0), (1.02, 2.55, 0.3, 8), (1.5, 2.6, 0, -6), (9.2, 2.5, 0, 12))):
        kit.ph(f"PROP_crate{i}", "plastic_crate_01", (x, y, z), r, 1.0, col)                       # F03, R13
    geo.cylinder("PROP_drum", (9.2, 2.65, 0), 0.28, 0.85, m["drum"], col)                       # F03 blue drum
    kit.ph("PROP_chair_a", "plastic_monobloc_chair_01", (4.3, 2.15, 0), 200, 1.0, col)            # R08
    kit.ph("PROP_chair_b", "plastic_monobloc_chair_01", (8.0, 2.2, 0), 150, 1.0, col)     # clear of the handcart's lane

    # Anthony's stall: a steel counter with crates of produce (F05 density, muted)
    geo.box("STALL_counter", (2.45, 2.5, 0), (3.85, 2.95, 0.88), m["steel_dark"], col, 0.02)
    geo.box("STALL_top", (2.42, 2.46, 0.88), (3.88, 2.98, 0.94), m["steel"], col, 0.01)
    for k, x in enumerate((2.6, 3.05, 3.5)):
        geo.box(f"STALL_tray{k}", (x - 0.18, 2.55, 0.94), (x + 0.18, 2.88, 1.02), m["crate_dusty"], col, 0.01)
        for j in range(5):
            geo.sphere(f"STALL_fruit{k}_{j}", (x - 0.12 + j * 0.06, 2.7 + (j % 2) * 0.06, 1.05), 0.04, (1, 1, 1),
                       M.plastic(f"MAT_fruit{k}", ("#A8823F", "#8E5A3C", "#9A8F4E")[k], 0.5), col)
    # the leaning lamp pole with its transformer (R19, V03), with wires up to the facade
    kit.lamp_pole("POLE", 10.85, 0.35, m, col, height=7.2, transformer=True)
    for i, z in enumerate((6.4, 6.6)):
        kit.wire(f"POLE_wire{i}", (11.1, 0.3, z), (4.0, s.wall_y - 0.1, 4.75 + i * 0.08), 0.3, m["cable"], col)


def dress(st):
    """The Shivajinagar kit along the walk (V01-V05): two-wheelers nose-in along the shops, autos at
    the kerb, projecting flex boards and a banner, a stove cart, a tarp heap, pedestrians; at the
    market end the pink-over-stone boundary wall, the rain tree, bollards and pavement vendors."""
    s, m, col = st.street, st.m, st.props
    kit.two_wheeler_row("BIKE_a", -4.4, -3.6, 2.0, m, col, step=0.8, heading=180)          # a few nose-in at the shops
    # (no nose-in row by the drum: the handcart comes down that stretch)
    kit.two_wheeler_row("BIKE_kerb_a", -4.2, 0.4, -0.6, m, col, step=2.1, heading=90, z=kit.ROAD_Z)   # the rest along the kerb
    kit.two_wheeler_row("BIKE_kerb_b", 10.2, 12.4, -0.6, m, col, step=2.1, heading=90, z=kit.ROAD_Z)
    for i, (x, y) in enumerate(((2.6, -1.2), (6.4, -1.25), (8.9, -2.3))):        # autos on the road (V02, V03)
        kit.autorickshaw(f"AUTO_{i}", (x, y, kit.ROAD_Z), 0, m, col)
    for i, (x, z, mat) in enumerate(((-1.55, 3.35, "flex_red"), (1.85, 3.45, "flex_yellow"), (4.95, 3.3, "flex_blue"), (8.15, 3.45, "flex_red"))):
        kit.flex_board(f"FLEX_{i}", x, z, 1.1, s, m, m[mat], col)
    kit.banner("BANNER_0", 0.4, 4.6, 6.6, 0.9, s, m["flex_yellow"], col)
    kit.banner("BANNER_1", 6.2, 4.5, 6.2, 0.8, s, m["flex_blue"], col)
    kit.stove_cart("STOVE_cart", (-0.6, 1.75, 0), m, col)
    kit.ph("STOVE_lpg", "small_lpg_tank", (-1.45, 1.75, 0), 0, 1.0, col)
    kit.ph("MANHOLE", "water_manhole_cover", (8.2, 1.6, 0.002), 0, 1.0, col)
    kit.tarp_heap("TARP_heap", (-4.2, 2.55, 0), m, col)
    # (the pedestrians walk: see peds())
    # the market end (V05): boundary wall, pink plaster over a stone base, under a rain tree
    geo.box("BWALL_base", (11.45, 2.55, 0), (15.0, 2.8, 0.7), m["stone_base"], col, 0.02)
    geo.box("BWALL", (11.45, 2.57, 0.7), (15.0, 2.78, 2.3), m["pink_wall"], col, 0.02)
    geo.box("BWALL_coping", (11.4, 2.52, 2.3), (15.0, 2.83, 2.4), m["stone_base"], col, 0.02)
    kit.rain_tree("TREE", 14.3, 1.6, m, col)
    kit.bollards("BOLLARD", (11.6, 12.4, 13.9, 14.6), 0.95, m, col)
    # (the pavement vendors of V05 stay out of the pile's corner: it reads better uncrowded)


def cart(st):
    """PROP_cart: a loaded thela, the wooden handcart of the wholesale lanes (F01 shows its steel
    cousin), pushed down the pavement toward Riyaz mid-walk: he steps aside to let it pass. Tomato
    crates, onion net sacks, striped watermelons, bananas, taped cartons, a rice sack and a tarp, all
    lashed down (lib/goods.py). It travels -X, so it is built handles-first along +X (the way a thela
    is pushed), on its own layer, rendered alone so Station02 can roll it anywhere. Its pusher is CHAR_loader."""
    m, col = st.m, st.prop("cart")
    col["free"] = True
    c = CART_AT
    mats = goods.materials()
    root = geo.empty("CART", (0, 0, 0), col)
    before = set(col.objects)
    goods.thela("CART", (0.0, 0.0, 0.0), mats, col, m["tarp"], handle_rise=0.2)
    for o in set(col.objects) - before:
        if o.parent is None:
            o.parent = root
    root.location = c
    root.rotation_euler = (0, 0, math.pi)              # handles toward +X: the pusher walks behind it, going -X
    kit.shadow_catcher("CART_shadow_catcher", (c.x + 0.3, c.y, 0.003), (3.2, 1.6), m, col)
    st.anchor("cart_centre", (c.x, c.y, 0.9))
    st.anchor("cart_shadow_extent", (c.x + 1.7, c.y - 0.8, 0.0))     # pack_layers: keep the long shadow whole

    # the pusher, his hands on the grips (the bar is 1.47 m behind the middle, grips 0.29 m either side)
    at = (c.x + PUSHER_BACK, c.y, 0.0)
    mats_p = people.costume_materials("loader", look="worker")
    for i in range(WALK_FRAMES):
        g = people.gait(i / WALK_FRAMES, stride=0.16, lift=0.06, bob=0.02)
        g["pose"]["lean"] = 12.0                        # leaning into the load
        pc = st.char("loader", f"push{i}")
        pc["free"] = True
        people.figure(f"LOADER_push{i}", at, DIRS["w"], mats_p, (-0.3, -0.3, 0.82), (0.3, -0.3, 0.82), pc,
                      grip=("fist", "fist"), **g["pose"])
    st.world["chars"]["loader"] = at[:2]


def litter(st):
    """The Run 1 pile behind Russell Market: split sacks of bone and offal, a sack of rubbish,
    cardboard, a dry leaf, wet stains, two crows. It is a PROP so Run 2 can show the clean pavement."""
    m, col = st.m, st.prop("litter")
    c = LITTER_AT
    woven = dict(sack=m["sack_woven"], band=m["sack_band"], rope=m["sack_twine"], inside=m["stain"])
    # back row: two black bin bags and a tied woven sack against the wall; in front, the split woven sack
    # tipped over toward the street, its bone and offal spilling (below), and two knotted carry bags
    goods.bin_bag("LITTER_sack0", (c.x - 0.3, c.y + 0.4, 0), m["sack_black"], col, (0.6, 0.5, 0.56), rot=15, seed=1)
    goods.bin_bag("LITTER_sack1", (c.x + 0.3, c.y + 0.5, 0), m["sack_black"], col, (0.64, 0.52, 0.6), rot=-25, seed=2)
    goods.woven_sack("LITTER_sack2", (c.x - 0.95, c.y + 0.35, 0), woven, col, (0.5, 0.36, 0.68), rot=8, seed=3)
    _, mouth = goods.woven_sack("LITTER_sack3", (c.x - 0.35, c.y - 0.15, 0), woven, col, (0.48, 0.38, 0.62), rot=-60, tip=78, seed=4, split=True)
    for i, (dx, dy, k) in enumerate(((-0.8, -0.3, 1.0), (0.75, -0.35, 0.9)), start=4):
        root = geo.empty(f"LITTER_sack{i}_root", (c.x + dx, c.y + dy, 0), col)
        objs, _ = kit.kilo_bag(f"LITTER_sack{i}", (c.x + dx, c.y + dy, 0.12), 0.0, {"bag": m["bag_waste"]}, col)
        for o in objs:                               # scale about the bag's base, not the world origin
            o.parent = root
            o.matrix_parent_inverse = Matrix.Translation(-root.location)
        root.scale = (k, k, k)
    # the split sack spills bone and offal onto the paving
    # spilled from the split sack's mouth, fanning out onto the paving
    for i in range(8):
        a = -1.3 + i * 0.37
        dist = 0.12 + 0.07 * (i % 3)
        p0 = Vector((mouth.x + math.cos(a) * dist * 1.6 + 0.05 * (i % 2), mouth.y - 0.1 + math.sin(a) * dist, 0.018))
        d_ = Vector((math.cos(a * 2.3 + i), math.sin(a * 2.3 + i), 0)) * (0.07 + 0.02 * (i % 3))
        goods.bone(f"LITTER_bone{i}", p0, p0 + d_, m["bone"], col)
    for i in range(4):
        geo.sphere(f"LITTER_offal{i}", (mouth.x + 0.15 + i * 0.09, mouth.y - 0.22 - (i % 2) * 0.07, 0.025), 0.045,
                   (1.4, 1.0, 0.4), m["meat"], col, rot=(0, 0, i * 0.8))
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
        c = st.char("riyaz", pose)
        c["free"] = True
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
            kilo = st.prop("kilo")
            kilo["free"] = True
            _, bag_knot = kit.kilo_bag("KILO_bag", centre, centre.z - 0.13, bag_mat, kilo)
            st.anchor("kilo_knot", bag_knot)
            st.anchor("kilo_centre", centre)
    st.anchor("riyaz_hand", st.anchors["riyaz_hand_e"])
    st.anchor("riyaz_feet", RIYAZ_AT)
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], 1.75))
    st.world["chars"]["riyaz"] = RIYAZ_AT[:2]


def peds(st):
    """Passers-by (V03, V05) who walk their stretch of pavement and back: an eight-frame walk east and
    west each, rendered at their lane start and slid along by Station02."""
    for name, look, (x, y), _ in PEDS:
        mats = people.costume_materials(name, look=look)
        for d in ("e", "w"):
            for i in range(WALK_FRAMES):
                g = people.gait(i / WALK_FRAMES, stride=0.2, swing=0.13)
                c = st.char(name, f"walk_{d}{i}")
                c["free"] = True
                people.figure(f"{name.upper()}_walk_{d}{i}", (x, y, 0.0), DIRS[d], mats, g["right_hand"], g["left_hand"], c, **g["pose"])
        st.world["chars"][name] = (x, y)
    st.world["peds"] = [{"name": n, "lane": [x, y], "dir": d} for n, _, (x, y), d in PEDS]


# Stall-holder poses: right hand, left hand (local wrist targets), grips, head turn. "idle" casts the
# shadow in bg.png; Station02 cycles the rest (Anthony calls out and beckons, Arif folds his arms,
# adjusts his hat and waves when Riyaz passes).
ANTHONY_POSES = {
    "idle": ((-0.3, 0.0, 0.6), (0.3, 0.0, 0.6), ("loose", "loose"), 0),
    "call": ((-0.07, -0.16, 1.22), (0.3, 0.0, 0.6), ("loose", "loose"), 10),
    "beckon_a": ((-0.32, -0.42, 1.04), (0.3, 0.0, 0.6), ("flat", "loose"), 15),
    "beckon_b": ((-0.26, -0.3, 0.98), (0.3, 0.0, 0.6), ("loose", "loose"), 15),
    "show": ((-0.3, 0.0, 0.6), (0.42, 0.08, 0.98), ("loose", "flat"), -25),
    "look_l": ((-0.3, 0.0, 0.6), (0.3, 0.0, 0.6), ("loose", "loose"), 30),
    "look_r": ((-0.3, 0.0, 0.6), (0.3, 0.0, 0.6), ("loose", "loose"), -30),
}
ARIF_POSES = {
    "idle": ((-0.3, 0.0, 0.6), (0.3, 0.0, 0.6), ("loose", "loose"), 0),
    "fold": ((0.13, -0.17, 0.96), (-0.13, -0.19, 0.93), ("loose", "loose"), 0),
    "fold_look": ((0.13, -0.17, 0.96), (-0.13, -0.19, 0.93), ("loose", "loose"), 28),
    "hat": ((-0.12, -0.21, 1.29), (0.3, 0.0, 0.6), ("loose", "loose"), -8),     # fingers to the brim
    "wave_a": ((-0.34, -0.16, 1.32), (0.3, 0.0, 0.6), ("flat", "loose"), 25),
    "wave_b": ((-0.44, -0.08, 1.26), (0.3, 0.0, 0.6), ("flat", "loose"), 25),
    "hips": ((-0.3, 0.02, 0.8), (0.3, 0.02, 0.8), ("fist", "fist"), -15),
}


def stakeholders(st):
    """Anthony at his stall and Arif in his doorway (task 11), each in a few poses Station02 animates."""
    for name, origin, heading, poses, anchor in (("anthony", ANTHONY_AT, 10, ANTHONY_POSES, "anthony_head"),
                                                 ("arif", ARIF_AT, -10, ARIF_POSES, "arif_head")):
        mats = people.costume_materials(name)
        for pose, (right, left, grip, turn) in poses.items():
            people.figure(f"{name.upper()}_{pose}", origin, heading, mats, right, left, st.char(name, pose),
                          grip=grip, head_turn=turn)
        st.anchor(anchor, (origin[0], origin[1], 1.75))
        st.world["chars"][name] = origin[:2]


def footprint(objs, below=0.5):
    """World XY box of what stands on the ground: mesh bounds whose bottom is below `below` m (a tree's
    trunk, not its canopy)."""
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


def occluders(st):
    """Tag each occluding set piece's objects ["occ"] = name (render_station renders occ_<name>), and
    record every footprint Station02 sorts and collides by."""
    props = bpy.data.collections["PROPS"]
    for name, prefixes in OCCLUDERS.items():
        objs = [o for o in props.all_objects
                if o.name.startswith(prefixes) and not o.name.startswith(NOT_OCCLUDERS)]
        for o in objs:
            o["occ"] = name
        fp = footprint(objs)
        if fp:
            st.world["occ"][name] = fp
        else:
            print(f"[warn] occluder {name}: nothing found")
    litter = [o for o in bpy.data.collections["PROP_litter"].all_objects       # (near the pile: the rat import
              if not o.get("shadow_catcher") and abs(o.matrix_world.translation.x - LITTER_AT.x) < 2.5]   # carries a stray part)
    st.world["litter"] = footprint(litter)
    cart = [o for o in bpy.data.collections["PROP_cart"].all_objects if not o.get("shadow_catcher")]
    st.world["cart"] = footprint(cart, below=1.0)
    # four reference points: Station02 turns world metres into plate pixels with them
    for k, p in (("o", (0, 0, 0)), ("x", (1, 0, 0)), ("y", (0, 1, 0)), ("z", (0, 0, 1))):
        st.anchor(f"proj_{k}", p)


def build():
    st = station.begin("s02")
    st.world = {"occ": {}, "chars": {}}
    materials(st.m)
    before = set(st.set.objects)
    kit.plinth(st.street, st.m, st.set)
    kit.road(st.street, st.m, st.set)
    for o in set(st.set.objects) - before:
        o["ground"] = True                        # free figures keep the ground's bounce light (render_station)
    facade(st)
    market_corner(st)
    kit.kit_materials(st.m)
    street_props(st)
    dress(st)
    cart(st)
    litter(st)
    riyaz(st)
    peds(st)
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

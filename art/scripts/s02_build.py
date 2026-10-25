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
import math
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
from mathutils import Vector  # noqa: E402

TARGET = (0.0, 3.0, 1.0)                 # camera focal point: the start of the walk
PLATE_W, PLATE_H = 3200, 1920             # the street plate: 1920x1080 start frame plus the pan
PLATE_TARGET = (6.0, 2.19, 1.0)           # plate centre; 640 px right and 420 px down of TARGET
PPM = 1920 / 11.0                         # keep the 11 m / 1920 px camera scale
RIYAZ_AT = (0.2, 2.75, 0.0)              # on the pavement, near the shopfronts, walking +X
HEADING = 90                              # facing along the street
HAND_R = (-0.3, 0.02, 0.74)               # local: the right arm down at his side, carrying the bag
ANTHONY_AT = (3.0, 2.25, 0.0)
ARIF_AT = (7.0, 2.8, 0.0)
LITTER_AT = Vector((13.0, 1.95, 0.0))      # against the market's boundary wall (V05)
PILE_TOP = 0.42
CART_AT = Vector((6.1, 2.25, 0.0))        # the handcart that crosses the walk (the mini-game)

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
        sack_black=M.plastic("MAT_sack_black", "#2E2B2A", 0.35),
        sack_grey=M.plastic("MAT_sack_grey", "#6E6A65", 0.45),
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
    kit.ph("PROP_barrel", "Barrel_01", (9.75, 2.55, 0), 0, 1.0, col)                              # F03 drum
    kit.ph("PROP_chair_a", "plastic_monobloc_chair_01", (4.3, 1.9, 0), 200, 1.0, col)            # R08
    kit.ph("PROP_chair_b", "plastic_monobloc_chair_01", (8.9, 1.6, 0), 150, 1.0, col)
    kit.ph("PROP_bin", "metal_trash_can", (10.4, 2.6, 0), 0, 1.0, col)
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
    kit.two_wheeler_row("BIKE_a", -4.4, -1.9, 2.15, m, col)
    kit.two_wheeler_row("BIKE_b", 5.3, 7.9, 2.2, m, col)
    for i, (x, h) in enumerate(((6.9, 0), (9.8, 0))):                         # an auto rank at the kerb (V02)
        kit.autorickshaw(f"AUTO_{i}", (x, 0.75, 0), h, m, col)
    for i, (x, z, mat) in enumerate(((-1.55, 3.35, "flex_red"), (1.85, 3.45, "flex_yellow"), (4.95, 3.3, "flex_blue"), (8.15, 3.45, "flex_red"))):
        kit.flex_board(f"FLEX_{i}", x, z, 1.1, s, m, m[mat], col)
    kit.banner("BANNER_0", 0.4, 4.6, 6.6, 0.9, s, m["flex_yellow"], col)
    kit.banner("BANNER_1", 6.2, 4.5, 6.2, 0.8, s, m["flex_blue"], col)
    kit.stove_cart("STOVE_cart", (-0.6, 1.75, 0), m, col)
    kit.ph("STOVE_lpg", "small_lpg_tank", (-0.2, 1.4, 0), 0, 1.0, col)
    kit.ph("MANHOLE", "water_manhole_cover", (8.2, 1.6, 0.002), 0, 1.0, col)
    kit.tarp_heap("TARP_heap", (-4.2, 2.55, 0), m, col)
    for i, (x, y, h, k, stride) in enumerate(((-2.6, 1.3, 80, 0, 0.15), (2.4, 1.15, -100, 1, -0.15), (6.6, 1.35, 95, 2, 0.12),
                                              (9.6, 1.6, -80, 0, 0.0), (13.0, 0.95, 180, 3, 0.0))):
        kit.pedestrian(f"PED_{i}", (x, y, 0), h, col, kind=k, stride=stride)
    # the market end (V05): boundary wall, pink plaster over a stone base, under a rain tree
    geo.box("BWALL_base", (11.45, 2.55, 0), (15.0, 2.8, 0.7), m["stone_base"], col, 0.02)
    geo.box("BWALL", (11.45, 2.57, 0.7), (15.0, 2.78, 2.3), m["pink_wall"], col, 0.02)
    geo.box("BWALL_coping", (11.4, 2.52, 2.3), (15.0, 2.83, 2.4), m["stone_base"], col, 0.02)
    kit.rain_tree("TREE", 14.3, 1.6, m, col)
    kit.bollards("BOLLARD", (11.6, 12.4, 13.9, 14.6), 0.95, m, col)
    for i, x in enumerate((14.5, 11.7)):
        geo.box(f"VENDOR_stand{i}", (x - 0.45, 1.15, 0), (x + 0.45, 1.75, 0.75), m["flex_red"], col, 0.01)
        kit.ph(f"VENDOR_basket{i}", "wicker_basket_01", (x - 0.2, 1.45, 0.75), 20 * i, 1.0, col)
        kit.ph(f"VENDOR_crate{i}", "wooden_crate_01", (x + 0.2, 1.45, 0.75), -15, 0.8, col)


def cart(st):
    """PROP_cart: a steel handcart with a blue tarp bundle (F01), which crosses the pavement
    mid-walk. Its own layer, so Station02 can roll it across."""
    m, col = st.m, st.prop("cart")
    c = CART_AT
    geo.box("CART_bed", (c.x - 0.75, c.y - 0.4, 0.55), (c.x + 0.75, c.y + 0.4, 0.62), m["cart_steel"], col, 0.01)
    for name, lo, hi in (("rail_f", (c.x - 0.75, c.y - 0.42, 0.62), (c.x + 0.75, c.y - 0.38, 0.75)),
                         ("rail_b", (c.x - 0.75, c.y + 0.38, 0.62), (c.x + 0.75, c.y + 0.42, 0.75))):
        geo.box(f"CART_{name}", lo, hi, m["cart_steel"], col, 0.005)
    for i, x in enumerate((c.x - 0.45, c.x + 0.45)):
        geo.cylinder(f"CART_wheel{i}", (x, c.y - 0.44, 0.28), 0.28, 0.06, m["tyre"], col, axis="Y", segments=28, bevel=0.01)
        geo.cylinder(f"CART_wheel{i}b", (x, c.y + 0.38, 0.28), 0.28, 0.06, m["tyre"], col, axis="Y", segments=28, bevel=0.01)
    geo.limb("CART_handle", (c.x - 0.75, c.y, 0.6), (c.x - 1.15, c.y, 0.95), 0.02, 0.02, m["cart_steel"], col)
    geo.box("CART_tarp", (c.x - 0.6, c.y - 0.32, 0.62), (c.x + 0.55, c.y + 0.32, 1.05), m["tarp"], col, 0, subsurf=2)
    kit.shadow_catcher("CART_shadow_catcher", (c.x, c.y, 0.003), (2.2, 1.4), m, col)
    st.anchor("cart_centre", (c.x, c.y, 0.6))


def litter(st):
    """The Run 1 pile behind Russell Market: split sacks of bone and offal, a sack of rubbish,
    cardboard, a dry leaf, wet stains, two crows. It is a PROP so Run 2 can show the clean pavement."""
    m, col = st.m, st.prop("litter")
    c = LITTER_AT
    sacks = ((-0.5, 0.05, "sack_white", 1.5), (0.05, -0.2, "sack_black", 1.6), (0.5, 0.1, "sack_grey", 1.4),
             (0.0, 0.35, "sack_white", 1.3), (-0.75, -0.3, "bag_waste", 1.0))
    for i, (dx, dy, mat, k) in enumerate(sacks):
        root = geo.empty(f"LITTER_sack{i}_root", (c.x + dx, c.y + dy, 0), col)
        objs, _ = kit.kilo_bag(f"LITTER_sack{i}", (c.x + dx, c.y + dy, 0.12), 0.0, {"bag": m[mat]}, col)
        for o in objs:
            geo.parent_keep(o, root)
        root.scale = (k, k, k)                    # sacks, not carry bags: scaled about their base
    # the split sack spills bone and offal onto the paving
    for i in range(7):
        a = i * 0.9
        geo.sphere(f"LITTER_bone{i}", (c.x - 0.2 + math.cos(a) * 0.35, c.y - 0.55 + math.sin(a) * 0.12, 0.03), 0.035,
                   (2.2, 0.8, 0.7), m["bone"], col, rot=(0, 0, a))
    for i in range(4):
        geo.sphere(f"LITTER_offal{i}", (c.x + 0.25 + i * 0.12, c.y - 0.45 - (i % 2) * 0.08, 0.03), 0.05, (1.3, 1.0, 0.45), m["meat"], col)
    for i, (model, dx, dy, r, k) in enumerate((("trashbag", 0.8, 0.25, 30, 1.2), ("trashbag", -0.95, 0.35, -40, 1.1),
                                                ("compost_bags", 0.35, 0.55, 10, 0.9), ("cement_bag", -0.3, -0.75, 70, 1.0),
                                                ("cardboard_box_01", 0.95, -0.35, 18, 1.0))):
        kit.ph(f"LITTER_{model}{i}", model, (c.x + dx, c.y + dy, 0), r, k, col)
    kit.ph("LITTER_rat", "street_rat", (c.x - 1.2, c.y - 0.8, 0), -60, 1.0, col)
    geo.box("LITTER_leaf", (c.x - 1.1, c.y - 0.1, 0.0), (c.x - 0.6, c.y + 0.25, 0.008), m["leaf"], col, 0)
    for i, (dx, dy, r) in enumerate(((0.0, -0.4, 0.75), (-0.9, 0.2, 0.4), (0.9, -0.6, 0.35))):
        p = geo.cylinder(f"LITTER_stain{i}", (c.x + dx, c.y + dy, 0.0), r, 0.004, m["stain"], col, segments=28, bevel=0)
        p.scale = (1.6, 0.9, 1.0)
    for i, (dx, dy, z, rot) in enumerate(((0.2, 0.0, 0.48, 30), (-0.95, -0.55, 0.0, -50))):
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
    """Riyaz walking along the street, the kilo in his right hand. Three walk frames (right foot
    ahead, passing, left foot ahead) with the free arm swinging against the legs; the bag is its
    own prop layer so Run 1 can leave it on the pile."""
    m = st.m
    mats = people.costume_materials("riyaz", apron="#D6CFC0", cap="#E6E2D8", wet_hands=True)
    mats["apron"] = s03.apron_worn("MAT_riyaz_apron_worn")
    frames = {"walk_a": (0.17, (0.24, -0.16, 0.86)), "walk": (0.0, (0.25, 0.0, 0.82)), "walk_b": (-0.17, (0.24, 0.15, 0.86))}
    for pose, (stride, left) in frames.items():
        people.figure(f"RIYAZ_{pose}", RIYAZ_AT, HEADING, mats, HAND_R, left, st.char("riyaz", pose),
                      grip=("fist", "loose"), stride=stride)
    hand = Vector(RIYAZ_AT) + Vector((-HAND_R[1], HAND_R[0], HAND_R[2]))      # local -> world for heading 90
    kilo = st.prop("kilo")
    centre = Vector((hand.x + 0.04, hand.y - 0.02, hand.z - 0.27))
    _, bag_knot = kit.kilo_bag("KILO_bag", centre, centre.z - 0.13, {"bag": m["bag_waste"]}, kilo)
    st.anchor("riyaz_hand", bag_knot)
    st.anchor("kilo_knot", bag_knot)
    st.anchor("kilo_centre", centre)
    st.anchor("riyaz_head", (RIYAZ_AT[0], RIYAZ_AT[1], 1.75))


def stakeholders(st):
    """Anthony at his stall and Arif in his doorway (task 11), in plain market clothes."""
    for name, origin, heading, shirt, anchor in (("anthony", ANTHONY_AT, 10, "#8C8477", "anthony_head"),
                                                 ("arif", ARIF_AT, -10, "#9AA0A4", "arif_head")):
        mats = people.costume_materials(name, shirt=shirt, cap=None)
        people.figure(f"{name.upper()}_idle", origin, heading, mats, (-0.26, -0.06, 0.88), (0.26, -0.06, 0.88),
                      st.char(name, "idle"), moustache=name == "arif")
        st.anchor(anchor, (origin[0], origin[1], 1.75))


def build():
    st = station.begin("s02")
    materials(st.m)
    kit.plinth(st.street, st.m, st.set)
    facade(st)
    market_corner(st)
    kit.kit_materials(st.m)
    street_props(st)
    dress(st)
    cart(st)
    litter(st)
    riyaz(st)
    stakeholders(st)

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

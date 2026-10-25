"""The Shivajinagar asset kit (art-bible §4, §6): street-slice pieces every station reuses.

Every function takes a `Street` (where the facade sits) and the material dict from
`materials()`. Units are metres; the street face of the ground-floor wall is at y = street.wall_y,
pavement in front (smaller y), buildings behind (larger y).
"""
import math
from dataclasses import dataclass

import bmesh
import bpy
from mathutils import Vector

import geo
import materials as M
from safety import REPO

SIGNS = REPO / "art" / "build" / "signs"


@dataclass
class Street:
    x0: float = -5.0          # plinth runs x0..x1 (10 m of frontage by default)
    x1: float = 5.0
    depth: float = 3.0        # pavement depth in front of the wall
    wall_y: float = 3.0       # street face of the ground-floor wall
    wall_t: float = 0.25
    chajja_z: float = 4.25    # sunshade; an overhang at H projecting p hides the wall down to H - 0.82p
    top_z: float = 7.4        # facades rise past the frame top (art-bible §1)


def materials():
    """The shared palette as materials (art-bible §3, §4). Stations add their own on top."""
    return dict(
        paving=M.paving("MAT_paving", wet_centre=(0.0, 2.4), wet_radius=1.5),
        kerb=M.matte("MAT_kerb", "#8C877F", 0.8),
        bedding=M.matte("MAT_bedding", "bedding", 0.95),
        soil=M.matte("MAT_soil", "soil", 1.0),
        section=M.matte("MAT_section", "#3A322D", 0.9),
        cream=M.plaster("MAT_plaster_cream", "env.cream", 0.3),
        cream_yellow=M.plaster("MAT_plaster_creamyellow", "#D8C27E", 0.25),
        orange=M.plaster("MAT_plaster_orange", "env.plaster", 0.45),
        upper=M.plaster("MAT_plaster_upper", "#CFC4AE", 0.4, floor_z=4.0),
        concrete=M.plaster("MAT_concrete_stained", "#B9B2A2", 0.2, floor_z=3.9),
        masonry=M.masonry("MAT_masonry_market"),
        shutter=M.shutter("MAT_shutter"),
        shutter_box=M.steel("MAT_shutter_box", "#596470", 0.5),
        steel=M.steel("MAT_steel"),
        steel_dark=M.steel("MAT_steel_dark", "#5E5952", 0.45),
        window_frame=M.matte("MAT_window_frame", "env.door-green", 0.6, 0.3),
        window_glass=M.matte("MAT_window_glass", "#2A2E33", 0.15),
        tiles_in=M.tiles("MAT_tiles_interior", "tile-white", "tile-white", 0.2, checker=False),
        tiles_checker=M.tiles("MAT_tiles_checker", "tile-white", "env.tile-blue", 0.15),
        floor=M.floor_wet("MAT_floor_wet"),
        ceiling=M.matte("MAT_ceiling", "#B8AE9C", 0.9),
        awning=M.fabric_stripes("MAT_awning"),
        tarp=M.plastic("MAT_tarp", "#4F7FA3", 0.5),
        board_faded_a=M.plastic("MAT_board_faded_a", "#C9C0AC", 0.7),
        board_faded_b=M.plastic("MAT_board_faded_b", "#8C9A8E", 0.7),
        wood=M.wood_block("MAT_block"),
        meat=M.meat("MAT_meat"),
        goat=M.carcass("MAT_carcass_goat", lean="#B86A60", deep="#7E3530", fat="#E3D2BE", fat_amount=0.55),
        side=M.carcass("MAT_carcass_side", lean="#8E3A30", deep="#5C2420", fat="#D8B47E", fat_amount=0.45),
        bulb=M.emissive("MAT_bulb", "#FFC98A", 12.0),
        tube=M.emissive("MAT_tube", "#F2F5E8", 9.0),
        glass=M.glass("MAT_glass"),
        ac=M.plastic("MAT_ac_unit", "#CFCBBF", 0.6),
        cable=M.matte("MAT_cable", "env.charcoal", 0.5),
        chair_navy=M.plastic("MAT_chair_navy", "env.plastic-navy"),
        chair_cream=M.plastic("MAT_chair_cream", "#D9CFB8"),
        crate_dusty=M.plastic("MAT_crate_dusty", "#9C3E37"),
        drum=M.plastic("MAT_drum", "#2C3549"),
        scooter=M.plastic("MAT_scooter_body", "#7B8790", 0.35),
        seat=M.matte("MAT_scooter_seat", "#2A2624", 0.6),
        bag=M.bag_plastic("MAT_bag"),
        catcher=M.matte("MAT_catcher", "#808080", 0.8),
        grey=M.matte("MAT_greybox", "#9A958E", 0.8),          # grey-box blockouts only
        grey_dark=M.matte("MAT_greybox_dark", "#6E6A65", 0.8),
    )


# ---------------------------------------------------------------- ground
def plinth(st, m, col):
    """Street-slice floor with the 25 cm cut edge (art-bible §6.1) and a kerb."""
    back = st.wall_y + 3.0
    geo.box("PLINTH_paving", (st.x0, 0, -0.06), (st.x1, back, 0), m["paving"], col, geo.BEVEL_ARCH)
    geo.box("PLINTH_bedding", (st.x0, 0, -0.12), (st.x1, back, -0.06), m["bedding"], col, 0)
    geo.box("PLINTH_soil", (st.x0, 0, -0.25), (st.x1, back, -0.12), m["soil"], col, 0)
    geo.box("PLINTH_kerb", (st.x0, 0, 0), (st.x1, 0.15, 0.04), m["kerb"], col)


# ---------------------------------------------------------------- facade
def pier(st, name, x0, x1, mat, col, proud=0.0, top=None):
    geo.box(name, (x0, st.wall_y - proud, 0), (x1, st.wall_y + st.wall_t, top or st.chajja_z), mat, col, geo.BEVEL_ARCH)


def shutter_bay(st, name, x0, x1, m, col, board_mat):
    """A closed shop: rolling shutter, its housing, lintel and signboard."""
    w = st.wall_y
    geo.box(f"{name}_shutter", (x0, w + 0.08, 0), (x1, w + 0.12, 2.6), m["shutter"], col, 0.005)
    geo.box(f"{name}_housing", (x0, w, 2.6), (x1, w + 0.2, 2.85), m["shutter_box"], col)
    geo.box(f"{name}_lintel", (x0, w, 2.85), (x1, w + st.wall_t, st.chajja_z), m["cream"], col, geo.BEVEL_ARCH)
    geo.box(f"{name}_board", (x0 + 0.05, w - 0.06, 3.1), (x1 - 0.05, w, 3.85), board_mat, col)


def shop_opening(st, name, x0, x1, m, col, top=2.6):
    """An open shop front: lintel above, rolled-up shutter housing inside the top of the opening."""
    w = st.wall_y
    geo.box(f"{name}_lintel", (x0, w, top), (x1, w + st.wall_t, st.chajja_z), m["cream"], col, geo.BEVEL_ARCH)
    geo.box(f"{name}_housing", (x0, w + 0.02, top - 0.27), (x1, w + 0.22, top), m["shutter"], col)


def upper_storey(st, m, col, windows=((-4.2, -2.6), (-1.1, 0.7), (1.9, 3.7)), ac_at=-0.95):
    """Sunshade (chajja), the upper wall, a ledge, windows with mullions and an AC unit (F02, F04)."""
    w, cz = st.wall_y, st.chajja_z
    geo.box("FACADE_chajja", (st.x0, w - 0.4, cz - 0.1), (st.x1, w + st.wall_t, cz), m["concrete"], col, geo.BEVEL_ARCH)
    geo.box("FACADE_upper", (st.x0, w, cz), (st.x1, w + st.wall_t, st.top_z), m["upper"], col, geo.BEVEL_ARCH)
    geo.box("FACADE_ledge_upper", (st.x0, w - 0.25, cz + 2.3), (st.x1, w + st.wall_t, cz + 2.38), m["concrete"], col)
    wz0, wz1 = cz + 0.55, cz + 2.05
    for i, (x0, x1) in enumerate(windows):
        geo.box(f"FACADE_window{i}_frame", (x0, w - 0.04, wz0), (x1, w + 0.02, wz1), m["window_frame"], col)
        geo.box(f"FACADE_window{i}_glass", (x0 + 0.06, w - 0.05, wz0 + 0.06), (x1 - 0.06, w - 0.01, wz1 - 0.06), m["window_glass"], col, 0.004)
        for k in range(1, 3):
            xm = x0 + (x1 - x0) * k / 3
            geo.box(f"FACADE_window{i}_mullion{k}", (xm - 0.025, w - 0.07, wz0 + 0.06), (xm + 0.025, w - 0.03, wz1 - 0.06), m["window_frame"], col, 0.005)
    if ac_at is not None:
        geo.box("FACADE_ac_unit", (ac_at, w - 0.38, cz), (ac_at + 0.8, w - 0.06, cz + 0.55), m["ac"], col)
        geo.box("FACADE_ac_grille", (ac_at + 0.07, w - 0.385, cz + 0.08), (ac_at + 0.55, w - 0.37, cz + 0.47), m["shutter_box"], col, 0.004)


def building_mass(st, m, col, rooms=()):
    """Solid mass behind the facade so the cut end at +X reads as a section. `rooms` are
    (x0, x1, back, ceiling) voids left open for shop interiors."""
    w0, w1 = st.wall_y + st.wall_t, st.wall_y + 3.0
    xs = [st.x0]
    for x0, x1, _, _ in sorted(rooms):
        xs += [x0, x1]
    xs.append(st.x1)
    for i in range(0, len(xs), 2):
        geo.box(f"BUILDING_mass_{i // 2}", (xs[i], w0, 0), (xs[i + 1], w1, st.top_z), m["section"], col, 0)
    for k, (x0, x1, back, ceiling) in enumerate(rooms):
        geo.box(f"BUILDING_mass_back{k}", (x0, back, 0), (x1, w1, st.top_z), m["section"], col, 0)
        geo.box(f"BUILDING_mass_top{k}", (x0, w0, ceiling), (x1, back, st.top_z), m["section"], col, 0)


def wire(name, a, b, sag, mat, col, r=0.012, steps=24):
    """Overhead cable as a sagging curve (F02, R19)."""
    a, b = Vector(a), Vector(b)
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth, curve.bevel_resolution = r, 2
    spline = curve.splines.new("POLY")
    spline.points.add(steps)
    for i in range(steps + 1):
        t = i / steps
        p = a.lerp(b, t) - Vector((0, 0, sag * 4 * t * (1 - t)))
        spline.points[i].co = (*p, 1)
    obj = bpy.data.objects.new(name, curve)
    col.objects.link(obj)
    curve.materials.append(mat)
    return obj


def facade_wires(st, m, col, heights=((4.72, 0.0), (4.8, 0.14))):
    for i, (z, sag) in enumerate(heights):
        wire(f"FACADE_wire{i}", (st.x0, st.wall_y - 0.06, z), (st.x1, st.wall_y - 0.12, z), sag, m["cable"], col)


def awning(st, name, x0, x1, m, col, z_wall=3.02, depth=0.55, drop=0.28):
    """Striped awning with a scalloped hem (R01). Keep depth <= 0.6 m (the overhang rule)."""
    y_wall, y_front, z_front = st.wall_y - 0.02, st.wall_y - depth, z_wall - drop
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((x0, y_wall, z_wall), (x1, y_wall, z_wall), (x1, y_front, z_front), (x0, y_front, z_front))]
    bm.faces.new(v)
    geo.solid(name, bm, m["awning"], col, 0.02)
    bm = bmesh.new()
    pts = [(x0, z_front)]
    n = round((x1 - x0) / 0.2)
    w = (x1 - x0) / n
    for i in range(n):
        cx = x0 + w * (i + 0.5)
        for k in range(9):
            ang = math.pi + math.pi * k / 8
            pts.append((cx + math.cos(ang) * w / 2, z_front - 0.12 + math.sin(ang) * w / 2))
    pts.append((x1, z_front))
    bm.faces.new([bm.verts.new((x, y_front, z)) for x, z in pts])
    geo.solid(f"{name}_hem", bm, m["awning"], col, 0.015)
    geo.cylinder(f"{name}_rod", (x0, y_front, z_front), 0.018, x1 - x0, m["steel_dark"], col, axis="X", bevel=0)
    for x in (x0 + 0.05, (x0 + x1) / 2, x1 - 0.05):
        geo.limb(f"{name}_strut_{x:+.2f}", (x, y_wall, 2.55), (x, y_front, z_front), 0.012, 0.012, m["steel_dark"], col)
    return y_front, z_front


# ---------------------------------------------------------------- signs (text from src/data, art-bible §7)
def sign_material(station, sign_id, fallback, box_uv=True):
    """Material for a sign rendered by tools/render_signs.mjs, or `fallback` if not rendered yet."""
    png = SIGNS / f"{station['id']}-{sign_id}.png"
    sign = next(s for s in station["signs"] if s["id"] == sign_id)
    if not png.exists():
        print(f"[warn] {png.name} missing: run `node tools/render_signs.mjs`")
        return fallback
    return M.image(f"MAT_sign_{station['id']}_{sign_id}", png, box_uv=box_uv, flex=sign["style"].startswith("flex"))


def fascia(st, station, sign_id, x_centre, z0, m, col):
    """A shop's main sign on its steel backing, facing the street."""
    sign = next(s for s in station["signs"] if s["id"] == sign_id)
    w, h = sign["size_m"]
    mat = sign_material(station, sign_id, m["board_faded_a"], box_uv=False)
    geo.box(f"SIGN_{sign_id}_back", (x_centre - w / 2 - 0.02, st.wall_y - 0.07, z0 - 0.02),
            (x_centre + w / 2 + 0.02, st.wall_y, z0 + h + 0.02), m["steel_dark"], col)
    geo.panel(f"SIGN_{sign_id}", (x_centre, st.wall_y - 0.075, z0 + h / 2), (w, h), "-Y", mat, col)


def sticker(st, station, sign_id, x, z, proud, col):
    """Small sticker (e.g. the UPI QR) on a pillar face `proud` metres in front of the wall."""
    sign = next(s for s in station["signs"] if s["id"] == sign_id)
    png = SIGNS / f"{station['id']}-{sign_id}.png"
    if png.exists():
        geo.panel(f"SIGN_{sign_id}", (x, st.wall_y - proud - 0.006, z), tuple(sign["size_m"]), "-Y",
                  M.image(f"MAT_sign_{station['id']}_{sign_id}", png, 0.4), col)


# ---------------------------------------------------------------- street props
def chair(name, origin, mat, rot, col, monoblock=True):
    """Plastic chair (R08): moulded monoblock, or a thin metal-frame chair."""
    o = geo.empty(name, origin, col)
    leg_r = 0.045 if monoblock else 0.014
    parts = [
        geo.box(f"{name}_seat", (-0.23, -0.22, 0.39 if monoblock else 0.41), (0.23, 0.22, 0.46), mat, col, 0, subsurf=1 if monoblock else 0),
        geo.box(f"{name}_back", (-0.22, 0.17, 0.46), (0.22, 0.23, 0.88), mat, col, 0, subsurf=1 if monoblock else 0),
    ]
    for i, (x, y) in enumerate(((-0.19, -0.19), (0.19, -0.19), (-0.19, 0.19), (0.19, 0.19))):
        parts.append(geo.cylinder(f"{name}_leg{i}", (x, y, 0), leg_r, 0.43, mat, col, bevel=0, radius2=leg_r * (0.7 if monoblock else 1)))
    for p in parts:
        geo.parent_keep(p, o)
    o.rotation_euler = (0, 0, math.radians(rot))
    return o


def scooter(m, col, origin, heading=-20, name="PROP_scooter"):
    """Parked scooter after F04. Generic and unbranded. Built in local space, then placed."""
    o = geo.empty(name, (0, 0, 0), col)
    parts = []
    add = parts.append
    for i, y in enumerate((-0.62, 0.62)):
        add(geo.cylinder(f"{name}_tyre{i}", (-0.05, y, 0.2), 0.2, 0.1, m["cable"], col, axis="X", segments=32, bevel=0.025))
        add(geo.cylinder(f"{name}_hub{i}", (-0.06, y, 0.2), 0.11, 0.12, m["steel"], col, axis="X", bevel=0.01))
    body = m["scooter"]
    add(geo.box(f"{name}_floor", (-0.18, -0.36, 0.2), (0.18, 0.3, 0.32), body, col, 0.04))
    add(geo.box(f"{name}_rear", (-0.21, 0.08, 0.26), (0.21, 0.86, 0.7), body, col, 0.12))
    add(geo.box(f"{name}_seat", (-0.16, 0.14, 0.69), (0.16, 0.8, 0.8), m["seat"], col, 0.045))
    add(geo.box(f"{name}_apron", (-0.21, -0.56, 0.22), (0.21, -0.32, 1.0), body, col, 0.08))
    add(geo.box(f"{name}_mudguard", (-0.11, -0.84, 0.34), (0.11, -0.42, 0.5), body, col, 0.06))
    add(geo.box(f"{name}_head", (-0.15, -0.62, 1.0), (0.15, -0.38, 1.16), body, col, 0.05))
    add(geo.cylinder(f"{name}_bar", (-0.34, -0.5, 1.12), 0.022, 0.68, m["steel_dark"], col, axis="X", bevel=0))
    add(geo.box(f"{name}_lamp", (-0.06, -0.635, 1.04), (0.06, -0.6, 1.12), m["ac"], col, 0.01))
    for i, s in enumerate((-1, 1)):
        add(geo.cylinder(f"{name}_grip{i}", (s * 0.34 - (0.1 if s > 0 else 0), -0.5, 1.12), 0.03, 0.1, m["seat"], col, axis="X", bevel=0))
        add(geo.cylinder(f"{name}_mirror_arm{i}", (s * 0.22, -0.5, 1.12), 0.008, 0.2, m["steel_dark"], col, bevel=0))
        add(geo.sphere(f"{name}_mirror{i}", (s * 0.24, -0.5, 1.34), 0.05, (1, 0.35, 0.7), m["cable"], col))
    add(geo.cylinder(f"{name}_stand", (0.0, 0.1, 0.0), 0.015, 0.22, m["steel_dark"], col, bevel=0))
    for p in parts:
        p.parent = o
    o.location = origin
    o.rotation_euler = (0, 0, math.radians(heading))
    return o


def hung_meat(st, m, col, xa=-1.72, xb=-1.04, yb=2.62, zb=2.2):
    """Meat hung at a shop door (F04): a steel U-bracket off the wall, a whole skinned goat
    hung by the hind legs (X05/R26) and a large side with yellowed fat (F04/R03).
    The bracket runs xa..xb at height zb, yb in front of the wall."""
    for i, x in enumerate((xa, xb)):
        geo.limb(f"MEAT_bracket_arm{i}", (x, st.wall_y - 0.03, zb), (x, yb, zb), 0.016, 0.016, m["steel"], col)
    geo.limb("MEAT_bracket_bar", (xa, yb, zb), (xb, yb, zb), 0.018, 0.018, m["steel"], col)

    gx, hook = xa + 0.22, zb - 0.08
    for i, s_ in enumerate((-1, 1)):
        geo.limb(f"MEAT_hook_goat{i}", (gx + s_ * 0.05, yb, zb), (gx + s_ * 0.05, yb, hook), 0.006, 0.006, m["steel"], col)
        geo.limb(f"MEAT_goat_shank{i}", (gx + s_ * 0.05, yb, hook), (gx + s_ * 0.075, yb, hook - 0.24), 0.022, 0.05, m["goat"], col)
        geo.limb(f"MEAT_goat_thigh{i}", (gx + s_ * 0.072, yb, hook - 0.2), (gx + s_ * 0.05, yb + 0.005, hook - 0.52), 0.062, 0.092, m["goat"], col)
        geo.limb(f"MEAT_goat_foreleg{i}", (gx + s_ * 0.09, yb - 0.02, hook - 1.14), (gx + s_ * 0.21, yb - 0.07, hook - 1.38), 0.036, 0.02, m["goat"], col)
    body = [(0.34, 0.1, 0.06, 0), (0.44, 0.135, 0.08, 0), (0.56, 0.12, 0.075, 0.005), (0.68, 0.115, 0.075, 0.01),
            (0.82, 0.14, 0.085, 0.012), (0.96, 0.15, 0.09, 0.012), (1.08, 0.14, 0.085, 0.01), (1.18, 0.11, 0.075, 0),
            (1.26, 0.065, 0.055, -0.005), (1.32, 0.04, 0.04, -0.01)]
    geo.loft("MEAT_goat_body", [((gx, yb + dy, hook - dz), rx, ry) for dz, rx, ry, dy in body], m["goat"], col, noise=0.05, seed=3)

    sx = xb - 0.16
    geo.limb("MEAT_hook_side", (sx, yb, zb), (sx, yb, hook), 0.006, 0.006, m["steel"], col)
    geo.limb("MEAT_side_shank", (sx, yb, hook), (sx + 0.01, yb, hook - 0.26), 0.03, 0.065, m["side"], col)
    side = [(0.22, 0.01, 0.07, 0.045, 0), (0.32, 0.03, 0.16, 0.06, 0), (0.46, 0.04, 0.2, 0.065, 0.01), (0.62, 0.03, 0.19, 0.06, 0.01),
            (0.78, 0.01, 0.17, 0.055, 0), (0.94, -0.01, 0.15, 0.05, 0), (1.08, -0.03, 0.11, 0.045, 0), (1.17, -0.04, 0.05, 0.03, 0)]
    geo.loft("MEAT_side_body", [((sx + dx, yb + dy, hook - dz), rx, ry) for dz, dx, rx, ry, dy in side], m["side"], col, noise=0.12, seed=7)


def kilo_bag(name, centre, base_z, m, col):
    """The kilo: a knotted translucent white carry bag (F03, F05 sacks), 1.3x (art-bible §2).
    Returns (objects, knot_top). `base_z` is the surface it sits on."""
    c = Vector(centre)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=0.15)
    from mathutils import Matrix
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((1.15, 0.95, 0.72, 1)), verts=bm.verts)
    for v in bm.verts:
        v.co.z = max(v.co.z, base_z - c.z + 0.002)             # sits flat
        if v.co.z < 0:                                           # slumps wider at the base
            k = 1 + 0.18 * min(-v.co.z / 0.1, 1)
            v.co.x *= k
            v.co.y *= k
        if v.co.z > 0.05:                                        # gathered towards the knot
            k = min((v.co.z - 0.05) / 0.06, 1)
            v.co.x *= 1 - 0.7 * k
            v.co.y *= 1 - 0.7 * k
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    bag = bpy.data.objects.new(name, me)
    col.objects.link(bag)
    me.materials.append(m["bag"])
    for p in me.polygons:
        p.use_smooth = True
    tex = bpy.data.textures.get("TEX_bag_crinkle") or bpy.data.textures.new("TEX_bag_crinkle", "CLOUDS")
    tex.noise_scale = 0.03
    sub = bag.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    d = bag.modifiers.new("crinkle", "DISPLACE")
    d.texture, d.strength, d.mid_level = tex, 0.02, 0.5
    top = c.z + 0.11
    objs = [bag, geo.sphere(f"{name}_knot", (c.x, c.y, top), 0.03, (1.2, 1.0, 0.9), m["bag"], col)]
    for i, s_ in enumerate((-1, 1)):                             # the tied handles, flopping outwards
        objs.append(geo.sphere(f"{name}_ear{i}", (c.x + s_ * 0.05, c.y + 0.005, top + 0.045), 0.055,
                               (0.38, 0.16, 1.0), m["bag"], col, rot=(0.15, math.radians(-38 * s_), 0)))
    return objs, Vector((c.x, c.y, top + 0.1))


def shadow_catcher(name, centre, size, m, col):
    """Horizontal shadow-catcher panel for a prop's contact shadow (render_station.py finds it)."""
    obj = geo.panel(name, centre, size, "+Z", m["catcher"], col)
    obj["shadow_catcher"] = True
    return obj


# ---------------------------------------------------------------- the Shivajinagar kit (art bible §0: F01-F05, V01-V05)
def kit_materials(m):
    """Materials the street kit needs, added to a station's material dict once."""
    m.setdefault("auto_body", M.plastic("MAT_auto_body", "#5F7F45", 0.4))          # V02/V03: green, kept off mean.income
    m.setdefault("auto_top", M.plastic("MAT_auto_top", "#CDB55A", 0.5))            # pale yellow canopy, off mean.pay
    m.setdefault("auto_dark", M.matte("MAT_auto_dark", "#24211F", 0.6))
    m.setdefault("flex_red", M.plastic("MAT_flex_red", "#A8504A", 0.6))            # V04 boards, dusty (§3.3)
    m.setdefault("flex_yellow", M.plastic("MAT_flex_yellow", "#C9AE5E", 0.6))
    m.setdefault("flex_blue", M.plastic("MAT_flex_blue", "#4F6E8C", 0.6))
    m.setdefault("pink_wall", M.plaster("MAT_wall_pink", "#D49A86", 0.35))         # V05: the market's boundary wall
    m.setdefault("stone_base", M.plaster("MAT_stone_base", "#7E7A72", 0.2))
    m.setdefault("bark", M.matte("MAT_bark", "#5C4A3C", 0.9))
    m.setdefault("canopy", M.matte("MAT_canopy", "#4E5B3A", 0.85))
    m.setdefault("kurta", M.matte("MAT_kurta_white", "#E2DED4", 0.85))
    m.setdefault("cylinder_red", M.plastic("MAT_gas_cylinder", "#8E3E38", 0.4))
    return m


def autorickshaw(name, origin, heading, m, col):
    """Bengaluru auto (V02, V03): a green tub on three wheels under a pale-yellow canopy. Generic,
    no permit numbers or text (§7). Built in local space, facing +X, then placed."""
    root = geo.empty(name, (0, 0, 0), col)
    parts = [
        geo.box(f"{name}_tub", (-0.9, -0.62, 0.32), (0.75, 0.62, 0.95), m["auto_body"], col, 0.08),
        geo.box(f"{name}_nose", (0.75, -0.3, 0.3), (1.25, 0.3, 1.0), m["auto_body"], col, 0.1),
        geo.box(f"{name}_seat", (-0.75, -0.55, 0.95), (-0.2, 0.55, 1.05), m["auto_dark"], col, 0.03),
        geo.box(f"{name}_canopy", (-0.98, -0.68, 1.55), (0.92, 0.68, 1.78), m["auto_top"], col, 0, subsurf=2),
        geo.box(f"{name}_screen", (0.86, -0.42, 1.0), (0.9, 0.42, 1.55), m["window_glass"], col, 0.01),
        geo.box(f"{name}_back", (-0.97, -0.6, 0.95), (-0.9, 0.6, 1.62), m["auto_top"], col, 0.02),
    ]
    for x, y in ((-0.6, -0.66), (-0.6, 0.6), (0.65, -0.62), (0.65, 0.56)):
        parts.append(geo.limb(f"{name}_post{x}{y}", (x, y, 0.95), (x, y, 1.64), 0.018, 0.018, m["steel_dark"], col))
    for i, (x, y) in enumerate(((-0.55, -0.66), (-0.55, 0.6), (1.05, -0.03))):
        parts.append(geo.cylinder(f"{name}_wheel{i}", (x, y, 0.22), 0.22, 0.09, m["auto_dark"], col, axis="Y", segments=24, bevel=0.01))
    for p in parts:
        p.parent = root
    root.location = origin
    root.rotation_euler = (0, 0, math.radians(heading))
    return root


def two_wheeler_row(prefix, x0, x1, y, m, col, step=0.75, heading=-70):
    """Scooters and bikes nose-in along a shopfront (V01, V04), every `step` metres."""
    shades = ("#7B8790", "#8E3E38", "#3A4A5A", "#C9C6BC", "#2E2B2A")
    x, i = x0, 0
    while x <= x1:
        mat = m.setdefault(f"scooter_{i % 5}", M.plastic(f"MAT_scooter_{i % 5}", shades[i % 5], 0.35))
        scooter({**m, "scooter": mat}, col, (x, y, 0), heading=heading + (i % 3 - 1) * 6, name=f"{prefix}_{i}")
        x += step
        i += 1


def flex_board(name, x, z, h, st, m, mat, col, proud=0.7):
    """A flex board projecting from the facade on a steel frame (V04, F05), its face to the street's
    length so it reads from the camera: text-free colour blocks (the illegible-board rule, §7)."""
    y = st.wall_y
    geo.box(f"{name}_frame", (x - 0.03, y - proud, z - h / 2), (x + 0.03, y, z + h / 2), m["steel_dark"], col, 0.004)
    geo.box(f"{name}_board", (x + 0.03, y - proud + 0.03, z - h / 2 + 0.03), (x + 0.05, y - 0.03, z + h / 2 - 0.03), mat, col, 0.003)


def banner(name, x, z0, z1, w, st, mat, col):
    """A vertical banner hung flat on a facade (V04)."""
    geo.box(name, (x - w / 2, st.wall_y - 0.03, z0), (x + w / 2, st.wall_y - 0.01, z1), mat, col, 0)


def lamp_pole(name, x, y, m, col, height=7.0, lean=3.0, transformer=False):
    """A concrete pole with a long lamp arm and a wire bundle (V02, V03, R19); optionally a
    transformer box halfway up."""
    pole = geo.cylinder(name, (x, y, 0), 0.1, height, m["pole"] if "pole" in m else m["concrete"], col, bevel=0, radius2=0.07)
    pole.rotation_euler = (math.radians(-lean), math.radians(lean * 0.6), 0)
    geo.limb(f"{name}_arm", (x, y, height - 0.6), (x + 0.2, y + 1.2, height - 0.3), 0.03, 0.025, m["steel_dark"], col)
    geo.box(f"{name}_lamp", (x + 0.1, y + 1.1, height - 0.42), (x + 0.32, y + 1.4, height - 0.32), m["steel_dark"], col, 0.01)
    if transformer:
        geo.box(f"{name}_transformer", (x - 0.35, y - 0.25, 3.6), (x + 0.05, y + 0.25, 4.4), m["shutter_box"], col, 0.02)


def bollards(prefix, xs, y, m, col):
    for i, x in enumerate(xs):
        geo.cylinder(f"{prefix}_{i}", (x, y, 0), 0.06, 0.75, m["steel_dark"], col, bevel=0.01)
        geo.cylinder(f"{prefix}_{i}_band", (x, y, 0.55), 0.062, 0.06, m["flex_yellow"], col, bevel=0)


def stove_cart(name, origin, m, col):
    """A pavement food cart (V04, F01): steel box on wheels, a burner, a red gas cylinder below."""
    x, y, _ = origin
    geo.box(f"{name}_box", (x - 0.6, y - 0.35, 0.3), (x + 0.6, y + 0.35, 0.95), m["steel"], col, 0.01)
    geo.box(f"{name}_top", (x - 0.62, y - 0.37, 0.95), (x + 0.62, y + 0.37, 0.99), m["steel"], col, 0.006)
    geo.cylinder(f"{name}_kadai", (x + 0.2, y, 0.99), 0.2, 0.08, m["steel_dark"], col, radius2=0.26)
    geo.cylinder(f"{name}_cylinder", (x - 0.3, y, 0.0), 0.15, 0.55, m["cylinder_red"], col)
    for i, xx in enumerate((x - 0.45, x + 0.45)):
        geo.cylinder(f"{name}_wheel{i}", (xx, y - 0.38, 0.16), 0.16, 0.05, m["cable"], col, axis="Y", segments=20, bevel=0)


def tarp_heap(name, origin, m, col, size=(1.4, 1.0, 0.7)):
    """Something covered with a blue tarp against a wall (V01, R20)."""
    x, y, _ = origin
    geo.box(name, (x - size[0] / 2, y - size[1] / 2, 0), (x + size[0] / 2, y + size[1] / 2, size[2]), m["tarp"], col, 0, subsurf=2)


def rain_tree(name, x, y, m, col, height=6.5):
    """A big rain tree over the street (V05): a leaning trunk and a broad, flat canopy of lumps."""
    geo.limb(f"{name}_trunk", (x, y, 0), (x + 0.4, y - 0.3, height * 0.75), 0.32, 0.2, m["bark"], col)
    for i, (dx, dy) in enumerate(((1.3, 0.4), (-1.0, 0.6), (0.6, -1.2))):
        geo.limb(f"{name}_branch{i}", (x + 0.35, y - 0.25, height * 0.6), (x + 0.4 + dx, y - 0.3 + dy, height * 0.8), 0.14, 0.07, m["bark"], col)
    rnd = __import__("random").Random(len(name))
    for i in range(18):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0.3, 2.2)
        geo.sphere(f"{name}_crown{i}", (x + 0.4 + math.cos(a) * r, y - 0.3 + math.sin(a) * r * 0.8, height * 0.82 + rnd.uniform(-0.3, 0.5)),
                   rnd.uniform(0.55, 0.85), (1.3, 1.2, 0.6), m["canopy"], col, segments=12, rings=8)


def pedestrian(name, origin, heading, col, kind=0, stride=0.0):
    """A passer-by (V03, V05): white kurta and skullcap, or a shirt and trousers. Plain faces,
    no likenesses (§7)."""
    import people
    looks = (dict(shirt="#E2DED4", trousers="#D8D4CA", cap="#EAE6DC"), dict(shirt="#7E9AAE", trousers="#3A3633", cap=None),
             dict(shirt="#B9A07E", trousers="#2E2B2A", cap=None), dict(shirt="#8C5A50", trousers="#4A4440", cap=None))
    mats = people.costume_materials(f"ped{kind}", **looks[kind % len(looks)])
    swing = 0.12 if stride else 0.0
    return people.figure(name, origin, heading, mats, (-0.26, -swing, 0.86), (0.26, swing, 0.86), col,
                         moustache=kind % 2 == 0, stride=stride)


# ---------------------------------------------------------------- CC0 models (tools/fetch_polyhaven.py)
POLYHAVEN = REPO / "art" / "external" / "polyhaven"


def ph(name, model, loc, rot=0.0, scale=1.0, col=None):
    """Import a Poly Haven model (CC0, art/external/polyhaven/credits.json) by script, place it and
    file it in `col`. Returns its root empty, or None (with a warning) if it has not been fetched."""
    files = sorted((POLYHAVEN / model).glob("*.gltf"))
    if not files:
        print(f"[warn] {model} not fetched: run python tools/fetch_polyhaven.py")
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(files[0]))
    new = [o for o in bpy.data.objects if o not in before]
    root = geo.empty(name, (0, 0, 0), col)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        (col or bpy.context.scene.collection).objects.link(o)
        o.name = f"{name}_{o.name}"
        if o.parent is None:
            o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, math.radians(rot))
    root.scale = (scale, scale, scale)
    return root

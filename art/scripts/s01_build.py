"""Station 1, the stall on Cockburn Road: builds art/blender/s01_stall.blend from scratch.

Run:  blender -b --python art/scripts/s01_build.py
Re-runnable. Destructive only to art/blender/s01_stall.blend, which is backed up to
art/blender/backups/ before every save. Sources per element: docs/art-bible.md §10.

Layout: a street-slice diorama. Pavement y 0..3, shop wall at y 3.0..3.25, shop
opening centred on x = 0 (2.3 m wide). The camera is centred on CAMERA_TARGET.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import geo  # noqa: E402
import materials as M  # noqa: E402
import rig  # noqa: E402
import safety  # noqa: E402

REPO = safety.REPO
STATION = json.loads((REPO / "src/data/stations/s01.json").read_text(encoding="utf-8"))
BLEND = REPO / STATION["set"]["blend"]
SIGNS = REPO / "art/build/signs"

CAMERA_TARGET = (0.0, 3.0, 1.0)
WALL_Y = 3.0          # street face of the ground-floor wall
WALL_T = 0.25
FLOOR_IN = 0.15       # shop floor is one step up (F04)
OPEN_X = (-1.15, 1.15)
OPEN_TOP = 2.6
X_END = 5.0           # plinth runs x -5..5

COUNTER_TOP = 1.0
COUNTER = dict(x0=-0.95, x1=0.85, y0=2.25, y1=2.85)
KILO_CENTRE = Vector((-0.5, 2.55, 1.12))
BLOCK = Vector((0.42, 2.6, COUNTER_TOP))


def mats():
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
        shutter=M.shutter("MAT_shutter"),
        shutter_box=M.steel("MAT_shutter_box", "#596470", 0.5),
        steel=M.steel("MAT_steel"),
        steel_dark=M.steel("MAT_steel_dark", "#5E5952", 0.45),
        window_frame=M.matte("MAT_window_frame", "env.door-green", 0.6, 0.3),
        window_glass=M.matte("MAT_window_glass", "#2A2E33", 0.15),
        tiles_in=M.tiles("MAT_tiles_interior", "tile-white", "tile-white", 0.2, checker=False),
        floor=M.floor_wet("MAT_floor_wet"),
        ceiling=M.matte("MAT_ceiling", "#B8AE9C", 0.9),
        awning=M.fabric_stripes("MAT_awning"),
        board_faded_a=M.plastic("MAT_board_faded_a", "#C9C0AC", 0.7),
        board_faded_b=M.plastic("MAT_board_faded_b", "#8C9A8E", 0.7),
        cabinet_board=M.menu_board("MAT_cabinet_board"),
        board_frame=M.matte("MAT_board_frame", "#2F7564", 0.6),
        poster=M.matte("MAT_poster_aged", "#8F846F", 0.9),
        wood=M.wood_block("MAT_block"),
        meat=M.meat("MAT_meat"),
        fat=M.matte("MAT_fat", "#CDB49C", 0.55),
        bulb=M.emissive("MAT_bulb", "#FFC98A", 12.0),
        tube=M.emissive("MAT_tube", "#F2F5E8", 9.0),
        glow=M.emissive("MAT_fridge_glow", "#DDEBF0", 3.5),
        glass=M.glass("MAT_glass"),
        cooler=M.steel("MAT_cooler_body", "#6F6A63", 0.5),
        packs_a=M.plastic("MAT_packs_a", "#B9886F"),
        packs_b=M.plastic("MAT_packs_b", "#C9C6BC"),
        ac=M.plastic("MAT_ac_unit", "#CFCBBF", 0.6),
        cable=M.matte("MAT_cable", "env.charcoal", 0.5),
        chair_navy=M.plastic("MAT_chair_navy", "env.plastic-navy"),
        scooter=M.plastic("MAT_scooter_body", "#7B8790", 0.35),
        seat=M.matte("MAT_scooter_seat", "#2A2624", 0.6),
        chair_cream=M.plastic("MAT_chair_cream", "#D9CFB8"),
        bag=M.bag_plastic("MAT_bag"),
        shirt=M.checker_cloth("MAT_shirt_checked", "#4E6275", "#B9B3A3", 0.022),
        apron=M.matte("MAT_apron", "#D6CFC0", 0.85),
        trousers=M.matte("MAT_trousers", "#2E2B2A", 0.8),
        cap=M.matte("MAT_cap", "#E6E2D8", 0.85),
        skin=M.skin("MAT_skin", "#7A4E38"),
        skin_wet=M.skin("MAT_skin_wet", "#7A4E38", wet=True),
        eye=M.matte("MAT_eye", "#1F1A17", 0.5),
        catcher=M.matte("MAT_catcher", "#808080", 0.8),
    )


# ---------------------------------------------------------------- the street and plinth
def plinth(m, col):
    geo.box("PLINTH_paving", (-X_END, 0, -0.06), (X_END, 6, 0), m["paving"], col, geo.BEVEL_ARCH)
    geo.box("PLINTH_bedding", (-X_END, 0, -0.12), (X_END, 6, -0.06), m["bedding"], col, 0)
    geo.box("PLINTH_soil", (-X_END, 0, -0.25), (X_END, 6, -0.12), m["soil"], col, 0)
    geo.box("PLINTH_kerb", (-X_END, 0, 0), (X_END, 0.15, 0.04), m["kerb"], col)


# ---------------------------------------------------------------- facade
CHAJJA_Z = 4.25       # sunshade height; an overhang at H projecting p hides the wall down to H - 0.82p
UPPER_Z = 4.35


def bay_shutter(name, x0, x1, m, col, sign_mat):
    """A neighbour's shop: closed rolling shutter, its housing, lintel, faded board."""
    geo.box(f"{name}_shutter", (x0, WALL_Y + 0.08, 0), (x1, WALL_Y + 0.12, 2.6), m["shutter"], col, 0.005)
    geo.box(f"{name}_housing", (x0, WALL_Y + 0.0, 2.6), (x1, WALL_Y + 0.2, 2.85), m["shutter_box"], col)
    geo.box(f"{name}_lintel", (x0, WALL_Y, 2.85), (x1, WALL_Y + WALL_T, CHAJJA_Z), m["cream"], col, geo.BEVEL_ARCH)
    geo.box(f"{name}_board", (x0 + 0.05, WALL_Y - 0.06, 3.1), (x1 - 0.05, WALL_Y, 3.85), sign_mat, col)


def pier(name, x0, x1, mat, col, proud=0.0, top=CHAJJA_Z):
    geo.box(name, (x0, WALL_Y - proud, 0), (x1, WALL_Y + WALL_T, top), mat, col, geo.BEVEL_ARCH)


def sign_mat(m, sign_id, fallback):
    png = SIGNS / f"{STATION['id']}-{sign_id}.png"
    return M.image(f"MAT_sign_{sign_id}", png, box_uv=True) if png.exists() else fallback


def facade(m, col):
    pier("FACADE_pier_L_end", -X_END, -4.3, m["cream"], col)
    bay_shutter("FACADE_bayL", -4.3, -2.1, m, col, sign_mat(m, "neighbour_left", m["board_faded_a"]))
    geo.box("FACADE_padlock", (-3.22, WALL_Y + 0.03, 0.08), (-3.14, WALL_Y + 0.08, 0.17), m["steel_dark"], col, 0.01)
    pier("FACADE_pier_L", -2.1, -1.6, m["cream"], col)
    pier("FACADE_pillar_orange", -1.6, OPEN_X[0], m["orange"], col, proud=0.05)          # R04
    geo.box("FACADE_lintel_shop", (OPEN_X[0], WALL_Y, OPEN_TOP), (OPEN_X[1], WALL_Y + WALL_T, CHAJJA_Z), m["cream"], col, geo.BEVEL_ARCH)
    geo.box("FACADE_shop_housing", (OPEN_X[0], WALL_Y + 0.02, 2.33), (OPEN_X[1], WALL_Y + 0.22, OPEN_TOP), m["shutter"], col)  # R06
    pier("FACADE_pillar_cream", OPEN_X[1], 1.5, m["cream_yellow"], col, proud=0.03)       # R05
    pier("FACADE_pier_R", 1.5, 1.8, m["cream"], col)
    bay_shutter("FACADE_bayR", 1.8, 4.2, m, col, sign_mat(m, "neighbour_right", m["board_faded_b"]))
    pier("FACADE_pier_R_end", 4.2, X_END, m["cream"], col)
    # chajja (concrete sunshade) and the upper storey, after F02 / R18
    geo.box("FACADE_chajja", (-X_END, WALL_Y - 0.4, CHAJJA_Z - 0.1), (X_END, WALL_Y + WALL_T, CHAJJA_Z), m["concrete"], col, geo.BEVEL_ARCH)
    geo.box("FACADE_upper", (-X_END, WALL_Y, CHAJJA_Z), (X_END, WALL_Y + WALL_T, 7.4), m["upper"], col, geo.BEVEL_ARCH)
    geo.box("FACADE_ledge_upper", (-X_END, WALL_Y - 0.25, 6.55), (X_END, WALL_Y + WALL_T, 6.63), m["concrete"], col)
    wz0, wz1 = UPPER_Z + 0.45, UPPER_Z + 1.95
    for i, (x0, x1) in enumerate(((-4.2, -2.6), (-1.1, 0.7), (1.9, 3.7))):
        geo.box(f"FACADE_window{i}_frame", (x0, WALL_Y - 0.04, wz0), (x1, WALL_Y + 0.02, wz1), m["window_frame"], col)
        geo.box(f"FACADE_window{i}_glass", (x0 + 0.06, WALL_Y - 0.05, wz0 + 0.06), (x1 - 0.06, WALL_Y - 0.01, wz1 - 0.06), m["window_glass"], col, 0.004)
        for k in range(1, 3):  # mullions
            xm = x0 + (x1 - x0) * k / 3
            geo.box(f"FACADE_window{i}_mullion{k}", (xm - 0.025, WALL_Y - 0.07, wz0 + 0.06), (xm + 0.025, WALL_Y - 0.03, wz1 - 0.06), m["window_frame"], col, 0.005)
    # AC unit standing on the sunshade, louvred front, grime streak below (F02, F04)
    geo.box("FACADE_ac_unit", (-0.95, WALL_Y - 0.38, CHAJJA_Z), (-0.15, WALL_Y - 0.06, CHAJJA_Z + 0.55), m["ac"], col)
    geo.box("FACADE_ac_grille", (-0.88, WALL_Y - 0.385, CHAJJA_Z + 0.08), (-0.4, WALL_Y - 0.37, CHAJJA_Z + 0.47), m["shutter_box"], col, 0.004)
    # building mass behind the facade, with a void for the shop room (only its cut end at +X is seen)
    x0, x1, back = OPEN_X[0] - 0.25, OPEN_X[1] + 0.25, 5.7
    geo.box("BUILDING_mass_L", (-X_END, WALL_Y + WALL_T, 0), (x0, 6.0, 7.4), m["section"], col, 0)
    geo.box("BUILDING_mass_R", (x1, WALL_Y + WALL_T, 0), (X_END, 6.0, 7.4), m["section"], col, 0)
    geo.box("BUILDING_mass_back", (x0, back, 0), (x1, 6.0, 7.4), m["section"], col, 0)
    geo.box("BUILDING_mass_top", (x0, WALL_Y + WALL_T, 3.05), (x1, back, 7.4), m["section"], col, 0)
    # wires along the facade (F02 / R19)
    for i, (z, sag) in enumerate(((4.72, 0.0), (4.8, 0.14))):
        wire(f"FACADE_wire{i}", (-X_END, WALL_Y - 0.06, z), (X_END, WALL_Y - 0.12, z), sag, m["cable"], col)


def wire(name, a, b, sag, mat, col, r=0.012, steps=24):
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


# ---------------------------------------------------------------- the shop
def shop(m, col, practicals):
    x0, x1 = OPEN_X
    back = 5.5
    geo.box("SHOP_floor", (x0, WALL_Y, 0), (x1, back, FLOOR_IN), m["floor"], col, 0.01)
    geo.box("SHOP_wall_L", (x0 - 0.25, WALL_Y + WALL_T, 0), (x0, back, 3.0), m["tiles_in"], col, 0)
    geo.box("SHOP_wall_R", (x1, WALL_Y + WALL_T, 0), (x1 + 0.25, back, 3.0), m["tiles_in"], col, 0)
    geo.box("SHOP_wall_back", (x0 - 0.25, back, 0), (x1 + 0.25, back + 0.2, 3.0), m["tiles_in"], col, 0)
    geo.box("SHOP_ceiling", (x0 - 0.25, WALL_Y, 2.95), (x1 + 0.25, back + 0.2, 3.05), m["ceiling"], col, 0)
    geo.cylinder("SHOP_rail", (x0, 4.3, 2.4), 0.02, x1 - x0, m["steel"], col, axis="X", bevel=0)      # R09
    # tube light on the left wall, hanging bulb at the front (F04)
    geo.cylinder("SHOP_tube", (x0 + 0.04, 3.7, 2.55), 0.02, 1.2, m["tube"], col, axis="Y", bevel=0)
    practicals.append(rig.point_light("LIGHT_tube", (x0 + 0.2, 4.3, 2.5), (0.95, 0.96, 0.91), 60, 0.3, col))
    geo.cylinder("SHOP_bulb_cord", (-0.2, 3.35, 2.32), 0.004, 0.63, m["cable"], col, bevel=0)
    geo.sphere("SHOP_bulb", (-0.2, 3.35, 2.28), 0.05, (1, 1, 1.25), m["bulb"], col)
    practicals.append(rig.point_light("LIGHT_bulb", (-0.2, 3.35, 2.2), (1.0, 0.79, 0.54), 30, 0.05, col))
    # hung meat on a bar projecting from the orange pillar, under the awning (R03, R26)
    yb = 2.62
    _strut("SHOP_meat_bar_arm", (-1.38, WALL_Y - 0.05, 2.2), (-1.38, yb, 2.2), m["steel"], col, 0.015)
    geo.cylinder("SHOP_meat_bar", (-1.7, yb, 2.2), 0.015, 0.62, m["steel"], col, axis="X", bevel=0)
    for i, (x, length) in enumerate(((-1.56, 0.82), (-1.3, 0.7))):
        top = 2.1
        geo.cylinder(f"SHOP_hook{i}", (x, yb, top - 0.04), 0.006, 0.1, m["steel"], col, bevel=0)
        geo.sphere(f"SHOP_meat{i}", (x, yb, top - 0.05 - length / 2), 0.13,
                          (1.0, 0.42, length / 0.26), m["meat"], col)
        geo.sphere(f"SHOP_meat{i}_fat", (x - 0.06, yb - 0.02, top - 0.12 - length * 0.3), 0.06,
                         (0.7, 0.5, length * 0.45 / 0.12), m["fat"], col)



def awning(m, col):
    """Striped awning with a scalloped hem (R01). Slopes from the wall to the street."""
    xa, xb = -1.7, 1.65
    y_wall, z_wall, y_front, z_front = WALL_Y - 0.02, 3.02, 2.45, 2.74
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((xa, y_wall, z_wall), (xb, y_wall, z_wall), (xb, y_front, z_front), (xa, y_front, z_front))]
    bm.faces.new(v)
    _solid("SHOP_awning", bm, m["awning"], col, 0.02)
    # hem: scallops 0.2 m wide, 0.12 m drop + half-disc
    bm = bmesh.new()
    pts = [(xa, z_front)]
    n = round((xb - xa) / 0.2)
    w = (xb - xa) / n
    for i in range(n):
        cx = xa + w * (i + 0.5)
        for k in range(9):
            ang = math.pi + math.pi * k / 8
            pts.append((cx + math.cos(ang) * w / 2, z_front - 0.12 + math.sin(ang) * w / 2))
    pts.append((xb, z_front))
    verts = [bm.verts.new((x, y_front, z)) for x, z in pts]
    bm.faces.new(verts)
    _solid("SHOP_awning_hem", bm, m["awning"], col, 0.015)
    geo.cylinder("SHOP_awning_rod", (xa, y_front, z_front), 0.018, xb - xa, m["steel_dark"], col, axis="X", bevel=0)
    for x in (xa + 0.05, 0.0, xb - 0.05):
        _strut(f"SHOP_awning_strut_{x:+.2f}", (x, y_wall, 2.55), (x, y_front, z_front), m["steel_dark"], col)


def _solid(name, bm, mat, col, thickness):
    me = bpy.data.meshes.new(name)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x, loop.vert.co.z)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    col.objects.link(obj)
    me.materials.append(mat)
    s = obj.modifiers.new("solid", "SOLIDIFY")
    s.thickness, s.offset = thickness, 0
    return obj


def _strut(name, a, b, mat, col, r=0.012):
    a, b = Vector(a), Vector(b)
    obj = geo.cylinder(name, (0, 0, 0), r, (b - a).length, mat, col, bevel=0)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (b - a).to_track_quat("Z", "Y")
    obj.location = a
    return obj


def signboard(m, col):
    sign = STATION["signs"][0]
    w, h = sign["size_m"]
    png = SIGNS / f"{STATION['id']}-{sign['id']}.png"
    if png.exists():
        mat = M.image("MAT_sign_fascia", png)
    else:
        print(f"[warn] {png} missing: run `node tools/render_signs.mjs`; using a blank board")
        mat = m["board_faded_a"]
    z0 = 3.08
    geo.box("SIGN_fascia_back", (-w / 2 - 0.02, WALL_Y - 0.07, z0 - 0.02), (w / 2 + 0.02, WALL_Y, z0 + h + 0.02), m["steel_dark"], col)
    geo.panel("SIGN_fascia", (0, WALL_Y - 0.075, z0 + h / 2), (w, h), "-Y", mat, col)


def counter(m, col):
    """Cabinet counter straddling the opening (F04), steel top, tiled photo-board front."""
    x0, x1, y0, y1 = COUNTER["x0"], COUNTER["x1"], COUNTER["y0"], COUNTER["y1"]
    geo.box("COUNTER_body", (x0, y0, 0.06), (x1, y1, COUNTER_TOP - 0.04), m["steel_dark"], col)
    geo.box("COUNTER_top", (x0 - 0.02, y0 - 0.02, COUNTER_TOP - 0.04), (x1 + 0.02, y1 + 0.02, COUNTER_TOP), m["steel"], col, 0.008)
    geo.box("COUNTER_board_frame", (x0 + 0.02, y0 - 0.01, 0.1), (x1 - 0.02, y0, COUNTER_TOP - 0.07), m["board_frame"], col, 0.004)
    geo.box("COUNTER_board", (x0 + 0.06, y0 - 0.016, 0.14), (x1 - 0.06, y0 - 0.008, COUNTER_TOP - 0.11), m["cabinet_board"], col, 0.003)
    for i, x in enumerate((x0 + 0.08, x1 - 0.08)):
        geo.cylinder(f"COUNTER_wheel{i}", (x, y0 + 0.1, 0.0), 0.045, 0.06, m["cable"], col, axis="Y", bevel=0)
    geo.cylinder("COUNTER_block", BLOCK, 0.24, 0.16, m["wood"], col)                 # R09, Five senses
    for i, (x, y) in enumerate(((BLOCK.x + 0.08, BLOCK.y + 0.04), (BLOCK.x - 0.06, BLOCK.y - 0.06))):
        geo.sphere(f"COUNTER_cut{i}", (x, y, COUNTER_TOP + 0.19), 0.055, (1.2, 0.8, 0.45), m["meat"], col)


def cooler(m, col, glow_objs):
    """Upright glass-door cooler against the inner left wall. Form generic (no photo: art-bible §0 gaps)."""
    x0, x1, y0, y1, z0, z1 = OPEN_X[0] + 0.02, -0.55, 3.3, 3.85, FLOOR_IN, 1.95
    geo.box("COOLER_body_back", (x0, y0, z0), (x0 + 0.06, y1, z1), m["cooler"], col)
    geo.box("COOLER_body_front", (x0, y0, z0), (x1, y0 + 0.05, z1), m["cooler"], col)
    geo.box("COOLER_body_rear", (x0, y1 - 0.05, z0), (x1, y1, z1), m["cooler"], col)
    geo.box("COOLER_base", (x0, y0, z0), (x1, y1, z0 + 0.2), m["cooler"], col)
    geo.box("COOLER_top", (x0, y0, z1 - 0.2), (x1, y1, z1), m["cooler"], col)
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
    glow = geo.panel("FRIDGE_glow", (x0 + 0.08, (y0 + y1) / 2, (z0 + z1) / 2), (y1 - y0 - 0.12, z1 - z0 - 0.45), "+X", m["glow"], col)
    glow_objs.append(glow)
    glow_objs.append(rig.point_light("LIGHT_fridge", (x0 + 0.25, (y0 + y1) / 2, 1.3), (0.87, 0.92, 0.94), 18, 0.2, col))


def scooter(m, col, origin=(-2.35, 1.35, 0), heading=-20):
    """Parked scooter, after the one at the F04 shopfront. Generic, unbranded."""
    o = geo.empty("PROP_scooter", (0, 0, 0), col)
    parts = []
    add = parts.append
    for i, y in enumerate((-0.62, 0.62)):
        add(geo.cylinder(f"PROP_scooter_tyre{i}", (-0.05, y, 0.2), 0.2, 0.1, m["cable"], col, axis="X", segments=32, bevel=0.025))
        add(geo.cylinder(f"PROP_scooter_hub{i}", (-0.06, y, 0.2), 0.11, 0.12, m["steel"], col, axis="X", bevel=0.01))
    body = m["scooter"]
    add(geo.box("PROP_scooter_floor", (-0.18, -0.36, 0.2), (0.18, 0.3, 0.32), body, col, 0.04))
    add(geo.box("PROP_scooter_rear", (-0.21, 0.08, 0.26), (0.21, 0.86, 0.7), body, col, 0.12))
    add(geo.box("PROP_scooter_seat", (-0.16, 0.14, 0.69), (0.16, 0.8, 0.8), m["seat"], col, 0.045))
    add(geo.box("PROP_scooter_apron", (-0.21, -0.56, 0.22), (0.21, -0.32, 1.0), body, col, 0.08))
    add(geo.box("PROP_scooter_mudguard", (-0.11, -0.84, 0.34), (0.11, -0.42, 0.5), body, col, 0.06))
    add(geo.box("PROP_scooter_head", (-0.15, -0.62, 1.0), (0.15, -0.38, 1.16), body, col, 0.05))
    add(geo.cylinder("PROP_scooter_bar", (-0.34, -0.5, 1.12), 0.022, 0.68, m["steel_dark"], col, axis="X", bevel=0))
    add(geo.box("PROP_scooter_lamp", (-0.06, -0.635, 1.04), (0.06, -0.6, 1.12), m["ac"], col, 0.01))
    for i, s in enumerate((-1, 1)):
        add(geo.cylinder(f"PROP_scooter_grip{i}", (s * 0.34 - (0.1 if s > 0 else 0), -0.5, 1.12), 0.03, 0.1, m["seat"], col, axis="X", bevel=0))
        add(geo.cylinder(f"PROP_scooter_mirror_arm{i}", (s * 0.22, -0.5, 1.12), 0.008, 0.2, m["steel_dark"], col, bevel=0))
        add(geo.sphere(f"PROP_scooter_mirror{i}", (s * 0.24, -0.5, 1.34), 0.05, (1, 0.35, 0.7), m["cable"], col))
    add(geo.cylinder("PROP_scooter_stand", (0.0, 0.1, 0.0), 0.015, 0.22, m["steel_dark"], col, bevel=0))
    for p in parts:
        p.parent = o
    o.location = origin
    o.rotation_euler = (0, 0, math.radians(heading))


def chairs(m, col):
    def chair(name, origin, mat, rot, leg_r, monoblock):
        o = geo.empty(name, origin, col)
        parts = [
            geo.box(f"{name}_seat", (-0.23, -0.22, 0.39 if monoblock else 0.41), (0.23, 0.22, 0.46), mat, col, 0, subsurf=1 if monoblock else 0),
            geo.box(f"{name}_back", (-0.22, 0.17, 0.46), (0.22, 0.23, 0.88), mat, col, 0, subsurf=1 if monoblock else 0),
        ]
        for i, (x, y) in enumerate(((-0.19, -0.19), (0.19, -0.19), (-0.19, 0.19), (0.19, 0.19))):
            parts.append(geo.cylinder(f"{name}_leg{i}", (x, y, 0), leg_r, 0.43, mat, col, bevel=0, radius2=leg_r * (0.7 if monoblock else 1)))
        for p in parts:
            geo.parent_keep(p, o)
        o.rotation_euler = (0, 0, math.radians(rot))
    chair("PROP_chair_navy", (1.95, 2.25, 0), m["chair_navy"], 200, 0.014, False)     # R08
    chair("PROP_chair_cream", (2.65, 1.75, 0), m["chair_cream"], 160, 0.045, True)


# ---------------------------------------------------------------- the kilo
def kilo(m, col):
    """Knotted translucent white bag (F03, F05 sacks), 1.3x scale (art-bible §2)."""
    c = KILO_CENTRE
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=0.15)
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((1.15, 0.95, 0.72, 1)), verts=bm.verts)
    for v in bm.verts:
        v.co.z = max(v.co.z, COUNTER_TOP - c.z + 0.002)       # sits flat
        if v.co.z < 0:                                          # slumps wider at the base
            k = 1 + 0.18 * min(-v.co.z / 0.1, 1)
            v.co.x *= k
            v.co.y *= k
        if v.co.z > 0.05:                                       # gathered towards the knot
            k = min((v.co.z - 0.05) / 0.06, 1)
            v.co.x *= 1 - 0.7 * k
            v.co.y *= 1 - 0.7 * k
    bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    me = bpy.data.meshes.new("KILO_bag")
    bm.to_mesh(me)
    bm.free()
    bag = bpy.data.objects.new("KILO_bag", me)
    col.objects.link(bag)
    me.materials.append(m["bag"])
    for p in me.polygons:
        p.use_smooth = True
    tex = bpy.data.textures.new("TEX_bag_crinkle", "CLOUDS")
    tex.noise_scale = 0.03
    sub = bag.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    d = bag.modifiers.new("crinkle", "DISPLACE")
    d.texture, d.strength, d.mid_level = tex, 0.02, 0.5
    top = c.z + 0.11
    knot = geo.sphere("KILO_knot", (c.x, c.y, top), 0.03, (1.2, 1.0, 0.9), m["bag"], col)
    ears = []
    for i, s_ in enumerate((-1, 1)):                            # the tied handles, flopping outwards
        ears.append(geo.sphere(f"KILO_ear{i}", (c.x + s_ * 0.05, c.y + 0.005, top + 0.045), 0.055,
                               (0.38, 0.16, 1.0), m["bag"], col, rot=(0.15, math.radians(-38 * s_), 0)))
    catcher = geo.panel("KILO_shadow_catcher", (c.x + 0.1, (COUNTER["y0"] + COUNTER["y1"]) / 2, COUNTER_TOP + 0.001),
                        (1.1, COUNTER["y1"] - COUNTER["y0"]), "+Z", m["catcher"], col)
    return [bag, knot, *ears], catcher, Vector((c.x, c.y, top + 0.1))


# ---------------------------------------------------------------- Riyaz Q. (persona, deck p. 22)
RIYAZ = dict(x=0.55, y=3.12, floor=FLOOR_IN)


def limb(name, a, b, r, mat, col):
    return _strut(name, a, b, mat, col, r)


def arm_points(shoulder, hand, la=0.28, lb=0.27, bend=(0, 0.3, -1)):
    """Two-bone IK in the plane of (hand - shoulder) and `bend`: returns the elbow."""
    s, h = Vector(shoulder), Vector(hand)
    d = h - s
    dist = min(d.length, la + lb - 1e-3)
    a = (la * la - lb * lb + dist * dist) / (2 * dist)
    off = math.sqrt(max(la * la - a * a, 0))
    axis = d.normalized()
    bend_v = Vector(bend)
    perp = (bend_v - axis * bend_v.dot(axis)).normalized()
    return s + axis * a + perp * off


POSES = {
    # right hand (cleaver) target, left hand target
    "idle": ((BLOCK.x - 0.08, BLOCK.y + 0.06, COUNTER_TOP + 0.2), (BLOCK.x + 0.2, BLOCK.y + 0.02, COUNTER_TOP + 0.2)),
    "up":   ((BLOCK.x - 0.1, BLOCK.y + 0.2, COUNTER_TOP + 0.62), (BLOCK.x + 0.2, BLOCK.y + 0.02, COUNTER_TOP + 0.2)),
    "down": ((BLOCK.x - 0.06, BLOCK.y + 0.02, COUNTER_TOP + 0.24), (BLOCK.x + 0.2, BLOCK.y + 0.02, COUNTER_TOP + 0.2)),
}


def riyaz(m, col, pose="idle"):
    x, y, fz = RIYAZ["x"], RIYAZ["y"], RIYAZ["floor"]
    objs = []
    add = objs.append
    for i, dx in enumerate((-0.1, 0.1)):
        add(geo.cylinder(f"RIYAZ_leg{i}", (x + dx, y, fz), 0.08, 0.8, m["trousers"], col, bevel=0))
    add(geo.box("RIYAZ_torso", (x - 0.25, y - 0.15, fz + 0.78), (x + 0.25, y + 0.15, fz + 1.36), m["shirt"], col, 0, subsurf=2))
    add(geo.box("RIYAZ_apron", (x - 0.21, y - 0.175, fz + 0.45), (x + 0.21, y - 0.14, fz + 1.26), m["apron"], col, 0, subsurf=1))
    add(geo.cylinder("RIYAZ_neck", (x, y, fz + 1.3), 0.065, 0.14, m["skin"], col, bevel=0))
    hz = fz + 1.56
    add(geo.sphere("RIYAZ_head", (x, y, hz), 0.145, (0.95, 0.92, 1.05), m["skin"], col))
    add(geo.cylinder("RIYAZ_cap", (x, y, hz + 0.085), 0.13, 0.08, m["cap"], col, bevel=0.012))
    for i, s in enumerate((-1, 1)):
        add(geo.sphere(f"RIYAZ_eye{i}", (x + s * 0.05, y - 0.13, hz + 0.02), 0.016, (1, 0.6, 1.2), m["eye"], col))
        add(geo.sphere(f"RIYAZ_ear{i}", (x + s * 0.14, y, hz), 0.03, (0.5, 1, 1.2), m["skin"], col))
        add(geo.sphere(f"RIYAZ_brow{i}", (x + s * 0.05, y - 0.128, hz + 0.055), 0.022, (1.2, 0.4, 0.35), m["eye"], col))
    add(geo.sphere("RIYAZ_nose", (x, y - 0.145, hz - 0.01), 0.026, (0.8, 0.9, 1.1), m["skin"], col))
    add(geo.sphere("RIYAZ_moustache", (x, y - 0.138, hz - 0.055), 0.03, (1.6, 0.5, 0.4), m["eye"], col))
    # facing -Y, so his right side is -X
    right_hand, left_hand = POSES[pose]
    for side, sx, hand in (("R", -1, right_hand), ("L", 1, left_hand)):
        sh = Vector((x + sx * 0.25, y, fz + 1.26))
        el = arm_points(sh, hand, bend=(sx * 0.6, 0.4, -1))
        add(geo.sphere(f"RIYAZ_shoulder_{side}", sh, 0.085, (1, 1, 1), m["shirt"], col))
        add(limb(f"RIYAZ_upper_{side}", sh, el, 0.075, m["shirt"], col))
        add(geo.sphere(f"RIYAZ_elbow_{side}", el, 0.066, (1, 1, 1), m["skin_wet"], col))
        add(limb(f"RIYAZ_fore_{side}", el, hand, 0.064, m["skin_wet"], col))
        add(geo.sphere(f"RIYAZ_hand_{side}", hand, 0.08, (0.95, 1.1, 0.75), m["skin_wet"], col))   # 1.3x hands
        if side == "R":
            fwd = (Vector(hand) - el).normalized()
            blade = geo.box("RIYAZ_cleaver", (-0.003, -0.05, -0.09), (0.003, 0.05, 0.09), m["steel"], col, 0.002)
            blade.rotation_mode = "QUATERNION"
            blade.rotation_quaternion = fwd.to_track_quat("Z", "X")
            blade.location = Vector(hand) + fwd * 0.12
            add(blade)
    for o in objs:
        o["riyaz_pose"] = pose
    return objs


# ---------------------------------------------------------------- build
def build():
    safety.fresh_scene()
    scene = bpy.context.scene
    scene.name = "S01_stall"
    m = mats()
    set_col = geo.collection("SET")
    props_col = geo.collection("PROPS")
    kilo_col = geo.collection("KILO")
    glow_col = geo.collection("FRIDGE_GLOW")
    riyaz_root = geo.collection("RIYAZ")
    practicals = []
    glow_objs = []

    plinth(m, set_col)
    facade(m, set_col)
    shop(m, set_col, practicals)
    awning(m, set_col)
    signboard(m, set_col)
    counter(m, set_col)
    cooler(m, set_col, glow_objs)
    for o in glow_objs:
        set_col.objects.unlink(o)
        glow_col.objects.link(o)
    chairs(m, props_col)
    scooter(m, props_col)
    _, catcher, knot_top = kilo(m, kilo_col)

    for pose in POSES:
        pc = geo.collection(f"RIYAZ_{pose}", riyaz_root)
        riyaz(m, pc, pose)

    rig.camera(CAMERA_TARGET)
    rig.lights(STATION["set"]["lighting"])
    rig.render_settings()

    scene["anchors"] = json.dumps({
        "kilo_knot": rig.to_screen(knot_top, CAMERA_TARGET),
        "kilo_centre": rig.to_screen(KILO_CENTRE, CAMERA_TARGET),
        "block": rig.to_screen(BLOCK + Vector((0, 0, 0.16)), CAMERA_TARGET),
        "fridge": rig.to_screen((-0.55, 3.57, 1.3), CAMERA_TARGET),
        "riyaz_head": rig.to_screen((RIYAZ["x"], RIYAZ["y"], FLOOR_IN + 1.7), CAMERA_TARGET),
        "exit": rig.to_screen((4.0, 1.2, 0.0), CAMERA_TARGET),
    })
    catcher["role"] = "kilo_shadow"
    safety.save(BLEND)


if __name__ == "__main__":
    build()

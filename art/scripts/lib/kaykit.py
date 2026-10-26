"""Rigged people from a free template (KayKit "Character Pack: Adventurers" 2.0, CC0).

`tools/fetch_kaykit.py` fetches the pack. Every figure is the template's `Ranger` (a rigged,
low-poly man: 23 bones, ~9k verts), imported fresh, then
  * reproportioned (smaller head, a neck, longer legs) and scaled to 1.6 m (art-bible §2);
  * re-skinned: the template's palette atlas is replaced, cell by cell, by the procedural
    materials in materials.py (woven cloth, skin, hair, leather), so each person gets their own;
  * dressed: sleeves, trousers, apron, skullcap, turban and so on, skinned to the same rig;
  * posed: arms reach hand targets, legs stride, by aiming bones (two-bone IK).

Frame: local space, feet on the floor at the origin, facing -Y, so the right hand is at -X.
Template units are scaled by `S` (the armature's scale); `build` takes and returns metres.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import geo
import materials as M
import safety

GLB = (safety.ART / "external" / "kaykit" / "pack" / "KayKit_Adventurers_2.0_FREE" / "Characters" / "gltf" / "Ranger.glb")
HEIGHT = 1.6                  # art-bible §2: the adult figure, hair included

# Reproportioning, in template units (the template is 2.27 tall with a head 1.08 tall).
LEG_Z = 0.53                  # the legs end here
LEG_K = 1.40                  # legs stretched by this
HEAD_PIVOT = Vector((0, 0, 1.2))
HEAD_K = 0.50                 # head scaled by this
NECK = 0.08                   # gap the neck fills
HAND_K = 0.85                 # the template's mitts are already 1.3x a real hand (art-bible §2)

# The template's palette atlas is 8 x 4 cells; every polygon sits wholly in one cell.
CELL = dict(skin=(0, 0), hair=(1, 0), eye=(2, 0), metal=(3, 0), tunic=(5, 0), sleeve=(6, 0), belt=(7, 0),
            back=(0, 1), cuff=(1, 1), shorts=(7, 1), boot=(3, 2), hand=(7, 2))

# Who is who. hair/moustache/goatee are the face; head is the headgear; the rest is dress.
LOOKS = {
    "neutral": dict(hair="#2A2522", moustache=False, goatee=False, head=None, sleeves=None, legs="full", shoes="shoe", extras=()),
    # F04/X05 meat-seller type: white skullcap, checked half sleeves, bib apron, short grey beard.
    "butcher": dict(hair="#3A3430", moustache=True, goatee=True, head="skullcap", sleeves="half", legs="full", shoes="sandal", extras=("apron",)),
    "vendor": dict(hair="#2A2522", moustache=True, goatee=False, head="skullcap", sleeves="half", legs="full", shoes="sandal", extras=("apron",)),
    "attendant": dict(hair="#1E1A18", moustache=False, goatee=False, head=None, sleeves="half", legs="full", shoes="shoe", extras=("lanyard", "glasses", "pen")),
    "loader": dict(hair="#241E1B", moustache=True, goatee=False, head="wrap", sleeves=None, legs="rolled", shoes="sandal", extras=("towel",)),
    "worker": dict(hair="#2A2522", moustache=False, goatee=False, head="hardhat", sleeves="full", legs="full", shoes="gumboot", extras=("mask", "gloves")),
    "farmer": dict(hair="#B5B0A6", moustache=True, goatee=False, head="turban", sleeves="full", legs="dhoti", shoes="sandal", extras=("kurta",)),
}


def look_of(name):
    return dict(LOOKS[name])


def _warp_z(z):
    return z * LEG_K if z < LEG_Z else z + LEG_Z * (LEG_K - 1)


def _warp(p):
    return Vector((p[0], p[1], _warp_z(p[2])))


def _head_pt(p):
    """Template head-space point -> reproportioned template space."""
    p = Vector(p)
    return Vector((p.x * HEAD_K, p.y * HEAD_K, _warp_z(HEAD_PIVOT.z) + NECK + (p.z - HEAD_PIVOT.z) * HEAD_K))


def _cell(me, poly, uv):
    n = len(poly.loop_indices)
    u = sum(uv[l].uv.x for l in poly.loop_indices) / n
    v = sum(uv[l].uv.y for l in poly.loop_indices) / n
    return int(u * 8), int((1 - v) * 4)


def _is_head(o):
    return o.name.endswith("_Head")


def _import(col):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    return new


def _reproportion(arm, meshes):
    """Warp every mesh and bone: legs longer, head smaller, a neck. Done at rest, so the weights hold."""
    for o in meshes:
        head = _is_head(o)
        for v in o.data.vertices:
            v.co = _head_pt(v.co) if head else _warp(v.co)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    old = {b.name: (b.head.copy(), b.tail.copy()) for b in eb}
    for b in eb:
        b.use_connect = False
    for b in eb:
        f = _head_pt if b.name == "head" else _warp
        h, t = old[b.name]
        b.head, b.tail = f(h), f(t)
    bpy.ops.object.mode_set(mode="OBJECT")


def _ring(name, centre, radius, thick, mat, col):
    """A torus standing in the XZ plane (spectacle rims)."""
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=thick, major_segments=20, minor_segments=6,
                                     location=centre, rotation=(math.radians(90), 0, 0))
    o = bpy.context.active_object
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    o.name = name
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def _skin_to(obj, arm, bone):
    """Weight the whole object to one bone, so it bends with it. The armature modifier goes first."""
    vg = obj.vertex_groups.new(name=bone)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    mod = obj.modifiers.new("armature", "ARMATURE")
    mod.object = arm
    obj.modifiers.move(len(obj.modifiers) - 1, 0)
    obj.parent = arm


def _attach(obj, arm, bone=None):
    if bone:
        _skin_to(obj, arm, bone)
    else:
        obj.parent = arm
    return obj


def _front_y(body, z, x=0.0, half=0.12):
    ys = [v.co.y for v in body.data.vertices if abs(v.co.z - z) < 0.04 and abs(v.co.x - x) < half]
    return min(ys) if ys else -0.25


def _materials(o, cells, fallback):
    """Replace the template's one material by one per atlas cell, from `cells` {cell: material}."""
    o.data.materials.clear()
    uv = o.data.uv_layers.active.data
    slot = {}
    for p in o.data.polygons:
        c = _cell(o.data, p, uv)
        if c not in slot:
            o.data.materials.append(cells.get(c, fallback))
            slot[c] = len(slot)
        p.material_index = slot[c]
        p.use_smooth = True


def _delete_polys(o, keep):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.active
    kill = []
    for f in bm.faces:
        u = sum(l[uv].uv.x for l in f.loops) / len(f.loops)
        v = sum(l[uv].uv.y for l in f.loops) / len(f.loops)
        if not keep((int(u * 8), int((1 - v) * 4)), f.calc_center_median()):
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(o.data)
    bm.free()


def two_bone(root, target, la, lb, bend):
    """Joint position for a two-bone limb from `root` reaching `target`, bending toward `bend`."""
    s, h = Vector(root), Vector(target)
    d = h - s
    dist = max(min(d.length, la + lb - 1e-3), abs(la - lb) + 1e-3)
    a = (la * la - lb * lb + dist * dist) / (2 * dist)
    off = math.sqrt(max(la * la - a * a, 0))
    axis = d.normalized()
    b = Vector(bend)
    perp = b - axis * b.dot(axis)
    if perp.length < 1e-4:
        perp = Vector((0, -1, 0)) - axis * axis.y
    return s + axis * a + perp.normalized() * off


def _aim(pb, direction):
    """Turn a pose bone about its head so it points along `direction` (armature space)."""
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    m = (q.to_matrix() @ pb.matrix.to_3x3()).to_4x4()
    m.translation = pb.head
    pb.matrix = m
    bpy.context.view_layer.update()


def _bone(arm, name):
    b = arm.data.bones[name]
    return b.head_local.copy(), b.tail_local.copy()


def build(name, look, mats, origin, heading, right_hand, left_hand, col, floor=0.0, aim=None, stride=0.0,
          moustache=None):
    """Build one rigged, dressed, posed figure. Returns (root empty, info) where info has the
    right wrist and forearm direction in local metres (for a tool in the fist)."""
    spec = look_of(look)
    if moustache is not None:
        spec["moustache"] = moustache
    new = _import(col)
    arm = next(o for o in new if o.type == "ARMATURE")
    junk = [o for o in new if o.name.startswith("Icosphere") or o.name.endswith(("_Cape", "_Quiver"))]
    new = [o for o in new if o not in junk]
    for o in junk:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in new:
        if o.type == "MESH":
            o.name = f"{name}_{o.name.split('.')[0].split('_', 1)[1]}"
    arm.name = f"{name}_rig"
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm]
    _reproportion(arm, meshes)
    head = next(o for o in meshes if _is_head(o))
    body = next(o for o in meshes if o.name.endswith("_Body"))
    arms = [o for o in meshes if "_Arm" in o.name]
    legs = [o for o in meshes if "_Leg" in o.name]
    # Preserve the expressive head and armature from the CC0 base, but strip its adventurer
    # costume.  The old pouches, battle belt and ragged tunic were fighting the grounded Indian
    # worker silhouettes; the tailored clothing below is purpose-built for this cast.
    zs = [v.co.z for o in meshes for v in o.data.vertices]
    _delete_polys(body, lambda cell, c: cell == CELL["skin"])
    for o in arms:
        _delete_polys(o, lambda cell, c: cell in (CELL["skin"], CELL["hand"]))
    for o in legs:
        bpy.data.objects.remove(o, do_unlink=True)
    legs = []

    # --- face: shave, and take the hair off under a cap ---
    eye_z = 1.63
    capped = spec["head"] in ("skullcap", "hardhat", "turban", "wrap")

    def keep_head(cell, c):
        if cell != CELL["hair"]:
            return True
        z = c.z                     # already reproportioned: map back to template space
        zt = HEAD_PIVOT.z + (z - (_warp_z(HEAD_PIVOT.z) + NECK)) / HEAD_K
        if zt < 1.40:
            return spec["goatee"]
        if zt < 1.55:
            return spec["moustache"]
        return not (capped and zt > 1.86)

    _delete_polys(head, keep_head)

    # --- skin and cloth, cell by cell ---
    skin, hands = mats["skin"], mats["hands"]
    tunic = mats["shirt"]
    hair = mats["hair"]
    shoe = {"shoe": mats["shoe"], "sandal": mats["sandal"], "gumboot": mats["gumboot"]}[spec["shoes"]]
    cells = {
        CELL["skin"]: skin, CELL["hair"]: hair, CELL["eye"]: mats["eye"], CELL["metal"]: mats["steel"],
        CELL["tunic"]: tunic, CELL["sleeve"]: tunic, CELL["belt"]: mats["belt"], CELL["back"]: tunic,
        CELL["cuff"]: tunic, CELL["shorts"]: mats["trousers"], CELL["boot"]: shoe, CELL["hand"]: mats["gloves"] if "gloves" in spec["extras"] else skin,
    }
    _materials(head, cells, tunic)
    _materials(body, cells, tunic)
    for o in legs:
        _materials(o, cells, tunic)
    for o in arms:
        c = dict(cells)
        c[CELL["skin"]] = hands
        if "gloves" not in spec["extras"]:
            c[CELL["hand"]] = hands
        _materials(o, c, tunic)

    # --- scale to 1.6 m and stand on the floor ---
    top = max(zs) - min(zs)
    S = HEIGHT / top
    arm.scale = (S, S, S)
    arm.location = (0, 0, floor)

    # --- dress (built in template units, so they scale with the figure) ---
    skin_m = skin
    parts = []

    def add(o, bone=None):
        parts.append(_attach(o, arm, bone))
        return o

    nb = _warp((0, 0, 1.25)).z
    add(geo.cylinder("neck", (0, 0, nb - 0.05), 0.2, _warp_z(HEAD_PIVOT.z) + NECK - nb + 0.14, skin_m, col, segments=16, bevel=0))
    hz = lambda z: _head_pt((0, 0, z)).z
    hy = lambda y: _head_pt((0, y, 1.2)).y
    hw = lambda x: x * HEAD_K

    trou = mats["trousers"]
    # A clean work shirt replaces the template's fantasy tunic.  It is a soft, low-poly volume
    # rather than a painted texture, so its silhouette remains clear in the game layers.
    add(geo.loft("shirt_body", [
        ((0, 0, _warp_z(0.67)), 0.34, 0.23),
        ((0, 0, _warp_z(0.88)), 0.39, 0.25),
        ((0, 0, _warp_z(1.16)), 0.42, 0.24),
        ((0, 0, _warp_z(1.28)), 0.32, 0.21),
    ], tunic, col, ring=16, subsurf=1), "spine")
    cuff_r = 0.15
    if spec["legs"] in ("full", "rolled", "dhoti"):
        for side, sx in (("r", -1), ("l", 1)):
            uh, ut = _bone(arm, f"upperleg.{side}")
            lh, lt = _bone(arm, f"lowerleg.{side}")
            ankle = Vector((lt.x, lt.y, lt.z)) if spec["legs"] != "rolled" else lh.lerp(lt, 0.45)
            if spec["legs"] == "dhoti":
                continue
            add(geo.limb(f"thigh_{side}", uh + Vector((0, 0, 0.06)), ut, 0.185, 0.165, trou, col, segments=14), f"upperleg.{side}")
            add(geo.sphere(f"knee_{side}", ut, 0.165, (1, 1, 1), trou, col, segments=14, rings=10), f"upperleg.{side}")
            end = lh.lerp(lt, 0.62) if spec["legs"] == "rolled" else lt + Vector((0, 0.0, 0.03))
            add(geo.limb(f"shin_{side}", ut, end, 0.165, 0.15 if spec["legs"] != "rolled" else 0.16, trou, col, segments=14), f"lowerleg.{side}")
            fh, ft = _bone(arm, f"foot.{side}")
            add(geo.sphere(f"shoe_{side}", fh + Vector((0, -0.10, -0.015)), 1.0,
                           (0.17, 0.27, 0.11), shoe, col, segments=14, rings=8), f"foot.{side}")
    hips_h, _ = _bone(arm, "hips")
    waist = _warp((0, 0, 0.72)).z
    add(geo.cylinder("waist", (0, -0.02, waist - 0.12), 0.34, 0.17, trou, col, segments=20, bevel=0))
    if spec["legs"] == "dhoti":                      # a wrapped dhoti: a long skirt, legs showing below the knee
        add(geo.cylinder("dhoti", (0, -0.01, _warp_z(0.3)), 0.37, waist - _warp_z(0.3) - 0.02, mats["dhoti"], col, segments=24, bevel=0, radius2=0.31))
        add(geo.cylinder("dhoti_tuck", (0, -0.02, waist - 0.02), 0.31, 0.06, mats["dhoti"], col, segments=24, bevel=0))

    # sleeves over the upper arms
    for side, sx in (("r", -1), ("l", 1)):
        uh, ut = _bone(arm, f"upperarm.{side}")
        lh, lt = _bone(arm, f"lowerarm.{side}")
        if spec["sleeves"] == "half":
            add(geo.limb(f"sleeve_{side}", uh.lerp(ut, -0.1), ut.lerp(lt, 0.18), 0.19, 0.17, tunic, col, segments=14), f"upperarm.{side}")
        elif spec["sleeves"] == "full":
            add(geo.limb(f"sleeve_{side}", uh.lerp(ut, -0.1), lt.lerp(lh, 0.12), 0.19, 0.155, tunic, col, segments=14), f"upperarm.{side}")
            add(geo.limb(f"sleeve_fore_{side}", ut.lerp(lh, 0.0), lt.lerp(lh, 0.1), 0.17, 0.155, tunic, col, segments=14), f"lowerarm.{side}")

    cy = _front_y(body, 1.0)
    chest_z = _warp_z(1.0)
    belly_z = _warp_z(0.78)
    if "kurta" in spec["extras"]:                    # a long shirt over the dhoti
        add(geo.cylinder("kurta_skirt", (0, -0.01, belly_z - 0.1), 0.4, 0.5, tunic, col, segments=24, bevel=0, radius2=0.45))
    if "apron" in spec["extras"]:                    # bib apron: front panel, neck strap, waist tie, pocket (F04)
        ap = mats["apron"]
        add(geo.box("apron", (-0.3, cy - 0.06, _warp_z(0.55)), (0.3, cy - 0.02, _warp_z(1.2) + 0.05), ap, col, 0, subsurf=1))
        add(geo.box("apron_pocket", (-0.17, cy - 0.095, _warp_z(0.72)), (0.17, cy - 0.06, _warp_z(0.9)), ap, col, 0, subsurf=1))
        add(geo.box("apron_tie", (-0.38, cy - 0.03, _warp_z(0.86)), (0.38, 0.33, _warp_z(0.9)), ap, col, 0))
        for sx in (-1, 1):
            add(geo.limb(f"apron_strap{sx}", (sx * 0.2, cy - 0.04, _warp_z(1.2)), (sx * 0.1, cy + 0.05, nb + 0.02), 0.022, 0.022, ap, col, segments=8))

    # --- head and face ---
    # The source mesh is deliberately economical.  Give every worker a readable, hand-built
    # facial silhouette so the cast keeps its identity at the tiny sprite sizes and in close-ups.
    # These are rigidly skinned to the head, keeping the complete face animation-ready.
    face_y = -0.55
    brow_z = 1.76
    for sx in (-1, 1):
        add(geo.limb(f"brow{sx}", _head_pt((sx * 0.10, face_y, brow_z)),
                     _head_pt((sx * 0.34, face_y + 0.005, brow_z + 0.015)),
                     HEAD_K * 0.045, HEAD_K * 0.040, hair, col, segments=8), "head")
    add(geo.sphere("nose", _head_pt((0, -0.61, 1.60)), 1.0,
                   (hw(0.105), HEAD_K * 0.10, HEAD_K * 0.15), skin_m, col,
                   segments=12, rings=8), "head")
    if spec["moustache"]:
        for sx in (-1, 1):
            add(geo.limb(f"moustache{sx}", _head_pt((0.02 * sx, -0.585, 1.47)),
                         _head_pt((0.28 * sx, -0.57, 1.45)), HEAD_K * 0.040,
                         HEAD_K * 0.026, hair, col, segments=8), "head")
    if spec["goatee"]:
        add(geo.sphere("beard", _head_pt((0, -0.49, 1.28)), 1.0,
                       (hw(0.35), HEAD_K * 0.07, HEAD_K * 0.18), hair, col,
                       segments=14, rings=8), "head")
    if spec["head"] == "skullcap":
        add(geo.sphere("skullcap", _head_pt((0, -0.03, 1.98)), 1.0, (hw(0.6), HEAD_K * 0.54, HEAD_K * 0.4), mats["cap"], col, segments=20, rings=12))
        add(geo.cylinder("skullcap_rim", _head_pt((0, -0.03, 1.9)), 0.57 * HEAD_K * 1.02, HEAD_K * 0.07, mats["cap"], col, segments=20, bevel=0))
    elif spec["head"] == "hardhat":
        add(geo.sphere("hardhat", _head_pt((0, -0.03, 1.99)), 1.0, (hw(0.64), HEAD_K * 0.58, HEAD_K * 0.46), mats["cap"], col, segments=22, rings=12))
        add(geo.cylinder("hardhat_brim", _head_pt((0, -0.03, 1.93)), 0.62 * HEAD_K, HEAD_K * 0.05, mats["cap"], col, segments=22, bevel=0))
        add(geo.box("hardhat_peak", _head_pt((-0.4, -0.72, 1.92)), _head_pt((0.4, -0.35, 2.0)), mats["cap"], col, 0, subsurf=1))
        add(geo.box("hardhat_ridge", _head_pt((-0.04, -0.4, 2.0)), _head_pt((0.04, 0.35, 2.12)), mats["cap"], col, 0))
    elif spec["head"] == "turban":                   # a farmer's pheta, wound in coils
        wrap = mats["cap"]
        for i, (zc, r) in enumerate(((1.95, 0.62), (2.08, 0.6), (2.2, 0.5))):
            add(geo.sphere(f"turban{i}", _head_pt((0, -0.03, zc)), 1.0, (hw(r), HEAD_K * (r - 0.02), HEAD_K * 0.17), wrap, col, segments=22, rings=10, rot=(0, math.radians(7 * (i - 1)), 0)))
        add(geo.sphere("turban_top", _head_pt((0, -0.03, 2.22)), 1.0, (hw(0.44), HEAD_K * 0.42, HEAD_K * 0.2), wrap, col, segments=18, rings=10))
        add(geo.limb("turban_tail", _head_pt((0.5, 0.2, 1.9)), _head_pt((0.62, 0.4, 1.35)), HEAD_K * 0.1, HEAD_K * 0.07, wrap, col, segments=8))
    elif spec["head"] == "wrap":                     # a gamchha tied round the head
        wrap = mats["towel"]
        add(geo.sphere("wrap_band", _head_pt((0, -0.04, 1.96)), 1.0, (hw(0.6), HEAD_K * 0.57, HEAD_K * 0.26), wrap, col, segments=22, rings=10))
        add(geo.sphere("wrap_top", _head_pt((0, -0.04, 2.1)), 1.0, (hw(0.52), HEAD_K * 0.5, HEAD_K * 0.24), wrap, col, segments=18, rings=10))
        add(geo.limb("wrap_knot", _head_pt((0.2, 0.5, 1.92)), _head_pt((0.45, 0.7, 1.55)), HEAD_K * 0.1, HEAD_K * 0.06, wrap, col, segments=8))
    if "glasses" in spec["extras"]:
        for sx in (-1, 1):
            add(geo.sphere(f"lens{sx}", _head_pt((sx * 0.24, -0.5, eye_z)), 1.0, (hw(0.16), HEAD_K * 0.012, HEAD_K * 0.14), mats["glass"], col, segments=14, rings=8))
            add(_ring(f"rim{sx}", _head_pt((sx * 0.24, -0.5, eye_z)), hw(0.17), HEAD_K * 0.022, mats["frame"], col))
        add(geo.limb("glasses_bridge", _head_pt((-0.1, -0.5, eye_z)), _head_pt((0.1, -0.5, eye_z)), HEAD_K * 0.02, HEAD_K * 0.02, mats["frame"], col, segments=6))
        for sx in (-1, 1):
            add(geo.limb(f"glasses_arm{sx}", _head_pt((sx * 0.4, -0.48, eye_z)), _head_pt((sx * 0.52, -0.2, eye_z + 0.02)), HEAD_K * 0.02, HEAD_K * 0.02, mats["frame"], col, segments=6))
    if "mask" in spec["extras"]:                     # a cloth face mask over the mouth
        add(geo.sphere("mask", _head_pt((0, -0.28, 1.43)), 1.0, (hw(0.42), HEAD_K * 0.3, HEAD_K * 0.2), mats["mask"], col, segments=16, rings=8))
        for sx in (-1, 1):
            add(geo.limb(f"mask_loop{sx}", _head_pt((sx * 0.4, -0.2, 1.45)), _head_pt((sx * 0.56, 0.0, 1.5)), HEAD_K * 0.012, HEAD_K * 0.012, mats["mask"], col, segments=6))

    # --- body extras ---
    if "lanyard" in spec["extras"]:                  # ID lanyard and card (a clerk at the weigh-in)
        for sx in (-1, 1):
            add(geo.limb(f"lanyard{sx}", (sx * 0.17, cy - 0.015, nb + 0.04), (0, cy - 0.015, chest_z), 0.014, 0.014, mats["lanyard"], col, segments=6))
        add(geo.box("id_card", (-0.07, cy - 0.04, chest_z - 0.17), (0.07, cy - 0.02, chest_z - 0.02), mats["card"], col, 0, subsurf=0))
    if "pen" in spec["extras"]:
        add(geo.limb("pen", (0.2, cy - 0.025, chest_z - 0.02), (0.2, cy - 0.025, chest_z + 0.12), 0.012, 0.012, mats["frame"], col, segments=6))
    if "towel" in spec["extras"]:                    # a gamchha over one shoulder
        add(geo.limb("towel_a", (0.27, cy + 0.08, nb), (0.2, cy - 0.04, chest_z - 0.02), 0.05, 0.05, mats["towel"], col, segments=10))
        add(geo.limb("towel_b", (0.27, cy + 0.08, nb), (0.2, 0.3, chest_z - 0.4), 0.05, 0.05, mats["towel"], col, segments=10))

    # --- pose ---
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    pbs = arm.pose.bones
    info = {}
    for side, sx, target, is_right in (("r", -1, right_hand, True), ("l", 1, left_hand, False)):
        t = (Vector(target) - Vector((0, 0, floor))) / S
        uh, ut = _bone(arm, f"upperarm.{side}")
        lh, lt = _bone(arm, f"lowerarm.{side}")
        la, lb = (ut - uh).length, (lt - lh).length
        elbow = two_bone(uh, t, la, lb, (sx * 0.6, 0.4, -1))
        _aim(pbs[f"upperarm.{side}"], elbow - uh)
        fore = (t - elbow).normalized()
        _aim(pbs[f"lowerarm.{side}"], fore)
        hf = Vector(aim).normalized() if (aim and is_right) else fore
        _aim(pbs[f"wrist.{side}"], hf)
        _aim(pbs[f"hand.{side}"], hf)
        pbs[f"hand.{side}"].scale = (HAND_K, HAND_K, HAND_K)
        bpy.context.view_layer.update()
        if is_right:
            info = dict(wrist=tuple(elbow.lerp(t, 1.0) * S + Vector((0, 0, floor))), fwd=tuple(hf))
    for i, side in enumerate(("r", "l")):
        dy = -stride if i == 0 else stride                              # local -Y is forward
        lift = 0.04 if (stride and dy > 0) else 0.0                     # the trailing heel comes up
        uh, ut = _bone(arm, f"upperleg.{side}")
        lh, lt = _bone(arm, f"lowerleg.{side}")
        fh, ft = _bone(arm, f"foot.{side}")
        ankle = lt + Vector((0, dy / S, lift / S))
        knee = two_bone(uh, ankle, (ut - uh).length, (lt - lh).length, (0, -1, 0))
        _aim(pbs[f"upperleg.{side}"], knee - uh)
        _aim(pbs[f"lowerleg.{side}"], ankle - knee)
        _aim(pbs[f"foot.{side}"], ft - fh)
        _aim(pbs[f"toes.{side}"], _bone(arm, f"toes.{side}")[1] - _bone(arm, f"toes.{side}")[0])
    bpy.ops.object.mode_set(mode="OBJECT")

    root = geo.empty(f"{name}_root", (0, 0, 0), col)
    arm.parent = root
    root.location = origin
    root.rotation_euler = (0, 0, math.radians(heading))
    return root, info

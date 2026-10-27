"""People on a real rigged body: Quaternius' Universal Base Character (CC0, art/external/quaternius_ubc,
fetched 2026-10-26 from quaternius.itch.io/universal-base-characters, the free Standard pack).

`figure()` takes the same arguments as people.figure(), so a build script swaps one for the other:

    human.figure("RIYAZ_walk", origin, heading, mats, right_hand, left_hand, col, stride=0.17)

- Clothes are material regions, not meshes: every face of the body is sorted once, by the
  skeleton's own landmarks, into skin / shirt / trousers / shoes, and each figure fills those
  slots with plain woven cloth in its costume's colours (people.costume_materials); a kurta is a
  shirt region that runs to the knee.
- An apron is its own garment: a bib apron cut to shape, fitted onto the posed torso,
  with a neck strap.
- The pose is IK: each hand reaches for its wrist target, each foot for its stride. The targets are
  the same local points the old wooden figures used (facing -Y, metres), stretched to this body's
  height, so the build scripts' numbers carry over.
- A cap and a moustache are placed on the posed head; the hairstyles are CC0 meshes rigged to it.
The base body is broad-shouldered (the free pack only has the "Superhero" build), so every figure
is narrowed at the chest, shoulders and arms to an ordinary market build.
"""
import math

import bpy
from mathutils import Matrix, Vector

import geo
import materials as M
from safety import REPO

UBC = REPO / "art" / "external" / "quaternius_ubc" / "ubc"
BODY = UBC / "Base Characters" / "Godot - UE" / "Superhero_Male_FullBody.gltf"
HAIR = UBC / "Hairstyles" / "Rigged to Head Bone" / "glTF (Godot -Unreal)"
SCALE = 0.95                              # 1.82 m model -> a 1.73 m man
OLD_TO_NEW_Z = 1.10                       # old figure: shoulder 1.26 m; this body: 1.38 m (after SCALE)
SLOTS = ("skin", "shirt", "trousers", "shoe", "apron")
LOW_POLY = 0.08                           # decimate the 12.5k-face body to ~1k faces, flat shaded
BUILD = {                                 # pose-bone scale: from the "Superhero" build to an ordinary one
    "spine_03": (0.84, 0.9, 1.0), "spine_02": (0.9, 0.92, 1.0), "clavicle_l": (0.82, 1, 1), "clavicle_r": (0.82, 1, 1),
    "upperarm_l": (1.0, 0.8, 0.8), "upperarm_r": (1.0, 0.8, 0.8), "lowerarm_l": (1.0, 0.86, 0.86), "lowerarm_r": (1.0, 0.86, 0.86),
    "thigh_l": (0.9, 1.0, 0.9), "thigh_r": (0.9, 1.0, 0.9), "neck_01": (0.85, 1.0, 0.85),
}

_cache = {}


def HAIR_MAT():
    return bpy.data.materials.get("MAT_human_hair") or M.matte("MAT_human_hair", "#1E1A18", 0.55)


def _import(path, hold):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        hold.objects.link(o)
    return new


def _template():
    """Import the body once into a hidden collection and sort its faces into clothing regions."""
    if "arm" in _cache:
        return _cache
    hold = geo.collection("HUMAN_TEMPLATE")
    hold.hide_render = True
    hold.hide_viewport = True
    new = _import(BODY, hold)
    stray = [o for o in new if o.type == "MESH" and not o.data.materials]   # a stray icosphere ships in the file
    new = [o for o in new if o not in stray]
    for o in stray:
        bpy.data.objects.remove(o)
    arm = next(o for o in new if o.type == "ARMATURE")
    body = next(o for o in new if o.type == "MESH" and o.name.startswith("SuperHero"))
    extras = [o for o in new if o.type == "MESH" and o is not body]   # eyes, eyebrows
    for o in extras:
        if "brow" in o.name.lower():
            o.data.materials[0] = HAIR_MAT()
    _regions(arm, body)
    _cloth(body)
    _cache.update(arm=arm, body=body, extras=extras, hold=hold, hair={})
    return _cache


def _regions(arm, body):
    """Sort faces by where they sit on the T-posed body (bone landmarks, metres)."""
    bones = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
    neck = bones["neck_01"].z - 0.03
    shoulder_x = bones["upperarm_r"].x                    # -0.21
    elbow_x = bones["lowerarm_r"].x                       # -0.46
    waist = bones["pelvis"].z + 0.06
    knee = bones["calf_r"].z
    ankle = bones["foot_r"].z + 0.03
    me = body.data
    me.materials.clear()
    for name in SLOTS + ("trousers_long",):
        me.materials.append(M.matte(f"MAT_human_slot_{name}", "#808080", 0.8))
    for p in me.polygons:
        c = body.matrix_world @ p.center
        ax = abs(c.x)
        if c.z < ankle:
            slot = "shoe"
        elif c.z > neck and ax < 0.16:
            slot = "skin"                                 # head and neck
        elif c.z > 1.25 and ax > abs(shoulder_x) + 0.03:
            # the arms, out in the T-pose: a half sleeve to just above the elbow, then skin
            slot = "shirt" if ax < abs(shoulder_x) + 0.6 * (abs(elbow_x) - abs(shoulder_x)) else "skin"
        elif c.z > waist:
            slot = "shirt"
        elif c.z > knee + 0.08:
            slot = "trousers_long"                        # thighs: trousers, or the hem of a kurta
        else:
            slot = "trousers"
        p.material_index = (SLOTS + ("trousers_long",)).index(slot)


def _cloth(body):
    """Clothes, not body paint: stand the cloth a little off the body, then decimate the whole body
    to big flat facets (which also takes away the base body's muscle definition)."""
    me = body.data
    vg = body.vertex_groups.new(name="clothed")
    skin = SLOTS.index("skin")
    clothed = {v for p in me.polygons if p.material_index != skin for v in p.vertices}
    vg.add(list(clothed), 1.0, "REPLACE")
    d = body.modifiers.new("cloth_off_body", "DISPLACE")
    d.vertex_group, d.strength, d.mid_level = "clothed", 0.008, 0.0
    lp = body.modifiers.new("low_poly", "DECIMATE")                 # the low-poly look: big flat facets
    lp.ratio = LOW_POLY
    for k, name in enumerate(("cloth_off_body", "low_poly")):                  # both before the armature
        body.modifiers.move(body.modifiers.find(name), k)
    for p in me.polygons:
        p.use_smooth = False


def _hair(style):
    t = _template()
    if style not in t["hair"]:
        new = _import(HAIR / f"{style}.gltf", t["hold"])
        keep = [o for o in new if o.type == "MESH" and o.data.materials]
        for o in [o for o in new if o.type == "MESH" and not o.data.materials]:
            bpy.data.objects.remove(o)                    # the same stray icosphere
        for o in keep:
            o.data.materials[0] = HAIR_MAT()
            d = o.modifiers.new("low_poly", "DECIMATE")
            d.ratio = 0.15
            o.modifiers.move(o.modifiers.find("low_poly"), 0)
            for p in o.data.polygons:
                p.use_smooth = False
        t["hair"][style] = keep
    return t["hair"][style]


def _empty(name, loc, col):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.location = loc
    e.empty_display_size = 0.05
    return e


def _ik(arm, bone, target, pole, pole_angle, col, name):
    c = arm.pose.bones[bone].constraints.new("IK")
    c.target = _empty(f"{name}_ik_{bone}", target, col)
    c.pole_target = _empty(f"{name}_pole_{bone}", pole, col)
    c.pole_angle = math.radians(pole_angle)
    c.chain_count = 2


def figure(name, origin, heading, mats, right_hand, left_hand, col, tool=None, moustache=True, floor=0.0,
           grip=("loose", "loose"), edge=(0, 0, -1), aim=None, stride=0.0, hair="Hair_Buzzed", kurta=None):
    """One posed person in `col`. Hands are local wrist targets as in people.figure (facing -Y, metres
    from the feet). `stride`: metres the right foot leads. `kurta`: the shirt runs to the knee (by
    default when shirt and trousers are the same cloth). Returns the armature object."""
    t = _template()
    arm = t["arm"].copy()
    arm.name = f"{name}_rig"
    col.objects.link(arm)
    arm.location = (origin[0], origin[1], origin[2] + floor if len(origin) > 2 else floor)
    arm.rotation_euler = (0, 0, math.radians(heading))
    arm.scale = (SCALE,) * 3
    for b, s in BUILD.items():
        arm.pose.bones[b].scale = s

    long_shirt = kurta if kurta is not None else mats["shirt"] is mats["trousers"] or mats["shirt"].name.endswith("_kurta")
    shirt, trousers = fabric(mats["shirt"]), fabric(mats["trousers"])
    fill = {
        "skin": mats["skin"], "shirt": shirt, "trousers": trousers, "shoe": mats["shoe"],
        "apron": shirt, "trousers_long": shirt if long_shirt else trousers,
    }
    for src in [t["body"], *t["extras"]]:
        o = src.copy()
        o.name = f"{name}_{src.name}"
        col.objects.link(o)
        o.parent = arm
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.matrix_world = arm.matrix_world @ src.matrix_world
        for mod in o.modifiers:
            if mod.type == "ARMATURE":
                mod.object = arm
        if src is t["body"]:
            for i, slot in enumerate(SLOTS + ("trousers_long",)):
                o.material_slots[i].link = "OBJECT"
                o.material_slots[i].material = fill[slot]
        else:
            for slot in o.material_slots:                 # eyes and brows keep their own textures
                slot.link = "DATA"
    if hair and not mats.get("cap"):
        for src in _hair(hair):
            o = src.copy()
            o.name = f"{name}_{src.name}"
            col.objects.link(o)
            o.parent = arm
            o.matrix_parent_inverse = Matrix.Identity(4)
            o.matrix_world = arm.matrix_world @ src.matrix_world
            for mod in o.modifiers:
                if mod.type == "ARMATURE":
                    mod.object = arm

    # the pose: hands and feet by IK, in this figure's local frame (facing -Y)
    to_world = arm.matrix_world.copy()
    to_world_no_scale = Matrix.Translation(arm.location) @ Matrix.Rotation(math.radians(heading), 4, "Z")

    def world(p):
        x, y, z = p
        return to_world_no_scale @ Vector((x, y, z * OLD_TO_NEW_Z))

    for side, target, sx in (("r", right_hand, -1), ("l", left_hand, 1)):
        _ik(arm, f"lowerarm_{side}", world(target), world((sx * 0.55, 0.45, 1.05)), -90 if side == "r" else -90, col, name)
    if stride:
        for side, sx, dy in (("r", -1, -stride), ("l", 1, stride)):
            lift = 0.04 if dy > 0 else 0.0
            _ik(arm, f"calf_{side}", world((sx * 0.105, dy, (0.085 + lift) / OLD_TO_NEW_Z)), world((sx * 0.11, -0.8, 0.5)), -90, col, name)
    for side, kind in (("r", grip[0]), ("l", grip[1])):
        curl = {"fist": 75, "loose": 25, "flat": 4}.get(kind, 25)
        for f in ("index", "middle", "ring", "pinky"):
            for k in (1, 2, 3):
                arm.pose.bones[f"{f}_0{k}_{side}"].rotation_mode = "XYZ"
                arm.pose.bones[f"{f}_0{k}_{side}"].rotation_euler = (0, 0, math.radians(curl * (1 if side == "l" else -1)))

    # cap and moustache: found on the posed body itself (the top of the skull, the tip of the nose)
    bpy.context.view_layer.update()
    body_obj = next(o for o in col.objects if o.name == f"{name}_{t['body'].name}")
    ev = body_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
    head_c = arm.matrix_world @ arm.pose.bones["Head"].tail
    near = [q for q in pts if (q.xy - head_c.xy).length < 0.13 and q.z > head_c.z - 0.12]
    top = max(q.z for q in near)
    fwd = Matrix.Rotation(math.radians(heading), 3, "Z") @ Vector((0, -1, 0))
    nose = max(near, key=lambda q: (q - head_c).dot(fwd) - 3 * abs(q.z - (head_c.z - 0.02)))
    if mats.get("cap"):
        geo.cylinder(f"{name}_cap", (head_c.x, head_c.y, top - 0.055), 0.098, 0.07, mats["cap"], col, bevel=0.012)
    if moustache:
        geo.sphere(f"{name}_moustache", nose - fwd * 0.004 + Vector((0, 0, -0.03)), 0.024, (1.6, 0.45, 0.38), mats["eye"], col,
                   rot=(0, 0, math.radians(heading)))
    hems(name, arm, pts, shirt, col)
    if mats.get("apron"):
        apron(name, arm, body_obj, heading, fabric(mats["apron"]), col)
    return arm


def hems(name, arm, pts, cloth, col):
    """A collar band at the neckline and a hem round each sleeve, sized from the posed body where the
    shirt ends: a clean finished edge where the low-poly shirt region would otherwise end jagged."""
    neck = arm.matrix_world @ arm.pose.bones["neck_01"].head
    z = neck.z - 0.03 * SCALE
    ring = sorted((q.xy - neck.xy).length for q in pts if abs(q.z - z) < 0.012 and (q.xy - neck.xy).length < 0.11)
    r = ring[len(ring) * 3 // 4] if ring else 0.065                 # the neck itself, not the shoulder tops
    torus(f"{name}_collar", (neck.x, neck.y, z), r + 0.004, 0.011, cloth, col)
    for side in ("l", "r"):
        pb = arm.pose.bones[f"upperarm_{side}"]
        h, t = arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail
        axis = (t - h).normalized()
        c = h.lerp(t, 0.6)
        slab = [q for q in pts if abs((q - c).dot(axis)) < 0.012]
        r = max(((q - c) - axis * (q - c).dot(axis)).length for q in slab if ((q - c) - axis * (q - c).dot(axis)).length < 0.12) if slab else 0.055
        geo.limb(f"{name}_sleeve_{side}", c - axis * 0.016, c + axis * 0.016, r + 0.006, r + 0.006, cloth, col, segments=12)


def torus(name, centre, R, r, mat, col, seg=24, ring=8):
    import bmesh
    bm = bmesh.new()
    rows = []
    for i in range(seg):
        a = i / seg * 2 * math.pi
        rows.append([bm.verts.new((centre[0] + (R + r * math.cos(b)) * math.cos(a), centre[1] + (R + r * math.cos(b)) * math.sin(a),
                                   centre[2] + r * math.sin(b))) for b in (j / ring * 2 * math.pi for j in range(ring))])
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((rows[i][j], rows[(i + 1) % seg][j], rows[(i + 1) % seg][(j + 1) % ring], rows[i][(j + 1) % ring]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def colour_of(mat):
    """The main colour of a costume material: a checker's first colour, else the base colour."""
    nodes = mat.node_tree.nodes if mat.use_nodes else []
    for n in nodes:
        if n.type == "TEX_CHECKER":
            return tuple(n.inputs["Color1"].default_value)
    for n in nodes:                                       # materials.matte: the colour is the mix's A
        if n.type == "MIX" and n.data_type == "RGBA" and not n.inputs["A"].is_linked:
            return tuple(n.inputs["A"].default_value)
    for n in nodes:
        if n.type == "BSDF_PRINCIPLED":
            return tuple(n.inputs["Base Color"].default_value)
    return (0.5, 0.5, 0.5, 1)


def fabric(mat):
    """Plain woven cloth in the costume's colour: a fine weave in the bump, a soft colour wander,
    fully matte. Reads as cloth on the big low-poly facets where a printed check only smeared."""
    key = f"MAT_cloth_{mat.name}"
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    r, g, b, _ = colour_of(mat)
    n = M.Nodes(key)
    lo, hi = (r * 0.82, g * 0.82, b * 0.82, 1), (min(1, r * 1.06), min(1, g * 1.06), min(1, b * 1.06), 1)
    n.link(n.mix(n.maprange(n.noise(6.0, 3, 0.5), 0.35, 0.65), lo, hi), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.92)
    n.set("Sheen Weight", 0.25)
    weave = n.add("ShaderNodeTexWave")
    weave.wave_type = "BANDS"
    weave.inputs["Scale"].default_value = 140
    n.link(n.coords("Object"), weave.inputs["Vector"])
    n.bump(weave.outputs["Fac"], 0.08, 0.002)
    return n.mat


def apron(name, arm, body, heading, mat, col):
    """A butcher's bib apron as its own garment: cut from a grid to the outline below (local metres,
    x across, z up: the bib at the chest, flaring at the waist to the knee), laid onto the front of the
    posed torso (a depth map that leaves the arms out) and hanging flat from the hips, with a little thickness; a neck strap."""
    import bmesh
    outline = [(-0.10, 1.40), (0.10, 1.40), (0.12, 1.12), (0.19, 1.05), (0.2, 0.58), (-0.2, 0.58), (-0.19, 1.05), (-0.12, 1.12)]

    def inside(x, z):
        hit = False
        for (x0, z0), (x1, z1) in zip(outline, outline[1:] + outline[:1]):
            if (z0 > z) != (z1 > z) and x < x0 + (z - z0) * (x1 - x0) / (z1 - z0):
                hit = not hit
        return hit

    rot = Matrix.Rotation(math.radians(heading), 4, "Z")
    base = Matrix.Translation(arm.location) @ rot
    k = OLD_TO_NEW_Z * SCALE / 1.0
    # the front of the posed torso, by rays from in front (arms are left out: rays stay within |x| <= 0.13)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    to_obj = body.matrix_world.inverted() @ base
    dir_obj = (to_obj.to_3x3() @ Vector((0, 1, 0))).normalized()

    def ray_y(x, z, reach=0.13):
        o = to_obj @ Vector((max(-reach, min(reach, x)), -1.0, z))
        hit, loc, *_ = body.evaluated_get(dg).ray_cast(o, dir_obj, distance=2.0, depsgraph=dg)
        return (base.inverted() @ (body.matrix_world @ loc)).y if hit else None

    hips = [y for x in (-0.1, 0.0, 0.1) for z in (0.82 * k, 0.9 * k, 0.98 * k) if (y := ray_y(x, z)) is not None]
    skirt_y = min(hips) - 0.02

    def front(x, z):
        y = ray_y(x, z)
        return (y - 0.014) if y is not None else skirt_y

    bm = bmesh.new()
    nx, nz = 12, 22
    grid, depth = {}, {}
    xs = [-0.22 + 0.44 * i / nx for i in range(nx + 1)]
    zs = [0.60 + 0.80 * j / nz for j in range(nz + 1)]
    for i, x in enumerate(xs):
        prev = None
        for j in range(nz, -1, -1):                          # top down, so the skirt drapes
            zz = zs[j] * k / OLD_TO_NEW_Z
            if zs[j] > 1.0:                                  # the bib: laid on the chest
                y = front(x, zz)
            else:                                            # the skirt: rests on the thighs, falls straight below them
                hit = ray_y(x, zz, reach=0.17)
                y = (hit - 0.012) if hit is not None else (prev if prev is not None else skirt_y)
                y = min(y, prev if prev is not None else skirt_y)
            prev = depth[i, j] = y
    for j, z in enumerate(zs):                               # cloth bridges the gap between the legs
        if z <= 1.0:
            row = [depth[i, j] for i in range(nx + 1)]
            for i in range(nx + 1):
                depth[i, j] = min(row[max(0, i - 3):i + 4])
    for i, x in enumerate(xs):
        wrap = max(0.0, abs(x) - 0.13) * 1.2                 # the edges curl back round the body
        for j, z in enumerate(zs):
            grid[i, j] = bm.verts.new(base @ Vector((x, depth[i, j] + wrap, z * k / OLD_TO_NEW_Z)))
    for i in range(nx):
        for j in range(nz):
            cx, cz = -0.22 + 0.44 * (i + 0.5) / nx, 0.60 + 0.80 * (j + 0.5) / nz
            if inside(cx, cz):
                bm.faces.new((grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]))
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    me = bpy.data.meshes.new(f"{name}_apron")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(f"{name}_apron", me)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    th = ob.modifiers.new("cloth", "SOLIDIFY")
    th.thickness, th.offset = 0.004, 1.0
    for p in me.polygons:
        p.use_smooth = True
    # strap round the neck and ties at the waist, in the apron's cloth
    bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    pts = [ev.matrix_world @ v.co for v in m.vertices]
    ev.to_mesh_clear()
    neck = arm.matrix_world @ arm.pose.bones["neck_01"].head
    fwd = (rot.to_3x3() @ Vector((0, -1, 0)))
    side = (rot.to_3x3() @ Vector((1, 0, 0)))
    for s_ in (-1, 1):
        a = base @ Vector((s_ * 0.095, -0.12, 1.40 * k / OLD_TO_NEW_Z))
        top = neck + side * s_ * 0.06 + Vector((0, 0, 0.05))
        a = min(pts, key=lambda q: (q - a).length) + fwd * 0.016
        geo.limb(f"{name}_apron_strap{s_}", a, top, 0.009, 0.009, mat, col, segments=6)
    return ob

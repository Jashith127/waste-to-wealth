"""Rig the five Tripo/Meshy human models for the stations. Builds art/build/humans/humans_rigged.blend.

Run:  blender -b --python art/scripts/humans_build.py

Source: the five original GLBs in Downloads (user-supplied Tripo models: one mesh of ~300k triangles
each, a T-pose, unrigged, height 0.93, authored textures with nothing removed). For each:
  * the mesh is scaled to HEIGHT metres, feet on z = 0, facing -Y;
  * it is decimated to about TRIS triangles (UVs kept; the 2k normal map carries the detail);
  * a 24-bone humanoid rig (clavicles, a forearm twist, a finger and a thumb bone per hand) is fitted to
    joints measured from the T-pose's own cross-sections (landmarks), and skin weights are set by smooth
    functions of position, so it never fails the way heat weighting does on overlapping clothes;
  * the painted eyes and brows sit a little high on every model; the face UVs are lowered by a smooth
    bump (lower_face), which stretches the texture a little but never tears it;
  * a material is made from the maps (all three saved from the GLB to art/build/textures/humans),
    external so station blends stay small; plus a "wet hands" variant for Riyaz (deck p. 23).
The result is one collection HUMAN_<name> per model: an armature and its mesh. lib/humans.py appends
them into a station and poses the copies.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / "lib")]

import bpy
import numpy as np
from mathutils import Vector

import safety

DOWNLOADS = Path.home() / "Downloads"
HEIGHT = 1.58                  # metres: the models are authored 0.91-0.93 tall; the art bible wants about 1.6
TEX = safety.ART / "build" / "textures" / "humans"
OUT = safety.ART / "build" / "humans" / "humans_rigged.blend"
TRIS = 9000                    # figures are ~275 px tall in game (11 m across 1920 px); a little over what reads, for cleaner silhouettes
HEAD_KEEP = 0.3                # decimate weight on the head and hands (body 1): lower keeps more of them
SOURCES = {                    # name -> the GLB the user supplied
    "farmer": "farmer character 3d model.glb",       # checked shirt, bib apron, skullcap, beard
    "chef": "chef character 3d model.glb",
    "office": "office worker 3d model.glb",
    "worker": "stylized character 3d model.glb",
    "construction": "construction worker 3d model.glb",
}
# How far each model's painted eyes and brows sit too high, in the models' own units (0.014 is about 2.4 cm).
# Measured against the sculpted brow ridge on clay vs textured close-ups (office is under glasses, construction under a mask: right as is).
FACE_DROP = {"farmer": 0.014, "chef": 0.015, "office": 0.0, "worker": 0.009, "construction": 0.0}

# Landmarks in the models' own units (height 0.91-0.93, arm span 1.0). The torso and leg heights are the
# same across the five to within a few per cent; the arm's joints and centre line are measured per model
# (landmarks): the arms hang about 5 cm behind the body's centre, and the hand is a third of the arm.
SHOULDER_X = 0.14
HIP_Z, KNEE_Z, ANKLE_Z = 0.44, 0.225, 0.065


def smooth(x, a, b):
    """0 below a, 1 above b (either order), smooth between."""
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def landmarks(co, s):
    """The joints of this model's T-pose, from cross-sections of the full-resolution mesh (model units).
    The wrist is the narrowest slice of the forearm; the knuckles are where the thumb ends."""
    p = co / s
    ax = np.abs(p[:, 0])
    arm = p[(ax > SHOULDER_X + 0.02) & (p[:, 2] > 0.45)]
    aax = np.abs(arm[:, 0])

    def slab(lo, hi, pts=arm, px=aax):
        return pts[(px >= lo) & (px < hi)]

    def centre(sl):
        return (sl[:, 1].min() + sl[:, 1].max()) / 2, (sl[:, 2].min() + sl[:, 2].max()) / 2

    areas = []
    for x0 in np.arange(0.28, 0.40, 0.005):
        sl = slab(x0, x0 + 0.005)
        if len(sl) > 8:
            areas.append((np.ptp(sl[:, 1]) * np.ptp(sl[:, 2]), x0 + 0.0025))
    wrist = min(areas)[1]
    arm_y, arm_z = centre(slab(SHOULDER_X + 0.04, wrist - 0.01))
    knuckle = wrist + 0.085
    hand_y, hand_z = centre(slab(knuckle, knuckle + 0.03))
    end = float(aax.max())
    palm = slab(wrist + 0.015, knuckle)
    tip = palm[np.argmin(palm[:, 1] - 0.5 * palm[:, 2])]         # the thumb: forward of the palm, and below it
    legs = p[(p[:, 2] < HIP_Z - 0.04) & (ax > 0.012)]
    lax = np.abs(legs[:, 0])
    leg_x = float((lax.min() + lax.max()) / 2) if len(legs) else 0.075
    leg_y = float(np.median(legs[:, 1])) if len(legs) else 0.0
    torso = p[(p[:, 2] > 0.48) & (p[:, 2] < 0.62) & (ax < 0.08)]
    body_y = float((torso[:, 1].min() + torso[:, 1].max()) / 2)
    return dict(wrist=float(wrist), elbow=float((SHOULDER_X + wrist) / 2 + 0.01), knuckle=float(knuckle), end=end,
                arm_y=float(arm_y), arm_z=float(arm_z), hand_y=float(hand_y), hand_z=float(hand_z),
                thumb=(float(abs(tip[0])), float(tip[1]), float(tip[2])),
                leg_x=leg_x, leg_y=leg_y, body_y=body_y)


def read_co(me):
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def decimate(obj, tris, s, L):
    """Collapse to about `tris`, after welding the GLB's seam-split vertices (UVs live on loops, so they
    survive) so the collapse can't open cracks along the seams. The head and hands keep more of the
    budget: the face is read up close, and the hands bend at the fingers; the clothes are flat colour."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4 * s)
    bm.to_mesh(obj.data)
    bm.free()
    p = read_co(obj.data) / s
    vg = obj.vertex_groups.new(name="_keep")
    keep = np.maximum(smooth(p[:, 2], 0.62, 0.70), smooth(np.abs(p[:, 0]), L["wrist"] - 0.03, L["wrist"]))
    w = 1 - (1 - HEAD_KEEP) * keep                            # 1 on the body, HEAD_KEEP on the head and hands
    for v in np.unique(np.round(w, 2)):                       # every vertex weighted: an unweighted one is never collapsed
        vg.add([int(i) for i in np.nonzero(np.round(w, 2) == v)[0]], float(v), "REPLACE")
    n = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    mod = obj.modifiers.new("decimate", "DECIMATE")
    mod.vertex_group = vg.name
    mod.vertex_group_factor = 1.0
    ratio = min(1.0, tris / n)
    for _ in range(6):                                        # the protected head makes the count overshoot: steer the ratio
        mod.ratio = ratio
        dg = bpy.context.evaluated_depsgraph_get()
        new = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), depsgraph=dg)
        got = sum(len(p.vertices) - 2 for p in new.polygons)
        print(f"[decimate] ratio={ratio:.4f} tris={got}", flush=True)
        if got <= tris * 1.08 or _ == 5:
            break
        bpy.data.meshes.remove(new)
        ratio *= tris / got
    obj.modifiers.remove(mod)
    obj.vertex_groups.remove(vg)
    old = obj.data
    obj.data = new
    bpy.data.meshes.remove(old)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def save_map(img, path, size=2048):
    path.parent.mkdir(parents=True, exist_ok=True)
    if max(img.size) > size:
        img.scale(size, size)
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    return path


def skin_tone(mesh, img, s, L):
    """The model's own painted skin, from the texels under its palms (the saturated ones: the backs of the
    hands are unpainted grey in every Tripo texture)."""
    me = mesh.data
    co = read_co(me)
    loops = np.empty(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", loops)
    uvs = np.empty(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers[0].data.foreach_get("uv", uvs)
    uvs = uvs.reshape(-1, 2)[np.abs(co[loops, 0]) / s > L["wrist"] + 0.02]
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)[..., :3]
    c = px[np.clip((uvs[:, 1] * h).astype(int), 0, h - 1), np.clip((uvs[:, 0] * w).astype(int), 0, w - 1)]
    sat = c.max(1) - c.min(1)
    c = c[sat > 0.15]
    return tuple(float(v) for v in np.median(c, axis=0)) + (1.0,) if len(c) else (0.55, 0.36, 0.25, 1.0)


def attribute(nt, name):
    n = nt.nodes.new("ShaderNodeAttribute")
    n.attribute_name = name
    return n.outputs["Fac"]


def material(name, base_path, normal_path, rm_path, skin, wet=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])

    def image(path, colour):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(str(path), check_existing=True)
        n.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        n.interpolation = "Linear"
        return n
    base, normal, rm = image(base_path, True), image(normal_path, False), image(rm_path, False)
    # the backs of the hands are unpainted (grey) in the source: on the hands, grey texels become skin
    hsv = nt.nodes.new("ShaderNodeSeparateColor")
    hsv.mode = "HSV"
    nt.links.new(base.outputs["Color"], hsv.inputs["Color"])
    grey = nt.nodes.new("ShaderNodeMapRange")                 # 1 where unsaturated
    grey.inputs["From Min"].default_value, grey.inputs["From Max"].default_value = 0.45, 0.3   # skin is ~0.8 (linear HSV)
    nt.links.new(hsv.outputs["Green"], grey.inputs["Value"])
    fill = nt.nodes.new("ShaderNodeMath")
    fill.operation = "MULTIPLY"
    nt.links.new(grey.outputs["Result"], fill.inputs[0])
    nt.links.new(attribute(nt, "hand"), fill.inputs[1])
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    nt.links.new(fill.outputs[0], col.inputs[0])
    nt.links.new(base.outputs["Color"], col.inputs[6])
    col.inputs[7].default_value = skin
    nt.links.new(col.outputs[2], bsdf.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.8
    nt.links.new(normal.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(rm.outputs["Color"], sep.inputs["Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")                # matte: the maps read plasticky, so floor the roughness
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = 0.4, 1.0
    nt.links.new(sep.outputs["Green"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.0                # the maps' metal channel is noise on cloth and skin
    bsdf.inputs["Subsurface Weight"].default_value = 0.06
    if wet:                                                    # glossy forearms and hands: the "wet" attribute, set at rest
        mix = nt.nodes.new("ShaderNodeMix")                 # wet: glossy, not coated (the coat read as grey patches)
        mix.data_type = "FLOAT"
        mix.inputs[3].default_value = 0.3
        nt.links.new(attribute(nt, "wet"), mix.inputs[0])
        nt.links.new(rough.outputs["Result"], mix.inputs[2])
        nt.links.new(mix.outputs[0], bsdf.inputs["Roughness"])
    return mat


def weights(co, s, L):
    """{bone: per-vertex weight array} from vertex positions in the model's own units (co / s)."""
    p = co / s
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    ax = np.abs(x)
    side_l = smooth(x, -0.03, 0.03)                         # 1 on the +X (left) side
    # torso chain: hips -> spine -> chest -> neck -> head
    s1, s2, s3, s4 = smooth(z, 0.44, 0.54), smooth(z, 0.54, 0.60), smooth(z, 0.64, 0.67), smooth(z, 0.68, 0.71)
    T = dict(hips=1 - s1, spine=s1 * (1 - s2), chest=s1 * s2 * (1 - s3), neck=s1 * s2 * s3 * (1 - s4), head=s1 * s2 * s3 * s4)
    # the top of the shoulder, inside the arm root, rides the clavicle (a raised arm lifts it)
    clav = smooth(ax, 0.05, SHOULDER_X) * smooth(z, L["arm_z"] - 0.07, L["arm_z"] - 0.01) * (1 - s3)
    # arms: everything out past the shoulders, above the hips; along the arm by the measured joints
    a = smooth(ax, SHOULDER_X - 0.01, SHOULDER_X + 0.045) * smooth(z, 0.47, 0.50)
    up = 1 - smooth(ax, L["elbow"] - 0.03, L["elbow"] + 0.03)
    hand = smooth(ax, L["wrist"] - 0.012, L["wrist"] + 0.012)
    fore = np.clip(1 - up - hand, 0, 1)
    twist = fore * smooth(ax, L["elbow"] + 0.01, L["wrist"])    # the wrist half of the forearm shares the palm's roll
    # in the hand: the thumb (forward of and below the palm), the fingers (past the knuckles), the palm
    ry, rz = y - L["hand_y"], z - L["hand_z"]
    thumb = np.maximum(smooth(-ry, 0.055, 0.07), smooth(-rz, 0.024, 0.034)) * (1 - smooth(ax, L["knuckle"] - 0.005, L["knuckle"] + 0.01))
    thumb *= smooth(ax, L["wrist"] + 0.005, L["wrist"] + 0.02)
    fingers = smooth(ax, L["knuckle"] - 0.01, L["knuckle"] + 0.008) * (1 - thumb)
    palm = np.clip(1 - thumb - fingers, 0, 1)
    # legs: below the crotch, by side, then thigh / shin / foot
    l = smooth(z, HIP_Z + 0.06, HIP_Z - 0.04)
    thigh = smooth(z, KNEE_Z - 0.035, KNEE_Z + 0.035)
    foot = 1 - smooth(z, ANKLE_Z - 0.025, ANKLE_Z + 0.03)
    shin = 1 - thigh - foot
    overlap = a + l
    k = np.where(overlap > 1, 1 / np.maximum(overlap, 1e-6), 1.0)
    a, l = a * k, l * k
    body = 1 - a - l
    W = {name: body * w for name, w in T.items()}
    W["chest"] = body * T["chest"] * (1 - clav)
    for side, sw in (("L", side_l), ("R", 1 - side_l)):
        W[f"clavicle.{side}"] = body * T["chest"] * clav * sw
        W[f"upperarm.{side}"] = a * up * sw
        W[f"lowerarm.{side}"] = a * (fore - twist) * sw
        W[f"twist.{side}"] = a * twist * sw
        W[f"hand.{side}"] = a * hand * palm * sw
        W[f"fingers.{side}"] = a * hand * fingers * sw
        W[f"thumb.{side}"] = a * hand * thumb * sw
        W[f"upperleg.{side}"] = l * thigh * sw
        W[f"lowerleg.{side}"] = l * shin * sw
        W[f"foot.{side}"] = l * foot * sw
    return W


def rig(name, s, L):
    """The armature, in metres, from the measured T-pose landmarks `L` scaled by `s`. Arm bones run down
    the arm's own centre line (behind the body's), roll 0: each bone's local Z is up, so a T-pose palm
    faces local -Z."""
    data = bpy.data.armatures.new(f"{name}_rig")
    obj = bpy.data.objects.new(f"HUMAN_{name}_rig", data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones

    def bone(bname, head, tail, parent=None, connect=False):
        b = eb.new(bname)
        b.head, b.tail = Vector(head) * s, Vector(tail) * s
        b.roll = 0
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        return b
    by, ay, az, hy, hz = L["body_y"], L["arm_y"], L["arm_z"], L["hand_y"], L["hand_z"]
    el, wr, kn = L["elbow"], L["wrist"], L["knuckle"]
    mid = (el + wr) / 2
    bone("hips", (0, by, 0.42), (0, by, 0.50))
    bone("spine", (0, by, 0.50), (0, by, 0.57), "hips")
    bone("chest", (0, by, 0.57), (0, by, 0.645), "spine")
    bone("neck", (0, by, 0.645), (0, by, 0.69), "chest")
    bone("head", (0, by, 0.69), (0, by, 0.92), "neck")
    tx, ty, tz = L["thumb"]
    for side, sx in (("L", 1), ("R", -1)):
        bone(f"clavicle.{side}", (sx * 0.02, ay, az + 0.01), (sx * SHOULDER_X, ay, az), "chest")
        bone(f"upperarm.{side}", (sx * SHOULDER_X, ay, az), (sx * el, ay, az), f"clavicle.{side}", True)
        lo = bone(f"lowerarm.{side}", (sx * el, ay, az), (sx * mid, ay, az), f"upperarm.{side}", True)
        tw = bone(f"twist.{side}", (sx * mid, ay, az), (sx * wr, ay, az), f"lowerarm.{side}", True)
        hd = bone(f"hand.{side}", (sx * wr, ay, az), (sx * kn, hy, hz), f"twist.{side}", True)
        bone(f"fingers.{side}", (sx * kn, hy, hz), (sx * L["end"], hy, hz), f"hand.{side}", True)
        bone(f"thumb.{side}", (sx * (wr + 0.015), ay - 0.03, az - 0.012), (sx * tx, ty, tz), f"hand.{side}")
        lo.inherit_scale = tw.inherit_scale = hd.inherit_scale = "NONE"   # arms are lengthened per bone (humans.ARM_K), the hand is not
        lx, ly = L["leg_x"], L["leg_y"]
        bone(f"upperleg.{side}", (sx * lx, ly, HIP_Z), (sx * lx, ly + 0.005, KNEE_Z), "hips")
        bone(f"lowerleg.{side}", (sx * lx, ly + 0.005, KNEE_Z), (sx * lx, ly + 0.01, ANKLE_Z), f"upperleg.{side}", True)
        bone(f"foot.{side}", (sx * lx, ly + 0.01, ANKLE_Z), (sx * lx, ly - 0.1, 0.02), f"lowerleg.{side}", True)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def lower_face(mesh, s, drop):
    """Lower the painted eyes and brows onto the sculpted sockets: they sit about `drop` (model units)
    too high. The face island is rotated in the atlas, so "down the face" is not down the texture: for each
    corner the UV gradient along the surface's up direction is measured from its own island, and the UVs
    move by a smooth bump of `drop` along it, over the brow-and-eye band (zero at the nose and mouth, and
    at the cap or hairline). The island is stretched a little, never cut."""
    me = mesh.data
    me.calc_loop_triangles()
    co = read_co(me)
    nv = len(co)
    loops = np.empty(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", loops)
    uv = me.uv_layers[0].data
    uvs = np.empty(len(uv) * 2, dtype=np.float32)
    uv.foreach_get("uv", uvs)
    uvs = uvs.reshape(-1, 2)
    tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("loops", tri)
    tri = tri.reshape(-1, 3)
    P = co[loops[tri]]                                        # (T, 3 corners, 3)
    U = uvs[tri]                                              # (T, 3, 2)
    e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
    du1, du2 = U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]
    n = np.cross(e1, e2)
    nl = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.maximum(nl, 1e-12)
    up = np.array([0, 0, 1.0], dtype=np.float32)
    t = up - n * (n @ up)[:, None]                            # "up" within the triangle's plane
    tl = np.linalg.norm(t, axis=1)
    # t = a e1 + b e2 (least squares in the plane)
    g11, g12, g22 = (e1 * e1).sum(1), (e1 * e2).sum(1), (e2 * e2).sum(1)
    r1, r2 = (t * e1).sum(1), (t * e2).sum(1)
    det = g11 * g22 - g12 * g12
    ok = (det > 1e-14) & (tl > 0.3)
    a_ = np.where(ok, (r1 * g22 - r2 * g12) / np.where(ok, det, 1), 0)
    b_ = np.where(ok, (r2 * g11 - r1 * g12) / np.where(ok, det, 1), 0)
    grad = (a_[:, None] * du1 + b_[:, None] * du2) / np.maximum(tl, 1e-6)[:, None]   # UV change per metre up the surface
    grad[~ok] = 0
    # average per (vertex, island): corners of a vertex whose UVs are close share a gradient
    key = loops[tri].reshape(-1).astype(np.int64) * 1_000_003 + (np.round(U.reshape(-1, 2)[:, 0] * 400).astype(np.int64) * 7919 + np.round(U.reshape(-1, 2)[:, 1] * 400).astype(np.int64))
    g = np.repeat(grad, 3, axis=0)
    wts = np.repeat(ok.astype(np.float32), 3)
    uniq, inv = np.unique(key, return_inverse=True)
    sums = np.zeros((len(uniq), 2), dtype=np.float32)
    cnt = np.zeros(len(uniq), dtype=np.float32)
    np.add.at(sums, inv, g * wts[:, None])
    np.add.at(cnt, inv, wts)
    avg_tri = (sums / np.maximum(cnt, 1)[:, None])[inv]       # per triangle-corner
    # write per loop (every loop appears in at least one triangle corner)
    loop_g = np.zeros((len(uvs), 2), dtype=np.float32)
    loop_g[tri.reshape(-1)] = avg_tri
    p = co[loops] / s
    z, x, y = p[:, 2], p[:, 0], p[:, 1]
    band = smooth(z, 0.745, 0.775) * (1 - smooth(z, 0.805, 0.83))
    front = smooth(-y, 0.02, 0.07) * (1 - smooth(np.abs(x), 0.09, 0.14))
    uvs += loop_g * (drop * s * band * front)[:, None]
    uv.foreach_set("uv", uvs.ravel())


def build():
    safety.fresh_scene()
    scene = bpy.context.scene
    for name, glb in SOURCES.items():
        before, before_imgs = set(bpy.data.objects), set(bpy.data.images)
        bpy.ops.import_scene.gltf(filepath=str(DOWNLOADS / glb))
        new_imgs = [i for i in bpy.data.images if i not in before_imgs]
        new = [o for o in bpy.data.objects if o not in before]
        mesh = next(o for o in new if o.type == "MESH")
        # scale to metres (the models are authored 0.93 tall), drop anything else the GLB brought
        co = read_co(mesh.data)
        s = HEIGHT / float(co[:, 2].max())
        mesh.data.vertices.foreach_set("co", (co * s).ravel())
        mesh.data.update()
        mesh.parent = None
        mesh.matrix_world = mesh.matrix_basis.__class__()
        for o in new:
            if o.type != "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
        # textures: all three maps from the GLB, saved external
        imgs = {k: next(i for i in new_imgs if k in i.name.lower()) for k in ("basecolor", "normal", "_rm")}
        base_path = save_map(imgs["basecolor"], TEX / f"{name}_base.png")
        normal_path = save_map(imgs["normal"], TEX / f"{name}_normal.png")
        rm_path = save_map(imgs["_rm"], TEX / f"{name}_rm.png")
        for i in new_imgs:                                  # the GLB's embedded copies are no longer needed
            bpy.data.images.remove(i)
        L = landmarks(read_co(mesh.data), s)
        print(f"[landmarks] {name}: " + ", ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={tuple(round(c, 3) for c in v)}" for k, v in L.items()), flush=True)
        decimate(mesh, TRIS, s, L)
        if FACE_DROP[name]:
            lower_face(mesh, s, FACE_DROP[name])
        mesh.name = f"HUMAN_{name}"
        mesh.data.name = f"HUMAN_{name}_mesh"
        # shader masks, written at rest so they ride the deform: hands (for the unpainted backs) and wet forearms
        co = read_co(mesh.data)
        ax = np.abs(co[:, 0]) / s
        for aname, val in (("hand", smooth(ax, L["wrist"] - 0.02, L["wrist"])), ("wet", smooth(ax, L["wrist"] - 0.07, L["wrist"] - 0.03))):
            mesh.data.attributes.new(aname, "FLOAT", "POINT").data.foreach_set("value", val.astype(np.float32))
        skin = skin_tone(mesh, bpy.data.images.load(str(base_path), check_existing=True), s, L)
        skin = tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in skin[:3]) + (1.0,)   # sRGB texels -> linear
        print(f"[skin] {name}: {tuple(round(c, 3) for c in skin)}", flush=True)
        mesh.data.materials.clear()
        mesh.data.materials.append(material(f"MAT_human_{name}", base_path, normal_path, rm_path, skin))
        wet = material(f"MAT_human_{name}_wet", base_path, normal_path, rm_path, skin, wet=True)
        # rig and skin
        arm = rig(name, s, L)
        W = weights(co, s, L)
        for bname, w in W.items():
            vg = mesh.vertex_groups.new(name=bname)
            idx = np.nonzero(w > 0.012)[0]
            for i in idx:
                vg.add([int(i)], float(w[i]), "REPLACE")
        mod = mesh.modifiers.new("armature", "ARMATURE")
        mod.object = arm
        mesh.parent = arm
        mesh["scale"] = s
        mesh["wet_material"] = wet.name
        mesh["height"] = float(co[:, 2].max())
        # file them in their own collection, off the scene
        col = bpy.data.collections.new(f"HUMAN_{name}")
        for o in (arm, mesh):
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
        scene.collection.children.link(col)
        print(f"[human] {name}: s={s:.3f} tris={sum(len(p.vertices) - 2 for p in mesh.data.polygons)} verts={len(mesh.data.vertices)}", flush=True)
    for m in list(bpy.data.materials):
        m.use_fake_user = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    safety.guard(OUT, safety.ART)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True, relative_remap=True)
    print(f"[save] {OUT}")


if __name__ == "__main__":
    build()

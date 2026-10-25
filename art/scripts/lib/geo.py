"""Geometry helpers. 1 unit = 1 m, +Z up. Every hard edge is bevelled (art-bible §2):
1.5 cm on props, 2 cm on architecture, 2 segments."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

BEVEL_PROP = 0.015
BEVEL_ARCH = 0.02


def collection(name, parent=None):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in (parent or bpy.context.scene.collection).children:
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def _obj(name, bm, mat, col, bevel, subsurf=0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    if mat:
        me.materials.append(mat)
    if bevel:
        b = obj.modifiers.new("bevel", "BEVEL")
        b.width, b.segments, b.limit_method = bevel, 2, "ANGLE"
        b.harden_normals = False
    if subsurf:
        s = obj.modifiers.new("round", "SUBSURF")
        s.levels = s.render_levels = subsurf
    for p in me.polygons:
        p.use_smooth = bool(subsurf)
    return obj


def box(name, lo, hi, mat=None, col=None, bevel=BEVEL_PROP, subsurf=0):
    """Axis-aligned box from corner `lo` to corner `hi` (world metres)."""
    lo, hi = Vector(lo), Vector(hi)
    size, centre = hi - lo, (hi + lo) / 2
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(centre) @ Matrix.Diagonal((*size, 1.0)), verts=bm.verts)
    _box_uvs(bm)
    return _obj(name, bm, mat, col, bevel, subsurf)


def _box_uvs(bm):
    """Planar UVs per face in metres, so procedural textures and images map predictably."""
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        u_ax, v_ax = [(1, 2), (0, 2), (0, 1)][ax]
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = (co[u_ax], co[v_ax])


def panel(name, centre, size, normal="-Y", mat=None, col=None):
    """Flat quad with 0..1 UVs (for image textures such as signboards). size=(w, h)."""
    w, h = size
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new("UVMap")
    for loop, co in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = co
    rot = {"-Y": Matrix.Identity(4), "+X": Matrix.Rotation(math.radians(90), 4, "Z"),
           "-X": Matrix.Rotation(math.radians(-90), 4, "Z"),
           "+Z": Matrix.Rotation(math.radians(-90), 4, "X")}[normal]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(centre) @ rot, verts=bm.verts)
    return _obj(name, bm, mat, col, 0)


def cylinder(name, base, radius, height, mat=None, col=None, segments=24, bevel=BEVEL_PROP, axis="Z", radius2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if radius2 is None else radius2, depth=height)
    rot = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.radians(90), 4, "Y"),
           "Y": Matrix.Rotation(math.radians(90), 4, "X")}[axis]
    offset = {"Z": Vector((0, 0, height / 2)), "X": Vector((height / 2, 0, 0)), "Y": Vector((0, height / 2, 0))}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(base) + offset) @ rot, verts=bm.verts)
    _box_uvs(bm)
    obj = _obj(name, bm, mat, col, bevel)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def sphere(name, centre, radius, scale=(1, 1, 1), mat=None, col=None, segments=24, rings=16, rot=(0, 0, 0)):
    """UV sphere baked at `centre`; `rot` (radians, XYZ) turns it about its own centre."""
    from mathutils import Euler
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    m = Matrix.Translation(centre) @ Euler(rot, "XYZ").to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    _box_uvs(bm)
    obj = _obj(name, bm, mat, col, 0)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def empty(name, loc, col=None):
    e = bpy.data.objects.new(name, None)
    (col or bpy.context.scene.collection).objects.link(e)
    e.location = loc
    return e


def parent_keep(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def set_render_role(obj, role):
    """Per-layer visibility (Cycles): 'normal', 'hidden' (still lights/shadows, not seen),
    'holdout' (cuts alpha, for occluders in front of a sprite), 'catcher' (shadow catcher)."""
    obj.hide_render = False
    obj.visible_camera = role != "hidden"
    obj.is_holdout = role == "holdout"
    obj.is_shadow_catcher = role == "catcher"

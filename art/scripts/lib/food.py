"""Off-the-shelf meat: Kenney's Food Kit (CC0, art/external/kenney_food, fetched 2026-10-26 from
kenney.nl/assets/food-kit). Its models are clean low-poly cuts painted from one colour atlas; here the
atlas is re-read as meat: its dark tones become lean, its light tones fat and bone, under a wet coat,
so the cuts sit with the rest of the art instead of reading as cartoon brown.

    food.cut("RIBS", "meat-ribs", (x, y, z), col, size=0.2, look="raw", rot=30)
"""
import math
from pathlib import Path

import bpy
from mathutils import Vector

import materials as M
from safety import REPO

KIT = REPO / "art" / "external" / "kenney_food" / "Models" / "GLB format"
LOOKS = {
    "raw": [(0.0, "#4A1612"), (0.3, "#7E2A22"), (0.5, "#A8463A"), (0.62, "#D9C7A4"), (0.8, "#EDE3CE")],
    "cooked": [(0.0, "#2E1A0E"), (0.35, "#5E3A1E"), (0.6, "#8E5E34"), (0.8, "#C9A06A")],
}


def meat_look(look, atlas):
    key = f"MAT_kenney_{look}"
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    n = M.Nodes(key)
    tex = n.add("ShaderNodeTexImage")
    tex.image = atlas
    tex.interpolation = "Closest"
    uv = n.add("ShaderNodeUVMap")
    n.link(uv.outputs["UV"], tex.inputs["Vector"])
    bw = n.add("ShaderNodeRGBToBW")
    n.link(tex.outputs["Color"], bw.inputs["Color"])
    # a little mottling inside each painted region, so a flat atlas patch reads as flesh
    mott = n.add("ShaderNodeMath", operation="ADD")
    n.link(bw.outputs["Val"], mott.inputs[0])
    n.link(n.maprange(n.noise(28.0, 4, 0.6), 0.3, 0.7, -0.05, 0.05), mott.inputs[1])
    n.link(n.ramp(mott.outputs[0], LOOKS[look]), n.bsdf.inputs["Base Color"])
    n.set("Roughness", 0.32 if look == "raw" else 0.5)
    n.set("Coat Weight", 0.5 if look == "raw" else 0.25)
    n.set("Subsurface Weight", 0.1 if look == "raw" else 0.0)
    n.bump(n.noise(40.0, 5, 0.7), 0.25, 0.003)
    return n.mat


def cut(name, model, loc, col, size=0.2, look="raw", rot=0.0, tilt=(0.0, 0.0)):
    """Place one Kenney cut, its longest side `size` metres, resting on `loc` (its base), in `col`."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(KIT / f"{model}.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    k = size / max(hi - lo)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        o.name = f"{name}_{o.name}"
        if o.parent is None:
            o.parent = root
            o.location -= centre
    for o in meshes:
        atlas = next((n.image for n in o.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"), None)
        o.data.materials[0] = meat_look(look, atlas)
        for p in o.data.polygons:
            p.use_smooth = True
    root.location = loc
    root.rotation_euler = (math.radians(tilt[0]), math.radians(tilt[1]), math.radians(rot))
    root.scale = (k, k, k)
    return root

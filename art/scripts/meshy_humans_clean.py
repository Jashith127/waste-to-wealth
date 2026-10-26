"""Assemble and repair the five user-supplied Meshy GLB humans.

The GLBs keep their authored UVs and embedded texture images.  Texture Mapping nodes are removed
because their transforms were causing the visibly offset surface maps; each image is explicitly
driven by the mesh's UV map.  The scene is intentionally a compact review render.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import bpy
from mathutils import Vector

import geo
import safety


DOWNLOADS = Path(r"C:\Users\Jash\Downloads")
OUT_BLEND = safety.ART / "blender" / "meshy_humans_clean.blend"
OUT_RENDER = safety.ART / "build" / "renders" / "humans" / "meshy_humans_clean.png"
SOURCES = (
    ("Chef", "chef character 3d model.glb"),
    ("Construction", "construction worker 3d model.glb"),
    ("Farmer", "farmer character 3d model.glb"),
    ("Worker", "stylized character 3d model.glb"),
    ("Office", "office worker 3d model.glb"),
)


def repair_material(mat):
    """Reset image coordinates to raw UVs, preserving the authored texture/normal maps."""
    if not mat or not mat.use_nodes:
        return
    tree = mat.node_tree
    for node in list(tree.nodes):
        if node.type == "MAPPING":
            tree.nodes.remove(node)
    uv = next((n for n in tree.nodes if n.type == "UVMAP"), None)
    if uv is None:
        uv = tree.nodes.new("ShaderNodeUVMap")
        uv.name = "UV_REPAIRED"
    for node in tree.nodes:
        if node.type == "TEX_IMAGE" and node.inputs.get("Vector"):
            vector = node.inputs["Vector"]
            for link in list(vector.links):
                tree.links.remove(link)
            tree.links.new(uv.outputs["UV"], vector)
            node.interpolation = "Linear"
            node.extension = "REPEAT"
    mat.diffuse_color[3] = 1.0


def lower_facial_uv(obj, amount=0.0):
    """Move only the front-of-head UV island down ~20–25 texture pixels.

    Meshy bakes eyes and brows into the facial albedo.  Treating the face as a compact island
    avoids reprojecting the whole character or disrupting clothing/seams.
    """
    if not amount or obj.type != "MESH" or not obj.data.uv_layers.active:
        return
    verts = obj.data.vertices
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    width, depth, height = max_x - min_x, max_y - min_y, max_z - min_z
    # The lineup is front-facing -Y.  This conservative band captures forehead, brows and eyes
    # without touching cap/head-wrap geometry or the rest of the texture atlas.
    z0, z1 = min_z + height * 0.69, min_z + height * 0.89
    y_front = min_y + depth * 0.31
    x_limit = width * 0.24
    uv = obj.data.uv_layers.active.data
    for poly in obj.data.polygons:
        centre = sum((verts[i].co for i in poly.vertices), Vector()) / len(poly.vertices)
        if z0 <= centre.z <= z1 and centre.y <= y_front and abs(centre.x) <= x_limit:
            for loop_index in poly.loop_indices:
                uv[loop_index].uv.y += amount


def imported_bounds(objects):
    pts = []
    for obj in objects:
        if obj.type == "MESH":
            pts.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))


def label(text, x, mat):
    curve = bpy.data.curves.new(f"LABEL_{text}", "FONT")
    curve.body, curve.align_x, curve.size = text, "CENTER", 0.18
    curve.extrude = 0.002
    obj = bpy.data.objects.new(f"LABEL_{text}", curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (x, -0.42, 0.02)
    obj.rotation_euler = (1.5708, 0, 0)
    obj.data.materials.append(mat)


def add_lights():
    for name, loc, energy, size, colour in (
        ("KEY", (-5, -6, 6), 1000, 4.5, (1.0, 0.84, 0.68)),
        ("FILL", (5, -4, 4), 650, 4, (0.68, 0.80, 1.0)),
        ("RIM", (0, 3, 6), 900, 3, (1.0, 0.94, 0.84)),
    ):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.shape, d.size, d.color = energy, "DISK", size, colour
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.9)) - o.location).to_track_quat("-Z", "Y").to_euler()


def build():
    safety.fresh_scene()
    scene = bpy.context.scene
    # EEVEE crashes in the headless driver when these imported texture arrays are compiled.
    # A small denoised CPU Cycles pass is reliable and is sufficient for the requested review.
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 4
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1200, 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("WORLD_clean_meshy")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = ((0.025, 0.035, 0.05, 1), 0.22)
    floor = bpy.data.materials.new("MAT_floor")
    floor.diffuse_color = (0.11, 0.15, 0.22, 1)
    ink = bpy.data.materials.new("MAT_ink")
    ink.diffuse_color = (0.92, 0.90, 0.84, 1)
    geo.box("STAGE", (-4.0, -0.15, -0.08), (4.0, 0.8, 0), floor, None, 0.02)
    positions = (-3.1, -1.55, 0, 1.55, 3.1)
    for (title, filename), x in zip(SOURCES, positions):
        source = DOWNLOADS / filename
        if not source.exists():
            raise FileNotFoundError(source)
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(source))
        imported = [o for o in bpy.data.objects if o not in before]
        root = bpy.data.objects.new(f"{title.upper()}_root", None)
        bpy.context.scene.collection.objects.link(root)
        for obj in imported:
            if obj.parent is None:
                obj.parent = root
            if obj.type == "MESH":
                for mat in obj.data.materials:
                    repair_material(mat)
                lower_facial_uv(obj)
        low, high = imported_bounds(imported)
        height = high.z - low.z
        factor = 1.58 / height
        root.scale = (factor, factor, factor)
        root.location = (x - (low.x + high.x) * factor / 2, -(low.y + high.y) * factor / 2, -low.z * factor)
        label(title, x, ink)
    camera_data = bpy.data.cameras.new("CAM_group")
    camera_data.type, camera_data.ortho_scale = "ORTHO", 7.0
    camera = bpy.data.objects.new("CAM_group", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (0, -16, 2.1)
    camera.rotation_euler = (Vector((0, 0, 0.85)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    add_lights()
    OUT_RENDER.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(safety.guard(OUT_RENDER))
    bpy.ops.wm.save_as_mainfile(filepath=str(safety.guard(OUT_BLEND)), compress=True)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build()
